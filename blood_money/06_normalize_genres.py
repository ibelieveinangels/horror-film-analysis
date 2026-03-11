# blood_money/06_normalize_genres.py
# Explodes pipe-delimited genre_ids from horror_films_clean into a 
# normalized film_genres table for clean subgenre grouping in SQL.

import sqlite3
import pandas as pd
from config import DB_PATH

GENRE_NAMES = {
    '28': 'Action', '12': 'Adventure', '16': 'Animation',
    '35': 'Comedy', '80': 'Crime', '99': 'Documentary',
    '18': 'Drama', '10751': 'Family', '14': 'Fantasy',
    '36': 'History', '27': 'Horror', '10402': 'Music',
    '9648': 'Mystery', '10749': 'Romance', '878': 'Science Fiction',
    '53': 'Thriller', '10752': 'War', '37': 'Western',
    '10770': 'TV Movie'
}

conn = sqlite3.connect(DB_PATH)
df = pd.read_sql("SELECT id, genre_ids FROM horror_films_clean", conn)

rows = []
for _, row in df.iterrows():
    if pd.isna(row['genre_ids']):
        continue
    for gid in str(row['genre_ids']).split('|'):
        gid = gid.strip()
        if gid in GENRE_NAMES and gid != '10770':  # exclude TV Movie
            rows.append({
                'film_id': row['id'],
                'genre_id': int(gid),
                'genre_name': GENRE_NAMES[gid]
            })

genre_df = pd.DataFrame(rows)
genre_df.to_sql('film_genres', conn, if_exists='replace', index=False)
conn.close()
print(f"film_genres table created: {len(genre_df):,} rows")