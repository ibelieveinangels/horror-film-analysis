# Analysis Notes
*Last updated: March 2026*

---

## Assessment Brief
Horror is a highly profitable genre, particularly in the micro budget category, even when unicorns are removed.

---

## Glossary

**Pre-Analysis**

1. TMDB
    - horror_films_clean - Data Dictionary, Summary of Key Details
    - horror_financial - General, Summary of Key Details
2. IMDb - Data Quality Log
3. Rotten Tomatoes - Data Quality Log

**Analysis**

4. Normalization, Joins
5. Tables
6. Querying - Methodology Caveats, Templates

**Post-Analysis**

7. Insight Layer
    - Finance Q1: The ROI Curve
    - Finance Q2: Release Patterns
    - Reception Q1: Critic vs. Audience Divergence
    - Reception Q2: The Top Critic Effect
    - Reception Q3: Distribution & Commercial Viability
    - Industry Trends Q1: Subgenre Cycles
    - Industry Trends Q2: Production Geography
8. Open Questions

---

## 1. TMDB

### Data Dictionary - horror_films_clean

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


### Summary of Key Details - horror_films_clean

**Streaming anomaly:** 
Some films show budget but zero revenue due to direct-to-streaming releases (e.g. Day Shift, Netflix 2022). These are 
not theatrical failures - they require separate treatment in release pattern analysis.

### **General** - horror_financial

The following was queried for in SQLite:

- ROI by budget tier
- Best performing decades by average ROI
- Top 20 highest ROI horror films ever
- Does micro budget ROI hold across all decades or is it a modern phenomenon?
- What is the ROI distribution within micro budget - is the average skewed by outliers?

### **Summary of Key Details** - horror_financial

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
only 6 films - Blair Witch distorting a tiny sample. Decade-level analysis 
requires noting sample sizes alongside averages.

---

## 2. IMDb

### IMDb - Data Quality Log
No data quality issues identified during processing. 
Pipeline ran cleanly via 04_merge_imdb_data.py; exact joins on tconst and title+year fuzzy fallback.

---

## 3. Rotten Tomatoes

### Rotten Tomatoes - Data Quality Log

#### Issue 1 - Duplicate Records in rt_movies_clean
**Problem identified:**
Running a duplicate check on rt_movies_clean revealed 300+ titles appearing
multiple times. Initially flagged by 28 Days Later returning NULL on the
combined join despite being present in the table.

**Analysis:**
1. True duplicates - same title, same valid year (e.g. 28 Days Later 2003 x2).
Caused by RT's concurrent scrape hitting the same page twice.
2. Year=0 groupings - different films sharing a generic title
(e.g. "Dracula", "Frankenstein", "Nightmare") with unparseable release dates,
falsely appearing as duplicates due to failed date parsing.

**Resolution:**
Added drop_duplicates(subset=["title", "release_date_year"]) to
process_rt_movies() in 05_process_rt_data.py before CSV export.
This collapses true scrape dupes while leaving year=0 records intact -
they remain in rt_movies_clean but never match on the title + year
join condition, so they don't pollute analysis.

#### Issue 2 - Staggered International Releases Causing NULL Joins
**Problem identified:**
After deduplication, 28 Days Later continued returning NULL RT scores on the
combined join. Confirmed present in rt_movies_clean with year 2003.

**Analysis:**
TMDB records 28 Days Later with a release_date of 2002-10-31 (UK theatrical
release). RT records it as 2003 (US theatrical release). The title + year join
condition fails because the year extracted from TMDB's date (2002) does not match
RT's year (2003).
This is not a data error in either source - both dates are correct within their
own context. RT consistently uses US release dates whilst TMDB defaults to the
earliest known release date, which for international films is often the country
of origin.

**Resolution:**
No code fix applied. This is an expected limitation of a title+year join across
sources with different release date conventions. Films with staggered international
releases will systematically null out on the RT join. Known affected titles should
be noted here as they are identified.

Known affected titles:
28 Days Later - UK 2002 (TMDB) vs US 2003 (RT)

---

## 4. Normalization and Joining

### Why film_genres was created

`genre_ids` in `horror_films_clean` is stored as pipe-delimited TEXT (e.g. "27|53|9648").
Grouping by subgenre in SQLite would require fragile string parsing with INSTR and SUBSTR
on every query. `06_normalize_genres.py` explodes this into a clean long-format table
where each row is one film-genre pair, enabling simple GROUP BY queries for all
subgenre analysis.

TV Movie (TMDB ID 10770) is excluded at the normalization stage - TV productions
don't have theatrical box office and would skew financial and reception analysis.
502 films carry this tag in horror_films_clean.

### normalized_score in rt_reviews_clean

`original_score` in the raw RT reviews data is a heterogeneous string field -
critics submit scores in their own format ("A+", "3.5/5", "7/10", "B-").
`normalize_score()` was added to `05_process_rt_data.py` to convert all formats
to a 0–100 float scale before CSV export. The `normalized_score` column is used
for all Top Critic Effect queries instead of `original_score`.

---

## 5. Tables

| Table | Description |
|---|---|
| film_genres | Normalized long-format genre table exploded from horror_films_clean.genre_ids. One row per film-genre pair. TV Movie excluded. |
| horror_combined | VIEW. Joins horror_films_clean + imdb_title_ratings_clean + rt_movies_clean on title+year. Includes computed columns: roi, release_month, critic_audience_delta. Used for reception and trend analysis only. |
| horror_films_clean | Cleaned TMDB horror data. 12,734 films. Primary source table. |
| horror_financial | TMDB horror subset with verified non-zero budget and revenue. 1,318 films. Used for all Finance queries. |
| imdb_title_basics_clean | Cleaned IMDb horror films with release year and TMDB-compatible genre_ids. |
| imdb_title_ratings_clean | Cleaned IMDb horror films with vote_average and vote_count. |
| rt_movies_clean | Cleaned RT horror films with tomatometer, audience_score, director, distributor, revenue, original_language, genre_ids. |
| rt_reviews_clean | Individual RT critic reviews with is_top_critic, normalized_score, score_sentiment, publication_name. |

---

## 6. Querying

### Methodology Caveats

**Vote threshold:**
All reception queries apply `vote_count > 25` (IMDb) to exclude statistically
unreliable ratings. A film with 1 review at 100% tomatometer is not comparable
to Alien at 98% from hundreds of critics. 25 votes is a conservative floor that
preserves foreign and independent horror while excluding truly unreviewed films.

**tomatometer vs audience_score comparability:**
These are not equivalent metrics. Tomatometer is a binary fresh/rotten percentage -
each critic review is classified, not scored. Audience score is an average rating
converted to a percentage. `critic_audience_delta` is directionally valid
(positive = critics rate higher, negative = audiences rate higher) but
methodologically imprecise as an absolute magnitude. All divergence findings
should be interpreted as directional signals, not exact gaps.

**horror_combined vs horror_financial:**
`horror_combined` is used exclusively for reception and trend analysis.
All Finance queries use `horror_financial` which contains only films with
verified non-zero budget and revenue. `budget=0` in horror_films_clean means
unknown, not zero-cost.

**TV Movie exclusion:**
TMDB genre ID 10770 (TV Movie) is excluded from film_genres at normalization.
502 films carry this tag. Add `WHERE genre_name != 'TV Movie'` to any query
joining film_genres if TV Movie exclusion was not applied at the script level.

**Unicorn threshold:**
Films with ROI > 10,000% are flagged as unicorns and reported separately.
Raw and adjusted figures are both documented for all ROI findings.
Primary unicorns: Paranormal Activity (Sep, ROI 1,288,938%), Blair Witch Project (Jul, ROI 414,298%).

### Query Templates

```sql
-- Finance queries
SELECT ... FROM horror_financial    -- never horror_combined for ROI

-- Reception queries
SELECT ... FROM horror_combined
WHERE tomatometer IS NOT NULL
AND audience_score IS NOT NULL
AND vote_count > 25

-- Trend queries
SELECT ... FROM horror_combined
WHERE release_year > 0

-- Subgenre queries
SELECT ... FROM film_genres
-- TV Movie already excluded at normalization stage
```

---

## 7. Insight Layer

### Finance - Q1: The ROI Curve
*← Average ROI % by budget tier (micro / low / mid / wide)*

**Core assumption verdict: CONFIRMED**
Micro budget horror consistently outperforms all other budget tiers across
every decade in the dataset. No obvious advantage exists to investing higher
than necessary in horror.

**Core finding:**
Micro budget avg ROI: 10,662% (raw) | 1,114% (excluding ROI > 10,000%).
Both figures are the highest of any budget tier. Two films - Paranormal Activity
and Blair Witch Project - are responsible for the extreme headline figure.

**Risk profile:**
42 of 206 micro budget films (20%) lost money.
65 of 206 (31%) exceeded 1,000% ROI.
High variance, high ceiling - low risk entry point with highly variable return.

**Small sample caveat:**
1990s micro avg ROI of 69,396% is based on only 6 films - Blair Witch
distorting a tiny sample. Decade-level analysis requires sample sizes
noted alongside averages.

#### Sub-finding - What separates the 65 winners from the 42 losers?

**Primary findings:**
Rating differential between winners and losers: 0.7 (negligible).
Aesthetic quality is not a primary predictor of micro budget success.
Largest differentiator: avg_vote_count - winners accumulate significantly
more audience engagement than losers.
Runtime differential: 1 minute (irrelevant).

**Causality caveat:**
Vote count may reflect success rather than predict it. Wider distribution
generates more ratings - not the reverse.

**Interpreted finding:**
Micro budget horror winners and losers are nearly identical in quality,
reception, and runtime. Distribution reach and marketing exposure matter
more than the film itself at this budget level. You can produce a masterpiece
that nobody sees.

**Personal note:**
Blair Witch and Paranormal Activity were marketing phenomena. Blair Witch
is among the earliest examples of ARG-style marketing with a fully
interactive website. Anecdotal report from family: a subset of Mexican
viewers initially believed Blair Witch was real found footage - plausible
given that fact-checking on the internet was not normalized at the time
of the 1999 release.

#### Sub-finding - 1980s Wide Budget Anomaly (Manhunter)

**Finding:**
The 1980s wide budget tier shows -94.25% avg ROI. This is not a data error.
Michael Mann's Manhunter (1986) is the sole wide budget horror film from
the 1980s in this dataset - $15M budget, $8.6M return.

**Historical significance:**
Manhunter introduced Hannibal Lecter to cinema. It was commercially and
critically rejected on release. The IP seeded here became one of horror's
most valuable franchises through Silence of the Lambs (1991) - a definitive
case study in long-term IP value versus short-term theatrical performance.

---

### Finance - Q2: Release Patterns
*← Average revenue and ROI by release month*

**Core assumption verdict: REJECTED**
October maximizes volume but not revenue or ROI. June outperforms on
revenue. No November halo effect exists in the data.

**Raw findings (all films):**

| Month | Films | Avg Revenue | Avg ROI |
|---|---|---|---|
| 1 | 112 | $36,978,673 | 655.4% |
| 2 | 90 | $33,034,431 | 309.5% |
| 3 | 91 | $30,036,207 | 382.7% |
| 4 | 101 | $31,837,948 | 430.2% |
| 5 | 116 | $38,386,079 | 440.8% |
| 6 | 96 | $52,095,485 | 558.2% |
| 7 | 98 | $50,023,441 | 5,297.2% |
| 8 | 133 | $49,016,872 | 834.3% |
| 9 | 144 | $43,479,322 | 9,342.1% |
| 10 | 172 | $41,447,324 | 1,031.5% |
| 11 | 88 | $30,508,682 | 988.3% |
| 12 | 77 | $42,409,506 | 372.6% |

**Unicorn distortion identified:**
September (9,342% avg ROI): Paranormal Activity (ROI 1,288,938%) dominates.
Passive values: Dawn of the Dead 8,493% | Satan's Slaves 7,428% | Eraserhead 6,900% | The Blob 3,536%

July (5,297% avg ROI): Blair Witch Project (ROI 414,298%) dominates.
Passive values: The Gallows 42,864% | Blood Feast 16,226% | The Hills Have Eyes 7,042% | The Collector 3,252%

**Adjusted findings (ROI ≤ 10,000%):**

| Month | Films | Avg Revenue | Avg ROI |
|---|---|---|---|
| 1 | 110 | $36,706,184 | 447.5% |
| 2 | 90 | $33,034,431 | 309.5% |
| 3 | 91 | $30,036,207 | 382.7% |
| 4 | 101 | $31,837,948 | 430.2% |
| 5 | 115 | $38,200,266 | 351.1% |
| 6 | 96 | $52,095,485 | 558.2% |
| 7 | 95 | $48,491,513 | 481.4% |
| 8 | 130 | $48,241,378 | 305.5% |
| 9 | 143 | $42,431,235 | 393.9% |
| 10 | 168 | $41,599,636 | 565.8% |
| 11 | 87 | $30,542,228 | 395.7% |
| 12 | 77 | $42,409,506 | 372.6% |

**Adjusted finding:**
June and October emerge as the dual peak months.
June: highest avg revenue ($52.1M), ROI 558.2%.
October: highest volume (168 films), ROI 565.8% - essentially tied with June.
Summer (June–August) consistently outperforms on revenue.
November halo effect absent - 87 films, $30.5M avg revenue, ranks last on volume.

---

### Reception - Q1: Critic vs. Audience Divergence
*← Tomatometer vs. audience score delta by subgenre, crossed with revenue from horror_financial*

**Core assumption verdict: REJECTED**
Critical consensus does not predict commercial performance in horror.
Audience-preferred subgenres (Action, Adventure, Crime) outperform 
critic-preferred subgenres on revenue. Drama is the sole exception.

**Raw Findings (by Subgenre)**

WITH VOTE COUNT > 25

Horror overall (all films):
| Genre | Films | Avg Tomatometer | Avg Audience Score | Avg Delta |
|---|---|---|---|---|
| Horror | 944 | 51.2 | 48.2 | +3.0 |

| Genre | Films | Avg Tomatometer | Avg Audience Score | Avg Delta |
|---|---|---|---|---|
| Documentary | 1 | 71.0 | 39.0 | +32.0 |
| Western | 5 | 63.4 | 37.6 | +25.8 |
| History | 1 | 27.0 | 9.0 | +18.0 |
| Drama | 140 | 62.2 | 55.5 | +6.7 |
| Science Fiction | 146 | 55.3 | 48.7 | +6.6 |
| Comedy | 116 | 58.0 | 54.3 | +3.7 |
| Mystery | 194 | 52.2 | 50.3 | +1.9 |
| War | 5 | 64.6 | 62.8 | +1.8 |
| Crime | 35 | 56.4 | 54.8 | +1.6 |
| Thriller | 428 | 47.3 | 46.5 | +0.9 |
| Adventure | 20 | 54.8 | 54.7 | +0.1 |
| Fantasy | 85 | 50.5 | 51.0 | -0.6 |
| Romance | 22 | 57.0 | 57.8 | -0.8 |
| Action | 70 | 40.9 | 49.1 | -8.3 |
| Music | 6 | 56.0 | 64.7 | -8.7 |

**Core insights:**
Critics and general audiences broadly agree on horror - overall delta of
+3.0 across 944 films. Horror as a genre does not produce systematic
critic-audience divergence at the macro level.

Divergence is subgenre-specific:
- Drama (+6.7) and Sci-Fi (+6.6) show the largest reliable critic premium
  - critics reward craft and ambition in elevated horror subgenres.
- Action (-8.3) shows the largest reliable audience premium - audiences
  enjoy action-horror more than critics, consistent with a hypothesis that
  critics penalize genre films perceived as prioritizing spectacle over craft.
  However this cannot be confirmed from score data alone.
- Thriller (428 films, delta +0.9) - the dominant co-genre - shows near
  perfect critic-audience agreement, suggesting mainstream horror-thriller
  is the most universally evaluated subgenre.

**Sample Size Caveat**
Documentary (1 film), Western (5), History (1), War (5) are statistically
unreliable. Findings weighted toward high-volume subgenres:
Thriller (428), Mystery (194), Sci-Fi (146), Drama (140), Comedy (116).

**Raw Findings (by Subgenre with Financial Data)**

| Genre | Films | Avg Delta | Avg Revenue | Avg ROI |
|---|---|---|---|---|
| Western | 1 | +17.0 | $475,846 | -73.6% |
| War | 1 | +15.0 | $41,657,844 | 9.6% |
| Drama | 66 | +2.6 | $53,026,053 | 278.5% |
| Science Fiction | 90 | 0.0 | $49,606,569 | 438.5% |
| Comedy | 56 | -0.2 | $28,268,802 | 229.4% |
| Mystery | 120 | -2.1 | $70,264,399 | 4,068.4% |
| Thriller | 233 | -4.1 | $58,481,209 | 844.4% |
| Romance | 14 | -4.3 | $44,296,668 | 238.7% |
| Adventure | 11 | -4.3 | $105,287,223 | 780.8% |
| Fantasy | 45 | -6.0 | $54,417,702 | 197.6% |
| Action | 47 | -12.1 | $84,011,570 | 146.7% |
| Crime | 18 | -14.2 | $78,147,677 | 1,075.7% |
| Music | 1 | -36.0 | $198,883 | -97.7% |

Mystery ROI (4,068.4%) is unicorn-distorted by (Paranormal Activity, The Blair Witch Project, The Legend of Boggy Creek).

#### Sub-finding - Documentary Anomaly (Wrinkles the Clown)

**Documentary anomaly - Wrinkles the Clown (2019):**
The sole documentary in the dataset. Tomatometer 68% vs audience score 36%, 
delta of +32.0, the largest in the dataset. The divergence is explained
by audience composition: a significant portion of audience reviewers
watched the film due to social media virality rather than documentary
interest, resulting in deflated audience scores from mismatched expectations.
Illustrates how audience score can reflect distribution reach and viewer
intent rather than film quality. Mirrors the Blair Witch marketing
phenomenon observed in Finance Q1.

Manual review of audience submissions reveals the score deflation
is not a reflection of film quality. Submissions include: a review
of Joker (wrong film entirely), a submission reading only "When is
it coming out", duplicate reviews copy-pasted across accounts, and
multiple reviewers explicitly stating they expected a horror film
rather than a documentary. The 36% audience score is functionally
invalid as a quality signal for this title.

This is the most direct illustration in the dataset of why audience
score requires critical interpretation - it measures engagement
context as much as film reception.

#### Sub-finding - Cult Film Anomaly (Repo! The Genetic Opera)

**Music Anomaly - Repo! The Genetic Opera**
Music anomaly. 37% tomatometer, 73% audience score, -36 delta. Cult horror musical with a deeply devoted 
fanbase that critics largely dismissed. One film but a clean illustration of the cult film dynamic where 
critical reception is essentially irrelevant to audience devotion.

#### Interpreted Finding — Delta vs. Revenue
Among financially documented films, audience-favored subgenres 
dominate on revenue. Action (-12.1 delta, $84M avg revenue) and 
Adventure (-4.3 delta, $105M avg revenue) are the two highest-earning 
co-genres - both audience-preferred over critics. Crime (-14.2 delta) 
shows the largest audience premium of any reliable sample and still 
produces 1,075% avg ROI.

Drama is the only subgenre where a critic premium (+2.6) coexists 
with strong revenue ($53M) and solid ROI (278.5%), suggesting elevated 
horror-drama is the one subgenre where critical approval and commercial 
performance align.

The data inverts the core assumption: audience preference, not critical 
consensus, correlates with higher revenue in horror. Films audiences 
enjoy more than critics earn more, not less.

---

### Reception - Q2: The Top Critic Effect
*← Average normalized_score by is_top_critic, grouped by subgenre using rt_reviews_clean joined to rt_movies_clean*

*(Pending)*

### Reception - Q3: Distribution & Commercial Viability
*← Average ROI and revenue by distributor tier (major / mid / independent) by decade*

*(Pending)*

---

### Industry Trends - Q1: Subgenre Cycles
*← Horror film count by subgenre by decade overlaid with cultural_timeline.csv*

**Baseline subgenre distribution (film_genres, Horror and TV Movie excluded):**

| Genre | Count | % of Co-Genre Tags |
|---|---|---|
| Thriller | 4,764 | 27.9% |
| Mystery | 1,980 | 11.6% |
| Drama | 1,931 | 11.3% |
| Science Fiction | 1,924 | 11.3% |
| Comedy | 1,879 | 11.0% |
| Action | 1,239 | 7.3% |
| Fantasy | 1,134 | 6.6% |
| Crime | 709 | 4.2% |
| Adventure | 408 | 2.4% |
| Animation | 307 | 1.8% |
| Romance | 307 | 1.8% |
| Music | 98 | 0.6% |
| Documentary | 93 | 0.5% |
| Family | 88 | 0.5% |
| Western | 73 | 0.4% |
| War | 67 | 0.4% |
| History | 56 | 0.3% |

Total co-genre tag assignments: 29,791 across 12,734 films.
Average co-genres per film: 2.38 - horror rarely operates as a pure single-genre product.

Thriller dominates at 27.9% of co-genre tags, appearing alongside horror in 4,764 films.
Top four co-genres (Thriller, Mystery, Drama, Sci-Fi) account for 62% of all co-genre assignments,
confirming horror clusters heavily around psychological and tension-driven adjacent genres.

This distribution establishes the baseline against which decade-level subgenre shifts will be measured.

*(Decade-level analysis pending)*

### Industry Trends - Q2: Production Geography
*← Tomatometer vs. audience score divergence by original_language and production_country*

*(Pending)*

---

## Open Questions
- Does micro budget advantage hold when controlling for genre within horror?