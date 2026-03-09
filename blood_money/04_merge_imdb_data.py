# blood_money/04_merge_imdb_data.py
# Horror Film Analytics Platform — IMDb Data Integration
#
# Ingests:  data/raw/title_basics.csv
#           data/raw/title_ratings.csv
# Outputs:  data/processed/imdb_title_basics_clean.csv
#           data/processed/imdb_title_ratings_clean.csv
#           data/processed/data_quality_report.csv
#           data/processed/error_log.csv
#           data/processed/fuzzy_review.csv
#           data/processed/data_integration.log

import re
import os
import numpy as np
import pandas as pd
from datetime import datetime
from rapidfuzz import fuzz
from tqdm import tqdm
from loguru import logger

# ── Import all paths and tuning constants from central config ──
from config import (
    PROCESSED_DATA_DIR,
    IMDB_BASICS_PATH,
    IMDB_RATINGS_PATH,
    BASICS_CLEAN_PATH,
    RATINGS_CLEAN_PATH,
    QUALITY_REPORT_PATH,
    ERROR_LOG_PATH,
    FUZZY_REVIEW_PATH,
    INTEGRATION_LOG_PATH,
    FUZZY_THRESHOLD,
    CHUNK_SIZE,
    LARGE_FILE_MB,
)

# ── Ensure output directory exists ──
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

# ── File sink so logs also write to disk alongside the tqdm-safe console sink
#    already configured in config.py ──
logger.add(INTEGRATION_LOG_PATH, mode="w", level="INFO")

# ─────────────────────────────────────────────
# GENRE MAPPING  (IMDb text → TMDB id + name)
# Keys are Title Case to match after .title() normalisation.
# ─────────────────────────────────────────────
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

# Columns the output must expose to align with horror_films_clean schema.
# Columns absent from IMDb source are null-padded so the schema is always complete.
TARGET_BASICS_COLS = [
    "imdb_id", "title", "release_date_year",
    "genre_ids", "runtime", "overview",
    "original_language", "popularity",
    "production_companies", "production_countries",
    "spoken_languages", "status", "budget", "revenue",
]
TARGET_RATINGS_COLS = [
    "imdb_id", "title", "release_date_year",
    "vote_average", "vote_count",
]


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def clean_title(title) -> str:
    """
    Normalise a raw title string:
      1. Lowercase + strip whitespace
      2. Remove special characters except hyphens (kept for compound titles)
      3. Strip a single LEADING article ('the' / 'a') only.

    NOTE: The leading-article strip checks only words[0].  Filtering the whole
    word list (as in the original prompt code) corrupts mid-title occurrences,
    e.g. "Attack the Block" would become "Attack Block".
    """
    if pd.isna(title):
        return ""
    title = str(title).lower().strip()
    title = re.sub(r"[^a-z0-9\s-]", "", title)
    words = title.split()
    if len(words) > 1 and words[0] in ("the", "a"):
        words = words[1:]
    return " ".join(words)


def transform_genres(genre_string: str) -> tuple[list[dict], bool]:
    """
    Convert a comma-separated IMDb genre string into TMDB-style dicts and flag
    whether Horror (id=27) is present.

    NOTE: Tokens are normalised with .title() so they match the Title Case dict
    keys.  Using .upper() (original prompt code) caused 'HORROR' != 'Horror',
    making every record fail the Horror check and be discarded.

    Returns:
        (genre_list, has_horror)
    """
    if pd.isna(genre_string) or str(genre_string).strip() in ("", "\\N"):
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
            logger.debug(f"Unmapped genre token: '{genre_name}'")

    return tmdb_ids, has_horror


def load_csv(file_path) -> pd.DataFrame:
    """
    Load a CSV/TSV with automatic encoding fallback (utf-8 → latin-1 → cp1252).
    Uses chunked reading for files larger than LARGE_FILE_MB.
    Treats IMDb's sentinel value '\\N' as NaN automatically.
    """
    file_path = str(file_path)
    sep = "\t" if file_path.endswith((".tsv", ".tsv.gz")) else ","
    encodings = ["utf-8", "latin-1", "cp1252"]
    size_mb = os.path.getsize(file_path) / (1024 * 1024)
    use_chunks = size_mb > LARGE_FILE_MB

    logger.info(f"Loading {file_path} ({size_mb:.1f} MB) | chunked={use_chunks}")

    for encoding in encodings:
        try:
            if use_chunks:
                chunks = []
                reader = pd.read_csv(
                    file_path, sep=sep, encoding=encoding,
                    chunksize=CHUNK_SIZE, low_memory=False,
                    na_values=["\\N", "NA", ""],
                )
                for chunk in tqdm(reader,
                                  desc=f"  Reading {os.path.basename(file_path)}",
                                  unit="chunk"):
                    chunks.append(chunk)
                df = pd.concat(chunks, ignore_index=True)
            else:
                df = pd.read_csv(
                    file_path, sep=sep, encoding=encoding,
                    low_memory=False, na_values=["\\N", "NA", ""],
                )

            logger.info(f"  Loaded {len(df):,} rows with '{encoding}' encoding")
            return df

        except UnicodeDecodeError:
            logger.warning(f"  Encoding '{encoding}' failed, trying next...")
        except Exception as exc:
            logger.error(f"  Unexpected error loading {file_path}: {exc}")
            raise

    raise ValueError(f"Could not load {file_path} with any supported encoding.")


def validate_columns(df: pd.DataFrame, required: list[str], filename: str) -> bool:
    """Return False and log an error if any required column is absent."""
    missing = [c for c in required if c not in df.columns]
    if missing:
        logger.error(f"Missing columns in {filename}: {missing}")
        return False
    return True


def null_pad_to_schema(df: pd.DataFrame, target_cols: list[str]) -> pd.DataFrame:
    """Add any missing target columns as NaN so output schema is always complete."""
    for col in target_cols:
        if col not in df.columns:
            df[col] = np.nan
    return df[target_cols]


# ─────────────────────────────────────────────
# CORE PROCESSING
# ─────────────────────────────────────────────

def process_title_basics() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load, normalise, and filter title_basics.

    Returns:
        horror_df  : rows that contain Horror genre
        dropped_df : rows dropped (non-horror), used for quality report
    """
    df = load_csv(IMDB_BASICS_PATH)

    required = ["tconst", "primaryTitle", "startYear", "genres"]
    if not validate_columns(df, required, IMDB_BASICS_PATH.name):
        raise ValueError(f"{IMDB_BASICS_PATH.name} is missing required columns — see log.")

    # Title normalisation runs BEFORE genre transform (per spec)
    logger.info("Normalising titles...")
    tqdm.pandas(desc="  clean_title")
    df["cleaned_title"] = df["primaryTitle"].progress_apply(clean_title)

    # Genre transform
    logger.info("Transforming genres...")
    tqdm.pandas(desc="  transform_genres")
    genre_results    = df["genres"].progress_apply(transform_genres)
    df["genre_ids"]  = [r[0] for r in genre_results]
    df["has_horror"] = [r[1] for r in genre_results]

    # Split: keep horror, capture dropped for quality report
    horror_df  = df[df["has_horror"]].copy()
    dropped_df = df[~df["has_horror"]].copy()
    logger.info(
        f"Horror records kept: {len(horror_df):,} | Non-horror dropped: {len(dropped_df):,}"
    )

    # Rename to target schema
    horror_df.rename(columns={
        "tconst":         "imdb_id",
        "primaryTitle":   "title",
        "startYear":      "release_date_year",
        "runtimeMinutes": "runtime",
    }, inplace=True)

    # Type coercion
    horror_df["release_date_year"] = (
        pd.to_numeric(horror_df["release_date_year"], errors="coerce")
        .fillna(0).astype(int)
    )
    horror_df["runtime"] = pd.to_numeric(
        horror_df.get("runtime"), errors="coerce"
    )  # REAL in target schema — stays float/NaN

    # genre_ids serialised as string for CSV portability
    horror_df["genre_ids"] = horror_df["genre_ids"].apply(str)

    horror_df = null_pad_to_schema(horror_df, TARGET_BASICS_COLS)
    return horror_df, dropped_df


def process_title_ratings() -> pd.DataFrame:
    """Load and clean title_ratings."""
    df = load_csv(IMDB_RATINGS_PATH)

    required = ["tconst", "averageRating", "numVotes"]
    if not validate_columns(df, required, IMDB_RATINGS_PATH.name):
        raise ValueError(f"{IMDB_RATINGS_PATH.name} is missing required columns — see log.")

    df.rename(columns={
        "tconst":        "imdb_id",
        "averageRating": "vote_average",
        "numVotes":      "vote_count",
    }, inplace=True)

    df["vote_average"] = pd.to_numeric(df["vote_average"], errors="coerce")
    df["vote_count"]   = (
        pd.to_numeric(df["vote_count"], errors="coerce").fillna(0).astype(int)
    )
    return df


# ─────────────────────────────────────────────
# MERGE  (exact join → fuzzy title fallback)
# ─────────────────────────────────────────────

def merge_with_fuzzy_fallback(
    basics_df: pd.DataFrame,
    ratings_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Primary join: exact match on imdb_id.
    Fallback:     rapidfuzz.fuzz.token_sort_ratio on cleaned title strings.

    Fuzzy matching rationale
    ────────────────────────
    token_sort_ratio sorts both strings' tokens alphabetically before scoring.
    This makes it robust to minor word-order differences (e.g. "Saw, The" vs
    "The Saw") without requiring a deterministic canonical form.  Matches at or
    above FUZZY_THRESHOLD (default 80%) are accepted and merged.  Candidates
    below the threshold are written to fuzzy_review.csv for human inspection —
    they are never silently dropped.

    Returns:
        merged           : successfully joined rows
        unmatched_basics : horror basics with no rating match (exact or fuzzy)
        fuzzy_review_df  : sub-threshold fuzzy candidates
    """
    # Exact join
    merged = pd.merge(basics_df, ratings_df, on="imdb_id", how="inner")
    logger.info(f"Exact join matched: {len(merged):,} records")

    unmatched_basics_ids  = set(basics_df["imdb_id"])  - set(merged["imdb_id"])
    unmatched_ratings_ids = set(ratings_df["imdb_id"]) - set(merged["imdb_id"])

    unmatched_basics  = basics_df[basics_df["imdb_id"].isin(unmatched_basics_ids)].copy()
    unmatched_ratings = ratings_df[ratings_df["imdb_id"].isin(unmatched_ratings_ids)]

    logger.info(
        f"Unmatched after exact join → basics: {len(unmatched_basics):,} "
        f"| ratings: {len(unmatched_ratings):,}"
    )

    if unmatched_basics.empty or unmatched_ratings.empty:
        return merged, unmatched_basics, pd.DataFrame()

    # ratings_df doesn't carry a title column on its own — skip fuzzy if absent
    if "title" not in unmatched_ratings.columns:
        logger.info("Ratings table has no 'title' column — skipping fuzzy pass.")
        return merged, unmatched_basics, pd.DataFrame()

    # Fuzzy fallback
    logger.info(f"Running fuzzy title matching on {len(unmatched_basics):,} unmatched basics records...")
    rating_titles = unmatched_ratings["title"].fillna("").tolist()
    fuzzy_matched_rows: list[dict] = []
    fuzzy_review_rows:  list[dict] = []

    for _, row in tqdm(unmatched_basics.iterrows(),
                       total=len(unmatched_basics),
                       desc="  Fuzzy matching"):
        query = row.get("title", "")
        if not query or pd.isna(query):
            continue

        best_match, best_score = "", 0
        for rt in rating_titles:
            score = fuzz.token_sort_ratio(query, rt)
            if score > best_score:
                best_score, best_match = score, rt

        candidate = {
            "imdb_id":    row["imdb_id"],
            "title":      query,
            "best_match": best_match,
            "score":      best_score,
        }

        if best_score >= FUZZY_THRESHOLD:
            match_row = unmatched_ratings[
                unmatched_ratings["title"] == best_match
            ].iloc[0]
            fuzzy_matched_rows.append({
                **row.to_dict(),
                "vote_average": match_row["vote_average"],
                "vote_count":   match_row["vote_count"],
            })
        else:
            fuzzy_review_rows.append(candidate)

    if fuzzy_matched_rows:
        merged = pd.concat(
            [merged, pd.DataFrame(fuzzy_matched_rows)], ignore_index=True
        )
        logger.info(f"Fuzzy matches accepted (>={FUZZY_THRESHOLD}%): {len(fuzzy_matched_rows):,}")

    fuzzy_review_df = pd.DataFrame(fuzzy_review_rows) if fuzzy_review_rows else pd.DataFrame()
    logger.info(f"Fuzzy candidates below threshold: {len(fuzzy_review_df):,}")

    # Recompute unmatched after fuzzy pass
    final_matched_ids = set(merged["imdb_id"])
    unmatched_basics  = basics_df[~basics_df["imdb_id"].isin(final_matched_ids)].copy()

    return merged, unmatched_basics, fuzzy_review_df


# ─────────────────────────────────────────────
# REPORT WRITERS
# ─────────────────────────────────────────────

def write_quality_report(dropped_df: pd.DataFrame) -> None:
    """Log all non-horror records dropped during genre filtering."""
    report = dropped_df[["tconst", "primaryTitle"]].rename(
        columns={"tconst": "imdb_id", "primaryTitle": "original_title"}
    ).copy()
    report["error_type"] = "Genre Filter"
    report["details"]    = "Missing Horror Genre"
    report.to_csv(QUALITY_REPORT_PATH, index=False)
    logger.info(f"Quality report: {len(report):,} records → {QUALITY_REPORT_PATH}")


def write_error_log(unmatched_df: pd.DataFrame) -> None:
    """Log horror basics records that found no rating match (exact or fuzzy)."""
    if unmatched_df.empty:
        pd.DataFrame(columns=["imdb_id", "title", "error_type", "details"]
                     ).to_csv(ERROR_LOG_PATH, index=False)
        return
    log = unmatched_df[["imdb_id", "title"]].copy()
    log["error_type"] = "Unmatched Record"
    log["details"]    = "No rating entry found after exact + fuzzy join"
    log.to_csv(ERROR_LOG_PATH, index=False)
    logger.info(f"Error log: {len(log):,} unmatched records → {ERROR_LOG_PATH}")


def write_fuzzy_review(fuzzy_df: pd.DataFrame) -> None:
    """Write sub-threshold fuzzy candidates for human review."""
    if fuzzy_df.empty:
        pd.DataFrame(columns=["imdb_id", "title", "best_match", "score"]
                     ).to_csv(FUZZY_REVIEW_PATH, index=False)
        return
    fuzzy_df.to_csv(FUZZY_REVIEW_PATH, index=False)
    logger.info(f"Fuzzy review: {len(fuzzy_df):,} candidates → {FUZZY_REVIEW_PATH}")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main() -> None:
    start = datetime.now()
    logger.info("=" * 60)
    logger.info("Horror Film Analytics Platform — IMDb Integration Pipeline")
    logger.info(f"Start: {start.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    basics_df,  dropped_df            = process_title_basics()
    ratings_df                         = process_title_ratings()
    merged_df, unmatched, fuzzy_review = merge_with_fuzzy_fallback(basics_df, ratings_df)

    # Align to target schemas before writing
    basics_out   = null_pad_to_schema(merged_df.copy(), TARGET_BASICS_COLS)
    ratings_cols = [c for c in TARGET_RATINGS_COLS if c in merged_df.columns]
    ratings_out  = merged_df[ratings_cols].copy()

    basics_out.to_csv(BASICS_CLEAN_PATH,   index=False)
    ratings_out.to_csv(RATINGS_CLEAN_PATH, index=False)
    logger.info(f"Basics  → {BASICS_CLEAN_PATH} ({len(basics_out):,} rows)")
    logger.info(f"Ratings → {RATINGS_CLEAN_PATH} ({len(ratings_out):,} rows)")

    write_quality_report(dropped_df)
    write_error_log(unmatched)
    write_fuzzy_review(fuzzy_review)

    elapsed = (datetime.now() - start).total_seconds()
    logger.info("=" * 60)
    logger.info(f"Pipeline complete in {elapsed:.1f}s")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
