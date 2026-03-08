"""
Collect ALL horror films from TMDB API and save to CSV.

Uses year-by-year discovery to bypass TMDB's 500-page (10,000 result) cap.
For each year, paginates /discover/movie filtered to genre 27 (horror).
Then fetches /movie/{id} details for every film.

Supports resuming: films already in the output CSV are skipped.
"""

import os
import time
import csv
from datetime import datetime
from dotenv import load_dotenv
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# --- Configuration ---
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "tmdbapi.env"))
API_KEY = os.getenv("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "horror_films_raw.csv")

REQUEST_TIMEOUT = 30  # seconds
CURRENT_YEAR = datetime.now().year

DISCOVER_FIELDS = [
    "id", "title", "release_date", "popularity",
    "vote_average", "vote_count", "original_language",
    "overview", "genre_ids",
]

DETAIL_FIELDS = [
    "budget", "revenue", "runtime",
    "production_companies", "production_countries",
    "spoken_languages", "status",
]

ALL_FIELDS = DISCOVER_FIELDS + DETAIL_FIELDS


def create_session():
    """Create a requests session with automatic retries."""
    session = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def discover_year(session, year):
    """Discover all horror films for a single year."""
    films = []
    params = {
        "api_key": API_KEY,
        "with_genres": 27,
        "sort_by": "primary_release_date.asc",
        "primary_release_date.gte": f"{year}-01-01",
        "primary_release_date.lte": f"{year}-12-31",
        "page": 1,
    }

    resp = session.get(f"{BASE_URL}/discover/movie", params=params, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    total_pages = min(data["total_pages"], 500)
    total_results = data["total_results"]
    films.extend(data["results"])

    for page in range(2, total_pages + 1):
        params["page"] = page
        resp = session.get(f"{BASE_URL}/discover/movie", params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        films.extend(resp.json()["results"])
        time.sleep(0.05)

    return films, total_results


def discover_all_horror_films(session):
    """Discover horror films year-by-year from 1880 to present, plus undated."""
    all_films = {}  # keyed by id to deduplicate
    total_api_results = 0

    # Year-by-year from 1880 through next year
    print("  Discovering by year...")
    for year in range(1880, CURRENT_YEAR + 2):
        films, count = discover_year(session, year)
        if films:
            for f in films:
                all_films[f["id"]] = f
            print(f"    {year}: {len(films)} films (API says {count})")
        time.sleep(0.05)

    # Also grab films with no release date (empty date range)
    print("  Discovering films with no release date...")
    params = {
        "api_key": API_KEY,
        "with_genres": 27,
        "sort_by": "popularity.desc",
        "page": 1,
    }
    # Films without dates: use a date range that's empty-ish
    # Actually we just do a broad search and dedupe
    for page in range(1, 501):
        params["page"] = page
        resp = session.get(f"{BASE_URL}/discover/movie", params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        if not data["results"]:
            break
        new_count = 0
        for f in data["results"]:
            if f["id"] not in all_films:
                all_films[f["id"]] = f
                new_count += 1
        # If no new films found for several pages, stop
        if page > 10 and new_count == 0:
            break
        if page % 50 == 0:
            print(f"    Broad sweep page {page}, unique films: {len(all_films)}")
        time.sleep(0.05)

    print(f"\n  Discovery complete: {len(all_films)} unique horror films found\n")
    return list(all_films.values())


def fetch_film_details(session, film_id):
    """Get detailed info for a single film from /movie/{id}."""
    params = {"api_key": API_KEY}
    resp = session.get(f"{BASE_URL}/movie/{film_id}", params=params, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def flatten_detail(detail):
    """Extract and flatten the detail fields we care about."""
    companies = detail.get("production_companies", [])
    countries = detail.get("production_countries", [])
    languages = detail.get("spoken_languages", [])

    return {
        "budget": detail.get("budget", 0),
        "revenue": detail.get("revenue", 0),
        "runtime": detail.get("runtime"),
        "production_companies": "|".join(c["name"] for c in companies) if companies else "",
        "production_countries": "|".join(c["iso_3166_1"] for c in countries) if countries else "",
        "spoken_languages": "|".join(lang["iso_639_1"] for lang in languages if lang.get("iso_639_1")) if languages else "",
        "status": detail.get("status", ""),
    }


def load_existing_ids():
    """Load IDs already in the CSV so we can resume."""
    existing = set()
    if os.path.exists(OUTPUT_PATH):
        with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing.add(int(row["id"]))
    return existing


def main():
    if not API_KEY:
        print("ERROR: TMDB_API_KEY not found. Check your tmdbapi.env file.")
        return

    session = create_session()

    print("=" * 60)
    print("TMDB Horror Film Collection (FULL)")
    print("=" * 60)

    # Step 1 -- Discover all horror films year-by-year
    print("\n[Step 1] Discovering ALL horror films (year-by-year)...")
    films = discover_all_horror_films(session)

    # Step 2 --Check for existing data to resume
    existing_ids = load_existing_ids()
    to_fetch = [f for f in films if f["id"] not in existing_ids]
    print(f"[Step 2] Fetching details: {len(to_fetch)} new films "
          f"({len(existing_ids)} already in CSV, skipping)\n")

    if not to_fetch:
        print("Nothing new to fetch!")
    else:
        os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

        # If resuming, append; otherwise write fresh with header
        file_is_new = len(existing_ids) == 0
        csvfile = open(OUTPUT_PATH, "a" if not file_is_new else "w", newline="", encoding="utf-8")
        writer = csv.DictWriter(csvfile, fieldnames=ALL_FIELDS)
        if file_is_new:
            writer.writeheader()

        total = len(to_fetch)
        for i, film in enumerate(to_fetch, 1):
            film_id = film["id"]

            # Build row from discovery data
            row = {}
            for field in DISCOVER_FIELDS:
                val = film.get(field)
                if field == "genre_ids" and isinstance(val, list):
                    val = "|".join(str(g) for g in val)
                row[field] = val

            # Fetch and merge detail data
            try:
                detail = fetch_film_details(session, film_id)
                row.update(flatten_detail(detail))
            except requests.exceptions.RequestException as e:
                print(f"  Warning: Could not fetch details for "
                      f"'{film.get('title')}' (id={film_id}): {e}")
                for field in DETAIL_FIELDS:
                    row[field] = ""

            writer.writerow(row)

            if i % 100 == 0:
                print(f"  Progress: {i}/{total} new films processed "
                      f"({i + len(existing_ids)} total)")
                csvfile.flush()

            time.sleep(0.25)

        csvfile.close()

    # Step 3 -- Summary
    all_rows = []
    with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
        all_rows = list(csv.DictReader(f))

    dates = [r["release_date"] for r in all_rows if r.get("release_date")]
    min_date = min(dates) if dates else "N/A"
    max_date = max(dates) if dates else "N/A"

    has_budget = sum(1 for r in all_rows if r.get("budget") and str(r["budget"]) not in ("", "0"))
    has_revenue = sum(1 for r in all_rows if r.get("revenue") and str(r["revenue"]) not in ("", "0"))

    print("\n" + "=" * 60)
    print("COLLECTION COMPLETE")
    print("=" * 60)
    print(f"  Total films collected : {len(all_rows)}")
    print(f"  Date range            : {min_date}  to  {max_date}")
    print(f"  Films with budget > 0 : {has_budget}")
    print(f"  Films with revenue > 0: {has_revenue}")
    print(f"  Output file           : {OUTPUT_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    main()
