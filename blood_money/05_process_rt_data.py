# blood_money/05_process_rt_data.py
# Horror Film Analytics Platform — Rotten Tomatoes Data Processing
#
# Ingests:  data/raw/rotten_tomatoes_movies.csv
#           data/raw/rotten_tomatoes_movie_reviews.csv
# Outputs:  data/processed/rt_movies_clean.csv
#           data/processed/rt_reviews_clean.csv
#           data/processed/rt_data_quality_report.csv
#           data/processed/rt_error_log.csv

import re
import os
import numpy as np
import pandas as pd
from datetime import datetime
from tqdm import tqdm
from loguru import logger

from config import (
    PROCESSED_DATA_DIR,
    RAW_DATA_DIR,
    CHUNK_SIZE,
    LARGE_FILE_MB,
    FUZZY_THRESHOLD,
)

# ── Paths ──
RT_MOVIES_PATH       = RAW_DATA_DIR  / "rotten_tomatoes_movies.csv"
RT_REVIEWS_PATH      = RAW_DATA_DIR  / "rotten_tomatoes_movie_reviews.csv"
RT_MOVIES_CLEAN      = PROCESSED_DATA_DIR / "rt_movies_clean.csv"
RT_REVIEWS_CLEAN     = PROCESSED_DATA_DIR / "rt_reviews_clean.csv"
RT_QUALITY_REPORT    = PROCESSED_DATA_DIR / "rt_data_quality_report.csv"
RT_ERROR_LOG         = PROCESSED_DATA_DIR / "rt_error_log.csv"
RT_INTEGRATION_LOG   = PROCESSED_DATA_DIR / "rt_integration.log"

PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
logger.add(RT_INTEGRATION_LOG, mode="w", level="INFO")

# ── Genre mapping reused from 04 ──
GENRE_MAPPING: dict[str, dict] = {
    "Action":      {"id": 28,    "name": "Action"},
    "Adventure":   {"id": 12,    "name": "Adventure"},
    "Animation":   {"id": 16,    "name": "Animation"},
    "Comedy":      {"id": 35,    "name": "Comedy"},
    "Crime":       {"id": 80,    "name": "Crime"},
    "Documentary": {"id": 99,    "name": "Documentary"},
    "Drama":       {"id": 18,    "name": "Drama"},
    "Family":      {"id": 10751, "name": "Family"},
    "Fantasy":     {"id": 14,    "name": "Fantasy"},
    "History":     {"id": 36,    "name": "History"},
    "Horror":      {"id": 27,    "name": "Horror"},   # TARGET GENRE
    "Music":       {"id": 10402, "name": "Music"},
    "Mystery":     {"id": 9648,  "name": "Mystery"},
    "Romance":     {"id": 10749, "name": "Romance"},
    "Sci-Fi":      {"id": 878,   "name": "Science Fiction"},
    "Thriller":    {"id": 53,    "name": "Thriller"},
    "War":         {"id": 10752, "name": "War"},
    "Western":     {"id": 37,    "name": "Western"},
}

# Target schema for movies output — aligns with horror_films_clean
TARGET_MOVIES_COLS = [
    "rt_id", "title", "release_date", "release_date_year",
    "runtime", "rating", "rating_contents",
    "original_language", "genre_ids",
    "audience_score", "tomatometer",
    "director", "writer", "distributor",
    "revenue", "sound_mix",
]

# Target schema for reviews output
TARGET_REVIEWS_COLS = [
    "rt_id", "review_id", "creation_date",
    "critic_name", "is_top_critic",
    "original_score", "review_state",
    "publication_name", "review_text",
    "score_sentiment", "review_url",
]


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def clean_title(title) -> str:
    """
    Identical normalisation to 04_merge_imdb_data.py — keeps join logic
    consistent across all three data sources.
    Strips leading article only, not mid-title occurrences.
    """
    if pd.isna(title):
        return ""
    title = str(title).lower().strip()
    title = re.sub(r"[^a-z0-9\s-]", "", title)
    words = title.split()
    if len(words) > 1 and words[0] in ("the", "a"):
        words = words[1:]
    return " ".join(words)


def slug_to_title(slug: str) -> str:
    """
    Convert RT's id slug to a readable string for fallback matching.
    e.g. 'space-zombie-bingo' → 'space zombie bingo'
    This is a secondary join key — cleaner than fuzzy matching on the
    full title string when the canonical title is messy.
    """
    if pd.isna(slug):
        return ""
    return str(slug).replace("-", " ").replace("_", " ").strip()


def clean_box_office(value) -> float:
    """
    RT boxOffice is a dirty string: '$12,345,678' or NaN.
    Strip currency symbols and commas, return float or NaN.
    """
    if pd.isna(value):
        return np.nan
    cleaned = re.sub(r"[^\d.]", "", str(value))
    try:
        return float(cleaned)
    except ValueError:
        return np.nan
    
def normalize_score(score) -> float:
    """
    Normalize heterogeneous RT critic score strings to 0-100 float.
    Handles formats: 'A+', 'B-', '3.5/5', '7/10', '85', '4/4' etc.
    Returns NaN if unparseable.
    """
    if pd.isna(score):
        return np.nan
    score = str(score).strip()

    # Letter grades
    grade_map = {
        'A+': 100, 'A': 95, 'A-': 92,
        'B+': 88, 'B': 85, 'B-': 82,
        'C+': 78, 'C': 75, 'C-': 72,
        'D+': 68, 'D': 65, 'D-': 62,
        'F': 30
    }
    if score in grade_map:
        return float(grade_map[score])

    # Fraction formats: '3.5/5', '7/10', '4/4'
    if '/' in score:
        try:
            num, denom = score.split('/')
            return round(float(num.strip()) / float(denom.strip()) * 100, 1)
        except:
            return np.nan

    # Plain numeric: '85', '7.5'
    try:
        val = float(re.sub(r'[^\d.]', '', score))
        # If already on 0-100 scale
        if val <= 100:
            return val
        return np.nan
    except:
        return np.nan

def transform_genres(genre_string: str) -> tuple[list[dict], bool]:
    """
    RT genre strings are comma-separated like IMDb.
    Same logic as 04 — .title() normalisation before lookup.
    RT uses 'Horror' directly so this maps cleanly.
    Returns (genre_list, has_horror).
    """
    if pd.isna(genre_string) or str(genre_string).strip() == "":
        return [], False

    raw_genres = [g.strip().strip('"').title() for g in str(genre_string).split(",")]
    tmdb_ids: list[dict] = []
    has_horror = False

    for genre_name in raw_genres:
        if genre_name in GENRE_MAPPING:
            entry = GENRE_MAPPING[genre_name]
            tmdb_ids.append({"id": entry["id"], "name": entry["name"]})
            if entry["id"] == 27:
                has_horror = True
        else:
            logger.debug(f"Unmapped RT genre token: '{genre_name}'")

    return tmdb_ids, has_horror


def extract_year(date_string) -> int:
    """
    Parse release year from RT's date strings (mixed formats: 'Jan 1, 2020',
    'Oct 31, 1990', etc.). Returns 0 if unparseable.
    """
    if pd.isna(date_string):
        return 0
    try:
        return pd.to_datetime(str(date_string), errors="coerce").year or 0
    except Exception:
        return 0

def null_pad_to_schema(df: pd.DataFrame, target_cols: list[str]) -> pd.DataFrame:
    """Add any missing target columns as NaN so schema is always complete."""
    for col in target_cols:
        if col not in df.columns:
            df[col] = np.nan
    return df[target_cols]


# ─────────────────────────────────────────────
# MOVIES PROCESSING
# ─────────────────────────────────────────────

def process_rt_movies() -> tuple[pd.DataFrame, pd.DataFrame, set]:
    """
    Load, filter, and transform rotten_tomatoes_movies.csv.

    Two-pass design: this function produces the horror id allowlist
    that process_rt_reviews() uses to avoid loading 391MB into memory.

    Returns:
        horror_df    : cleaned horror movies
        dropped_df   : non-horror records for quality report
        horror_ids   : set of rt_id slugs for the reviews allowlist
    """
    size_mb = os.path.getsize(RT_MOVIES_PATH) / (1024 * 1024)
    use_chunks = size_mb > LARGE_FILE_MB
    logger.info(f"Loading RT movies ({size_mb:.1f} MB) | chunked={use_chunks}")

    encodings = ["utf-8", "latin-1", "cp1252"]
    df = None

    for encoding in encodings:
        try:
            if use_chunks:
                chunks = []
                reader = pd.read_csv(
                    RT_MOVIES_PATH, encoding=encoding,
                    chunksize=CHUNK_SIZE, low_memory=False,
                )
                for chunk in tqdm(reader, desc="  Reading rt_movies", unit="chunk"):
                    chunks.append(chunk)
                df = pd.concat(chunks, ignore_index=True)
            else:
                df = pd.read_csv(RT_MOVIES_PATH, encoding=encoding, low_memory=False)
            logger.info(f"  Loaded {len(df):,} rows with '{encoding}' encoding")
            break
        except UnicodeDecodeError:
            logger.warning(f"  Encoding '{encoding}' failed, trying next...")

    if df is None:
        raise ValueError("Could not load rotten_tomatoes_movies.csv with any encoding.")

    # ── Title normalisation first ──
    logger.info("Normalising RT movie titles...")
    tqdm.pandas(desc="  clean_title")
    df["cleaned_title"] = df["title"].progress_apply(clean_title)

    # ── Slug-derived title as secondary join key ──
    df["slug_title"] = df["id"].apply(slug_to_title)

    # ── Genre transform + Horror filter ──
    logger.info("Transforming RT genres...")
    tqdm.pandas(desc="  transform_genres")
    genre_results    = df["genre"].progress_apply(transform_genres)
    df["genre_ids"]  = [r[0] for r in genre_results]
    df["has_horror"] = [r[1] for r in genre_results]

    horror_df  = df[df["has_horror"]].copy()
    dropped_df = df[~df["has_horror"]].copy()
    logger.info(
        f"RT horror kept: {len(horror_df):,} | Non-horror dropped: {len(dropped_df):,}"
    )

    # ── Build horror id allowlist for reviews pass ──
    horror_ids = set(horror_df["id"].dropna().unique())
    logger.info(f"Horror RT id allowlist: {len(horror_ids):,} slugs")

    # ── Schema rename ──
    horror_df.rename(columns={
        "id":             "rt_id",
        "audienceScore":  "audience_score",
        "tomatoMeter":    "tomatometer",
        "ratingContents": "rating_contents",
        "releaseDateTheaters": "release_date",
        "runtimeMinutes": "runtime",
        "originalLanguage": "original_language",
        "boxOffice":      "revenue",
        "soundMix":       "sound_mix",
    }, inplace=True)

    # ── Type coercion ──
    horror_df["release_date_year"] = horror_df["release_date"].apply(extract_year)
    horror_df["revenue"]           = horror_df["revenue"].apply(clean_box_office)
    horror_df["runtime"]           = pd.to_numeric(horror_df["runtime"], errors="coerce")
    horror_df["audience_score"]    = pd.to_numeric(horror_df["audience_score"], errors="coerce")
    horror_df["tomatometer"]       = pd.to_numeric(horror_df["tomatometer"], errors="coerce")
    horror_df["genre_ids"]         = horror_df["genre_ids"].apply(str)

    horror_df = horror_df.drop_duplicates(subset=["title", "release_date_year"])
    
    horror_df = null_pad_to_schema(horror_df, TARGET_MOVIES_COLS)
    return horror_df, dropped_df, horror_ids


# ─────────────────────────────────────────────
# REVIEWS PROCESSING  (two-pass, allowlist-filtered)
# ─────────────────────────────────────────────

def process_rt_reviews(horror_ids: set) -> pd.DataFrame:
    """
    Load rotten_tomatoes_movie_reviews.csv in chunks, keeping only reviews
    whose id is in the horror_ids allowlist produced by process_rt_movies().

    This avoids loading the full 391MB dataset into memory — each chunk is
    filtered immediately and discarded, so peak memory usage is one chunk
    (~10k rows) plus the accumulated horror reviews.

    Also fixes the 'publicatioName' typo present in the raw dataset.
    """
    size_mb = os.path.getsize(RT_REVIEWS_PATH) / (1024 * 1024)
    logger.info(f"Loading RT reviews ({size_mb:.1f} MB) in chunks — filtering to horror allowlist...")

    encodings = ["utf-8", "latin-1", "cp1252"]
    horror_chunks = []
    total_rows = 0
    kept_rows  = 0

    for encoding in encodings:
        try:
            reader = pd.read_csv(
                RT_REVIEWS_PATH, encoding=encoding,
                chunksize=CHUNK_SIZE, low_memory=False,
            )
            for chunk in tqdm(reader, desc="  Reading rt_reviews", unit="chunk"):
                total_rows += len(chunk)
                filtered = chunk[chunk["id"].isin(horror_ids)].copy()
                if not filtered.empty:
                    horror_chunks.append(filtered)
                    kept_rows += len(filtered)

            logger.info(
                f"  Reviews processed: {total_rows:,} total | "
                f"{kept_rows:,} horror ({kept_rows/total_rows*100:.1f}%)"
            )
            break

        except UnicodeDecodeError:
            logger.warning(f"  Encoding '{encoding}' failed, trying next...")
            horror_chunks = []
            total_rows = 0
            kept_rows  = 0

    if not horror_chunks:
        logger.warning("No horror reviews found — returning empty DataFrame.")
        return pd.DataFrame(columns=TARGET_REVIEWS_COLS)

    df = pd.concat(horror_chunks, ignore_index=True)

    # ── Fix typo in raw dataset: 'publicatioName' → 'publication_name' ──
    df.rename(columns={
        "id":             "rt_id",
        "reviewId":       "review_id",
        "creationDate":   "creation_date",
        "criticName":     "critic_name",
        "isTopCritic":    "is_top_critic",
        "originalScore":  "original_score",
        "reviewState":    "review_state",
        "publicatioName": "publication_name",   # ← typo in source data
        "reviewText":     "review_text",
        "scoreSentiment": "score_sentiment",
        "reviewUrl":      "review_url",
    }, inplace=True)

    # ── Type coercion ──
    df["is_top_critic"] = df["is_top_critic"].astype(bool)
    df["creation_date"] = pd.to_datetime(df["creation_date"], errors="coerce")

    df["normalized_score"] = df["original_score"].apply(normalize_score)

    df = null_pad_to_schema(df, TARGET_REVIEWS_COLS)
    logger.info(f"RT reviews clean: {len(df):,} rows")
    return df


# ─────────────────────────────────────────────
# REPORT WRITERS
# ─────────────────────────────────────────────

def write_quality_report(dropped_df: pd.DataFrame) -> None:
    """Log all non-horror RT movies dropped during genre filtering."""
    report = dropped_df[["id", "title"]].rename(
        columns={"id": "rt_id", "title": "original_title"}
    ).copy()
    report["error_type"] = "Genre Filter"
    report["details"]    = "Missing Horror Genre"
    report.to_csv(RT_QUALITY_REPORT, index=False)
    logger.info(f"RT quality report: {len(report):,} records → {RT_QUALITY_REPORT}")


def write_error_log(movies_df: pd.DataFrame) -> None:
    """
    Log horror movies with no release date or unparseable year —
    these will cause join failures downstream against the primary schema.
    """
    problem_rows = movies_df[
        (movies_df["release_date_year"] == 0) |
        movies_df["release_date_year"].isna()
    ][["rt_id", "title"]].copy()

    if problem_rows.empty:
        pd.DataFrame(columns=["rt_id", "title", "error_type", "details"]
                     ).to_csv(RT_ERROR_LOG, index=False)
        return

    problem_rows["error_type"] = "Missing Release Year"
    problem_rows["details"]    = "release_date unparseable or null — join on title+year will fail"
    problem_rows.to_csv(RT_ERROR_LOG, index=False)
    logger.info(f"RT error log: {len(problem_rows):,} records → {RT_ERROR_LOG}")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main() -> None:
    start = datetime.now()
    logger.info("=" * 60)
    logger.info("Horror Film Analytics Platform — RT Data Processing Pipeline")
    logger.info(f"Start: {start.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    # ── Pass 1: movies → produces horror_ids allowlist ──
    movies_df, dropped_df, horror_ids = process_rt_movies()

    # ── Pass 2: reviews → filtered to horror_ids only ──
    reviews_df = process_rt_reviews(horror_ids)

    # ── Write outputs ──
    movies_df.to_csv(RT_MOVIES_CLEAN,  index=False)
    reviews_df.to_csv(RT_REVIEWS_CLEAN, index=False)
    logger.info(f"RT movies  → {RT_MOVIES_CLEAN} ({len(movies_df):,} rows)")
    logger.info(f"RT reviews → {RT_REVIEWS_CLEAN} ({len(reviews_df):,} rows)")

    write_quality_report(dropped_df)
    write_error_log(movies_df)

    elapsed = (datetime.now() - start).total_seconds()
    logger.info("=" * 60)
    logger.info(f"Pipeline complete in {elapsed:.1f}s")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
