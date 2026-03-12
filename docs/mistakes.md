## Mistakes

Premature analysis

No structure

No framework

Naming conventions and organization
    i know the tmdb data is the tmdb data because its the only one without a specified source name

Scripting took multiple attempts due to normalization errors

Saved states with duplicate db names caused issues with 06.py

.md formatting (headers), formatting for github

NULL voids within datasets?
    Not sure if this is an issue, but the IMDB and Rotten Tomatoes tables have NULL voids that were created when schema compatibility was being addressed

Irrelevant columns are present in some CLEANED datasets (rt_movies_clean.sound_mix)
    not removing but probably takes space or something

Scripting 
    did not take into account hardcoded paths

    Silently dropped computed column (normalized_score)
    normalized_score was computed correctly in process_rt_reviews() but
    never made it to the CSV — null_pad_to_schema() enforced TARGET_REVIEWS_COLS
    which didn't include it, silently stripping the column before export.
    always verify TARGET_*_COLS when adding new computed columns to a pipeline.

Poisonous values (i.e. 'TV Movie' in genre_name)
    had to remove

SQL db
    is_top_critic stored as TEXT ("True"/"False") instead of boolean
        astype(bool) in 05_process_rt_data.py converts the column correctly
        in pandas but SQLite has no boolean type — it stores it as TEXT.
        CASE WHEN is_top_critic = 1 fails silently, returning NULL averages
        with no error message. always verify column types with PRAGMA table_info()
        before writing conditional aggregations.
    normalized_score stored as TEXT instead of REAL
        AVG() on a TEXT column returns NULL in SQLite without raising an error.
        requires explicit CAST(normalized_score AS REAL) in every aggregation.
        root cause: pandas writes float columns as TEXT when the column contains
        NaN mixed with numeric values and SQLite infers the type as TEXT on import.
        fix at source: cast to REAL on import or use explicit column type definitions.
    film_genres.film_id references horror_films_clean.id, not rt_movies_clean.rt_id
        rt_movies_clean has no shared key with film_genres — joining them directly
        fails. requires routing through horror_combined which bridges both sources
        on title + release_year. always trace the full join path before writing
        multi-table queries across sources with diverging schemas.