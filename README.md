# Blood Money

<a target="_blank" href="https://cookiecutter-data-science.drivendata.org/">
    <img src="https://img.shields.io/badge/CCDS-Project%20template-328F97?logo=cookiecutter" />
</a>

This project delivers a comprehensive end-to-end technical analysis of the horror film industry, examining: 
1. **Finance:** How has the economics of horror evolved across budget tiers, release strategies, and decades?
2. **Reception:** How do critics, top critics, and audiences diverge in their evaluation of horror, and does that divergence predict or correlate with financial performance?
3. **Industry Trends:** How have the cultural and industrial patterns of horror production — subgenre, geography, studio vs. independent — shifted over time?

Furthermore, this project seeks to exemplify my capabilities as a Data Analyst for potential employers to assess. 
For comprehensive information regarding the analyses, see `reports/analysis_notes.md` within the repository.

[GitHub](https://github.com/ibelieveinangels)
[LinkedIn](https://linkedin.com/in/jose-angel-zamudio-893843382)

## Table of Contents
1. [Project Organization](#project-organization)
2. [Questions and Core Assumptions](#questions-and-core-assumptions)
3. [Tools and Methodology](#tools-and-methodology)
4. [Project Status and Progression Notes](#project-status-and-progression-notes)

---

## Project Organization

```
├── LICENSE            <- MIT License
├── Makefile           <- Makefile with convenience commands like `make data` or `make train`
├── README.md          <- The top-level README for developers using this project
├── data
│   ├── external       <- Data from third party sources
│   ├── interim        <- Intermediate data that has been transformed
│   ├── processed      <- The final, canonical data sets for modeling
│   │   ├── technical  <- Data integration docs, quality reports, fuzzy review, error logs
│   └── raw            <- The original, immutable data dump
│
├── docs               <- Documents
│
│
├── notebooks          <- Jupyter notebooks for EDA
│
├── pyproject.toml     <- Project configuration file
│
├── references         <- Data dictionaries, manuals, and all other explanatory materials
│
├── reports            <- Generated analysis as HTML, PDF, LaTeX, etc
│   ├── analysis_notes.md
│   └── figures        <- Generated graphics and PowerBI dashboards (.pbix)
│
├── requirements.txt   <- TThe requirements file for reproducing the analysis environment
│
│
└── blood_money   <- Source code for use in this project.
    │
    ├── __init__.py             <- Makes blood_money a Python module
    │
    ├── config.py               <- Store useful variables and configuration
    │
    ├── 01_acquire_tmdb_data    <- Scrapes raw horror data off TMDB w/ API
    │
    ├── 02_load_tmdb_to_sql     <- Cleans and loads raw TMDB data into SQL
    │
    ├── 03_imdb_to_csv          <- Converts IMDB TSV data into CSV format
    │
    ├── 04_merge_imdb_data      <- Normalizes IMDb data to TMDB schema; filters for Horror only; fuzzy-joins to produce clean datasets for SQL ingestion
    │
    ├── 05_process_rt_data      <- Normalizes RT data to TMDB schema; filters for Horror only; deduplicates scrape artifacts; two-pass chunk loading to extract horror critic reviews from 391MB dataset
    │
    └── plots.py                <- Code to create visualizations
```

--------

---

## Questions and Core Assumptions

**Finance**

1. The ROI Curve: What is the actual return on investment curve 
   for horror budgets? Is there a sweet spot where low-budget 
   outperforms, and where does spending more stop mattering?
   
   Core Assumption: Micro and low-budget horror films produce a 
   significantly higher ROI percentage than high-budget horror films 
   due to the genre's inherent risk mitigation.
   
   ← Average ROI % by budget tier (micro / low / mid / wide)

2. Release Patterns: What release patterns maximize horror 
   performance? Is the October clustering actually optimal or is it 
   conventional wisdom that the data contradicts?
   
   Core Assumption: October releases maximize revenue, with a halo 
   effect bleeding into November.
   
   ← Average revenue and ROI by release month

**Reception**

1. Critic vs. Audience Divergence: Where do critics and audiences 
   most violently disagree on horror, and does that divergence 
   correlate with financial performance?

   Core Assumption: High critic-audience divergence is concentrated 
   in arthouse and elevated horror — and those films underperform 
   commercially despite critical praise, suggesting critical consensus 
   does not translate to box office in this genre.

   ← Tomatometer vs. audience score delta by subgenre, crossed with 
   revenue from horror_financial

2. The Top Critic Effect: Do top critics evaluate horror 
   systematically differently from general critics, and which 
   subgenres show the largest top critic penalty or premium?

   Core Assumption: Top critics apply a prestige bias that penalizes 
   mainstream horror (slasher, creature feature) while rewarding 
   elevated and psychological horror, creating a measurable scoring 
   gap versus general critics.

   ← Average original_score by is_top_critic, grouped by subgenre 
   using rt_reviews_clean joined to rt_movies_clean

3. Distribution & Commercial Viability: Does major studio 
   distribution produce better ROI than independent distribution 
   in horror, and has that relationship changed post-streaming?

   Core Assumption: Independent horror produces higher ROI than 
   studio horror due to lower cost basis, but studio horror produces 
   higher absolute revenue due to marketing spend and wider release.

   ← Average ROI and revenue by distributor tier 
   (major / mid / independent) by decade

**Industry Trends**

1. Subgenre Cycles: How has subgenre popularity cycled over 
   decades and do those cycles correlate with broader cultural events?

   Core Assumption: Subgenre popularity cycles directly mirror 
   historical and cultural anxieties rather than shifting randomly.

   ← Horror film count by subgenre by decade overlaid with 
   cultural_timeline.csv

2. Production Geography: How has the geographic origin of horror 
   shifted over decades, and do non-English productions perform 
   differently with critics versus audiences?

   Core Assumption: Non-English horror outperforms English-language 
   horror with critics relative to audience scores, reflecting a 
   critical bias toward foreign arthouse horror that general audiences 
   find less accessible.
   
   ← Tomatometer vs. audience score divergence by original_language 
   and production_country

---

## Tools and Methodology

**Tools:**
OSEMN - Lifecycle Framework
Cookiecutter Data Science - Project Structure
Python - Acquisition, Transformation, Advanced Analysis
SQL (SQLite) -  Cleaning, Aggregation, Relational Joins
PowerBI - Interactive Business Visualization
GitHub - Version Control
Claude - Assistive programming

**Methodology:**

OSEMN
    Multiple data sources and relatively broad questions lead me to OSEMN as a non-linear, repeatable framework to ensure a structured approach to business problem-solving.
Cookiecutter Data Science
    Chosen due to its positive reception to ensure a structured approach to codebase management.
Python
    Scripts are utilized for automated web scraping (TMDB API). Python is also leveraged for seamless data transformation (loading raw CSVs into SQLite to create relational tables).
SQL
    Chosen as the primary data-wrangling engine due to its efficiency with relational data. 
    Used for database storage, joining TMDB with IMDb/Rotten Tomatoes, and creating aggregated metrics (ROI, budget tiers, decade groupings).
PowerBI
    Utilized to translate statistical findings into an interactive, industry-standard deliverable for non-technical stakeholders.
Claude
    Used deliberately for assistive python scripting to accelerate workflow.
GitHub
    Industry standard for project documentation and version history.

---

## Project Status and Progression Notes

O - Obtain (Data Acquisition)
(Completed) 01_acquire_tmdb_data.py: executed: 99,007 raw films collected via TMDB API.
(Completed) Acquired relevant IMDb non-commercial datasets manually.
(Completed) Identified an appropriate Rotten Tomatoes dataset on Kaggle.

S - Scrub (Cleaning & Joining)
(Completed) 02_load_tmdb_to_sql.py: Deduplicated and reduced TMDB raw data to 12,734 clean films; created financial subset of 1,318 films with verified budget/revenue.
(Completed) 03_imdb_to_csv.py: Converted IMDb TSVs into CSVs ; 04_merge_imdb_data.py: Cleaned and transformed raw IMDb CSVs into processed data ready for analysis. 
(Completed) 05_process_rt_data.py: Cleaned and transformed raw rt CSVs into processed data ready for analysis.
(Completed) Successfully normalized and joined 6 cleaned datasets from 3 sources with diverging schemas.

E - Explore (Exploratory Data Analysis)
(In Progress) Initial SQL exploration in SQLite (ROI by budget tier, decade performance).
(Pending) Integrate cultural_timeline.csv to map real-world events against subgenre spikes.

M - Model (Statistical Analysis)
(Pending) Perform statistical testing (e.g., correlations between critic divergence and ROI) using Python (SciPy/Statsmodels).

N - iNterpret (Visualization & Insights)
(Pending) Build Power BI Dashboard.
(Pending) Finalize reports/analysis_notes.md into an executive summary of business recommendations.

Miscellaneous
(Completed) Codebase migration to Cookiecutter Data Science.