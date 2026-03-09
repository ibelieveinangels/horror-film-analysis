## Analysis Notes
*Last updated: March 2026*

# Assessment Brief
Horror is a highly profitable genre, particularly in the micro budget category, even when unicorns are removed.

# Glossary

1. Analysis Notes
2. TMDB
    horror_films_clean
        Data Dictionary
        Summary of Key Details
    horror_financial
        General
        Summary of Key Details
3. IMDb
    Data Quality Log
4. Rotten Tomatoes
    Data Quality Log
5. Insight Layer
    Closed Questions
    Open Questions

---

## horror_films_clean

# Data Dictionary — horror_films_clean

**Informal Column Rundown**

id - primary key, self explanatory

title - official release title of the films formatted in INITCAP

release_date - release year, month, and day formatted in ISO 8601 (XXXX-XX-XX)

popularity - upon first glance a float variable with no defined range, i.e. (Exit to Hell) 0.0136 - (Scream 7) 231.4379. Exit to Hell seems to be a relatively old movie, having been released in 2013 whilst Scream 7 should be considered “popular” under the context that it was only released 5 days ago as of March 4 2026. This trend follows the next two movies (Return to Silent Hill 2026-01-21 212.9702) and (28 Years Later: The Bone Temple 2026-01-14 98.1857) but discontinues with (Mouseboat Massacre 2025-05-09 80.3048) and follows with our first anomaly (The Faculty 1998-12-25 63.6252). I’m guessing “popularity” is a computed value but remains a mystery to me, we can assume that something must’ve come up that pushed up the relative popularity of The Faculty as an old movie. Cross-referencing on Google Trends is inconclusive.

vote_average - The float average with a max of 10 and a min of 1.2 as per the db. Within TMDB you may rate a movie from 1 - 10.

vote_count - The count of total vote submissions, becomes highly relevant since the highest rated movie with a “10” only have 18 vote submissions.

original_language - Two letter language code formatted in ISO 639-1 (en = english, ko = korean)

overview - A description of the films. The smallest overview is 21 characters whilst the largest is 999 characters. 999 Does not seem to be a hard cap as the overview does not cut out. ORDER BY reveals that some overviews are null which is something to take into consideration.

genre_ids - TMDB genre ids formatted as pipe-delimited strings (i.e. ”27” ”27|53|9648” “18|27”). They may appear to be in ascending order (i.e. 18 → 27), but (She-Wolf of London 9648|27|53)
reveals this is not necessarily true. All of them should contain 27 since that is the “horror” genre. There are movies with rich categorical mixes (i.e Tasmanian Devils 10770|14|27|878|12|28).

budget - integer budget data, ranging from 0 upward indefinitely (the MAX seems to be 200000000).

revenue - integer revenue data, ranging from 0 upward indefinitely (the MAX seems to be 719766009). This also reveals another anomaly in some movies where budgeted movies don’t have any revenue, but this can be explained easily (i.e. Day Shift (2022), the Jamie Foxx vampire movie, was a direct-to-streaming Netflix release rather than a traditional theatrical release, making it ineligible for a standard box office).

runtime - a float value of the minute runtime rounded to the nearest whole number. The MAX runtime is 608.0 whilst the MIN is 0.0, which is an anomaly (i.e. Fear Cabin: The Last Weekend of Summer 11 0.0). Notice that the missing data seems to be consistent with the vagueness / unpopularity of the movie overall so that’s something to keep in mind for future filtering / manipulation of the clean data.

production_companies - production company names formatted as pipe-delimited strings with some NULL values.

production_countries - production country names formatted as country codes (US= United States, RU = russia) with some NULL values.

spoken_languages - Two letter language code formatted in ISO 639-1 (en = english, ko = korean) with null values seemingly as “xx”.

status - The status of the film, which should be “released” by default as per the clean data


# Summary of Key Details — horror_films_clean

**Streaming anomaly:** 
Some films show budget but zero revenue due to direct-to-streaming releases (e.g. Day Shift, Netflix 2022). These are 
not theatrical failures — they require separate treatment in release pattern analysis.

---

## **General** - horror_financial

The following was queried for in SQLite:

- ROI by budget tier
- Best performing decades by average ROI
- Top 20 highest ROI horror films ever
- Does micro budget ROI hold across all decades or is it a modern phenomenon?
- What is the ROI distribution within micro budget — is the average skewed by outliers?

# **Summary of Key Details** — horror_financial

**Core finding:** 
Micro budget horror consistently outperforms all other 
budget tiers across every decade in the dataset.
This means there is no obvious advantage to investing higher than necessary in horror.

**Outlier adjustment:** 
Excluding films with ROI > 10,000%, micro budget average drops from 10,662% to 1,114% - still the highest performing tier. 
Two films (Paranormal Activity, Blair Witch Project) are responsible for the extreme headline figure. Our beautiful, scary unicorns.

**Risk profile:** 
42 of 206 micro budget films (20%) lost money. 
65 of 206 (31%) exceeded 1,000% ROI. High variance, high ceiling.
This means micro budget horror films are a low risk, high reward investment with highly variable return.

**Small sample caveat:** 
1990s micro showing 69,396% avg ROI is based on 
only 6 films — Blair Witch distorting a tiny sample. Decade-level analysis 
requires noting sample sizes alongside averages.

---

## IMDb — Data Quality Log
No data quality issues identified during processing. 
Pipeline ran cleanly via 04_merge_imdb_data.py; exact joins on tconst and title+year fuzzy fallback.

---

## Rotten Tomatoes — Data Quality Log

# Issue 1 — Duplicate Records in rt_movies_clean
**Problem identified:**
Running a duplicate check on rt_movies_clean revealed 300+ titles appearing
multiple times. Initially flagged by 28 Days Later returning NULL on the
combined join despite being present in the table.

**Analysis:**
1. True duplicates — same title, same valid year (e.g. 28 Days Later 2003 x2).
Caused by RT's concurrent scrape hitting the same page twice.
2. Year=0 groupings — different films sharing a generic title
(e.g. "Dracula", "Frankenstein", "Nightmare") with unparseable release dates,
falsely appearing as duplicates due to failed date parsing.

**Resolution:**
Added drop_duplicates(subset=["title", "release_date_year"]) to
process_rt_movies() in 05_process_rt_data.py before CSV export.
This collapses true scrape dupes while leaving year=0 records intact —
they remain in rt_movies_clean but never match on the title + year
join condition, so they don't pollute analysis.

## Issue 2 — Staggered International Releases Causing NULL Joins
**Problem identified:**
After deduplication, 28 Days Later continued returning NULL RT scores on the
combined join. Confirmed present in rt_movies_clean with year 2003.

**Analysis:**
TMDB records 28 Days Later with a release_date of 2002-10-31 (UK theatrical
release). RT records it as 2003 (US theatrical release). The title + year join
condition fails because the year extracted from TMDB's date (2002) does not match
RT's year (2003).
This is not a data error in either source — both dates are correct within their
own context. RT consistently uses US release dates whilst TMDB defaults to the
earliest known release date, which for international films is often the country
of origin.

**Resolution:**
No code fix applied. This is an expected limitation of a title+year join across
sources with different release date conventions. Films with staggered international
releases will systematically null out on the RT join. Known affected titles should
be noted here as they are identified.

Known affected titles:
28 Days Later — UK 2002 (TMDB) vs US 2003 (RT)

---

## Insight Layer

# Closed Questions
- Is the 1980s wide budget -94.25% ROI a data error or genuine?
    It's not a data error. Michael Mann's Manhunter had a $150M budget and returned only $8.6M. It is the sole wide budget horror film in the 1980s in this dataset, 
    meaning the entire decade's wide tier average is a single film. There is historical significance, however, since Hannibal Lecter was introduced to cinema
    and was critically / commercially rejected on release. The franchise that was seeded here became one of horror's most valuable IP through Silence of the Lambs (1991),
    truly a case study in long-term IP value amidst short-term theatrical performance.

- What separates the 65 micro films that exceeded 1,000% from the 42 that lost money?
    **Primary Findings**
    Ratings aren't actually that far off from each other (0.7 rounded differential). Aesthetic appeal isn't necessarily a primary predictor.
    Biggest difference is avg_votes which is interesting as a key factor.
    Average runtime is irrelevant (1 minute difference). 

    **Causality Caveat**: 
    Vote count may reflect success rather than predict 
    it. Wider distribution generates more ratings, not the reverse.

    **Interpreted Finding**:
    Micro budget horror winners and losers are nearly identical in quality, reception, and runtime. However, winners accumulate significantly more audience engagement - suggesting 
    that distribution reach and marketing exposure matter more than the film itself at this budget level. This implies the product isn't necessarily the differentiatior,
    at least as much as getting seen is. You can have a masterpiece horror movie that is incredibly vague and poorly marketed. 
    
    **Personal Notes**:
    This makes sense since Blair Witch and Paranormal Activity were marketing phenomena, the former being close to one of the earliest ARGs in terms of 
    marketing with a full on interactable website. I have a personal anecdotal report from my parents at the time stating that a small sample of viewers
    from Mexico had originally conceived the movie as rumored real found footage. Anecdotal data is weak, but food for thought, especially when confirming
    rumors on the internet was not as common at the time of Blair Witch's release.

# Open Questions
- Does micro budget advantage hold when controlling for genre within horror?