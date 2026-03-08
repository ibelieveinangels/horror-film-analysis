"""
Load horror_films_raw.csv into SQLite, create cleaned and financial tables.
"""

import os
import csv
import sqlite3

SCRIPT_DIR = os.path.dirname(__file__)
RAW_CSV = os.path.join(SCRIPT_DIR, "..", "data", "raw", "horror_films_raw.csv")
DB_PATH = os.path.join(SCRIPT_DIR, "..", "data", "horror_analysis.db")
CLEAN_CSV = os.path.join(SCRIPT_DIR, "..", "data", "cleaned", "horror_films_clean.csv")
FINANCIAL_CSV = os.path.join(SCRIPT_DIR, "..", "data", "cleaned", "horror_financial.csv")


def count(cur, table):
    return cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def main():
    os.makedirs(os.path.dirname(CLEAN_CSV), exist_ok=True)

    # --- Load CSV ---
    print("Loading CSV...")
    with open(RAW_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    print(f"  Rows in CSV: {len(rows)}")

    # --- Connect to SQLite ---
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # --- Create raw table ---
    cur.execute("""
        CREATE TABLE horror_films_raw (
            id              INTEGER PRIMARY KEY,
            title           TEXT,
            release_date    TEXT,
            popularity      REAL,
            vote_average    REAL,
            vote_count      INTEGER,
            original_language TEXT,
            overview        TEXT,
            genre_ids       TEXT,
            budget          INTEGER,
            revenue         INTEGER,
            runtime         REAL,
            production_companies  TEXT,
            production_countries  TEXT,
            spoken_languages      TEXT,
            status          TEXT
        )
    """)

    cur.executemany("""
        INSERT OR IGNORE INTO horror_films_raw
        (id, title, release_date, popularity, vote_average, vote_count,
         original_language, overview, genre_ids, budget, revenue, runtime,
         production_companies, production_countries, spoken_languages, status)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, [
        (
            int(r["id"]),
            r["title"] or None,
            r["release_date"] or None,
            float(r["popularity"]) if r["popularity"] else None,
            float(r["vote_average"]) if r["vote_average"] else None,
            int(r["vote_count"]) if r["vote_count"] else None,
            r["original_language"] or None,
            r["overview"] or None,
            r["genre_ids"] or None,
            int(r["budget"]) if r["budget"] else 0,
            int(r["revenue"]) if r["revenue"] else 0,
            float(r["runtime"]) if r["runtime"] else None,
            r["production_companies"] or None,
            r["production_countries"] or None,
            r["spoken_languages"] or None,
            r["status"] or None,
        )
        for r in rows
    ])
    conn.commit()

    raw_count = count(cur, "horror_films_raw")
    print(f"\n{'='*60}")
    print(f"horror_films_raw loaded: {raw_count} rows")
    print(f"{'='*60}")

    # --- Filter steps for horror_films_clean ---
    print("\n--- Filtering to horror_films_clean ---")

    # Step 1: status = 'Released'
    n_status = cur.execute(
        "SELECT COUNT(*) FROM horror_films_raw WHERE status = 'Released'"
    ).fetchone()[0]
    print(f"  status = 'Released'        : {n_status:>7,}  "
          f"(removed {raw_count - n_status:,} non-released)")

    # Step 2: + release_date not null/empty
    n_date = cur.execute("""
        SELECT COUNT(*) FROM horror_films_raw
        WHERE status = 'Released'
          AND release_date IS NOT NULL AND release_date != ''
    """).fetchone()[0]
    print(f"  + release_date not empty   : {n_date:>7,}  "
          f"(removed {n_status - n_date:,} with missing date)")

    # Step 3: + title not null
    n_title = cur.execute("""
        SELECT COUNT(*) FROM horror_films_raw
        WHERE status = 'Released'
          AND release_date IS NOT NULL AND release_date != ''
          AND title IS NOT NULL
    """).fetchone()[0]
    print(f"  + title not null           : {n_title:>7,}  "
          f"(removed {n_date - n_title:,} with no title)")

    # Step 4: + vote_count >= 10
    n_votes = cur.execute("""
        SELECT COUNT(*) FROM horror_films_raw
        WHERE status = 'Released'
          AND release_date IS NOT NULL AND release_date != ''
          AND title IS NOT NULL
          AND vote_count >= 10
    """).fetchone()[0]
    print(f"  + vote_count >= 10         : {n_votes:>7,}  "
          f"(removed {n_title - n_votes:,} with < 10 votes)")

    # Create the clean table
    cur.execute("DROP TABLE IF EXISTS horror_films_clean")
    cur.execute("""
        CREATE TABLE horror_films_clean AS
        SELECT *
        FROM horror_films_raw
        WHERE status = 'Released'
          AND release_date IS NOT NULL AND release_date != ''
          AND title IS NOT NULL
          AND vote_count >= 10
    """)
    conn.commit()

    clean_count = count(cur, "horror_films_clean")
    print(f"\n  horror_films_clean: {clean_count:,} rows "
          f"({raw_count - clean_count:,} removed from raw)")

    # --- Filter for horror_financial ---
    print("\n--- Filtering to horror_financial ---")

    n_budget = cur.execute(
        "SELECT COUNT(*) FROM horror_films_clean WHERE budget > 10000"
    ).fetchone()[0]
    print(f"  budget > 10,000            : {n_budget:>7,}  "
          f"(removed {clean_count - n_budget:,} with budget <= 10k)")

    n_both = cur.execute("""
        SELECT COUNT(*) FROM horror_films_clean
        WHERE budget > 10000 AND revenue > 10000
    """).fetchone()[0]
    print(f"  + revenue > 10,000         : {n_both:>7,}  "
          f"(removed {n_budget - n_both:,} with revenue <= 10k)")

    # Create the financial table with calculated columns
    cur.execute("DROP TABLE IF EXISTS horror_financial")
    cur.execute("""
        CREATE TABLE horror_financial AS
        SELECT *,
            ROUND((revenue - budget) * 100.0 / budget, 2) AS roi,
            CAST(SUBSTR(release_date, 1, 3) || '0s' AS TEXT) AS decade,
            CASE
                WHEN budget < 1000000  THEN 'micro'
                WHEN budget < 10000000 THEN 'low'
                WHEN budget < 50000000 THEN 'mid'
                ELSE 'wide'
            END AS budget_tier
        FROM horror_films_clean
        WHERE budget > 10000 AND revenue > 10000
    """)
    conn.commit()

    fin_count = count(cur, "horror_financial")
    print(f"\n  horror_financial: {fin_count:,} rows "
          f"({clean_count - fin_count:,} removed from clean)")

    # --- Export CSVs ---
    print(f"\n--- Exporting CSVs ---")

    for table, path in [("horror_films_clean", CLEAN_CSV),
                        ("horror_financial", FINANCIAL_CSV)]:
        cur.execute(f"SELECT * FROM {table}")
        cols = [desc[0] for desc in cur.description]
        rows_out = cur.fetchall()
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(cols)
            writer.writerows(rows_out)
        print(f"  {table} -> {path} ({len(rows_out):,} rows)")

    # --- Sample rows ---
    print(f"\n{'='*60}")
    print("Sample rows from horror_financial:")
    print(f"{'='*60}")
    cur.execute("""
        SELECT title, release_date, budget, revenue, roi, decade, budget_tier
        FROM horror_financial
        ORDER BY revenue DESC
        LIMIT 3
    """)
    sample_cols = [desc[0] for desc in cur.description]
    print(f"  {' | '.join(f'{c:>15}' for c in sample_cols)}")
    print(f"  {'-'*120}")
    for row in cur.fetchall():
        print(f"  {' | '.join(f'{str(v):>15}' for v in row)}")

    conn.close()
    print(f"\nDatabase saved to: {DB_PATH}")


if __name__ == "__main__":
    main()
