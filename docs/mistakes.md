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

Scripting does not take into account hardcoded paths

Poisonous values (i.e. 'TV Movie' in genre_name)
    had to remove