# Blood Money

<a target="_blank" href="https://cookiecutter-data-science.drivendata.org/">
    <img src="https://img.shields.io/badge/CCDS-Project%20template-328F97?logo=cookiecutter" />
</a>

This project delivers a comprehensive end-to-end technical analysis of the horror film industry, examining: 
1. **Finance:** How has the horror film industry morphed financially since its beginning?
2. **Reception:** What predicts audience reception and what is its correlative relationship with financial outcomes?
3. **Aesthetics:** How have horror film aesthetics differed by factors like release date or production locations?

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
├── README.md          <- The top-level README for developers using this project.
├── data
│   ├── external       <- Data from third party sources.
│   ├── interim        <- Intermediate data that has been transformed.
│   ├── processed      <- The final, canonical data sets for modeling.
│   └── raw            <- The original, immutable data dump.
│
├── docs               <- Documents
│
│
├── notebooks          <- Jupyter notebooks for EDA.
│
├── pyproject.toml     <- Project configuration file.
│
├── references         <- Data dictionaries, manuals, and all other explanatory materials.
│
├── reports            <- Generated analysis as HTML, PDF, LaTeX, etc.
│   ├── analysis_notes.md
│   └── figures        <- Generated graphics and PowerBI dashboards (.pbix).
│
├── requirements.txt   <- TThe requirements file for reproducing the analysis environment.
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
    └── plots.py                <- Code to create visualizations
```

--------

---

## Questions and Core Assumptions

**Finance**

1. The ROI Curve: What is the actual return on investment curve for horror budgets? Is there a sweet spot where low-budget outperforms, and where does spending more stop mattering?
Core Assumption: Micro and low-budget horror films produce a significantly higher ROI percentage than high-budget horror films due to the genre's inherent risk mitigation.

2. Release Patterns: What release patterns maximize horror performance? Is the October clustering actually optimal or is it conventional wisdom that the data contradicts?
Core Assumption: October releases maximize revenue, with a halo effect bleeding into November.

**Reception**

1. Critic vs. Audience Divergence: Where do critics and audiences most violently disagree on horror, and is there a pattern in what causes that divergence?
Core Assumption: Critics and audiences most violently disagree on aesthetic appeal versus subjective fear. Critics judge on objective filmmaking merits, while audiences grade on visceral subjective fear.

2. Franchise Viability: Does franchise horror perform better or worse per dollar than standalone films, and has that changed over time?
Core Assumption: Franchise horror films perform better per dollar than standalone films due to established IP and guaranteed baseline theater turnout.

**Aesthetics**

1. Subgenre Cycles: How has subgenre popularity cycled over decades (slasher, supernatural, psychological, folk horror) and do those cycles correlate with broader cultural events?
Core Assumption: Subgenre popularity cycles directly mirror historical and cultural anxieties (e.g., a shift from slasher to psychological/supernatural), rather than shifting randomly.

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
(Pending) Identify and appropriate Rotten Tomatoes dataset on Kaggle or scraping feasibility.

S - Scrub (Cleaning & Joining)
(Completed) 02_load_tmdb_to_sql.py: Deduplicated and reduced TMDB raw data to 12,734 clean films; created financial subset of 1,318 films with verified budget/revenue.
(Completed) 03_imdb_to_csv.py: Converted IMDb TSVs into CSVs ; 04_merge_imdb_data.py: Cleaned and transformed raw IMDb CSVs into processed data ready for analysis. 
(Pending) Integrate Rotten Tomatoes dataset.

E - Explore (Exploratory Data Analysis)
(In Progress) Initial SQL exploration in SQLite (ROI by budget tier, decade performance).
(Pending) Integrate cultural_timeline.csv to map real-world events against subgenre spikes.

M - Model (Statistical Analysis)
(Pending) Perform statistical testing (e.g., correlations between critic divergence and ROI) using Python (SciPy/Statsmodels).

N - iNterpret (Visualization & Insights)
(Pending) Build Power BI Dashboard.
(Pending) Finalize reports/analysis_notes.md into an executive summary of business recommendations.

Miscellaneous
(Completed) Codebase migration to Cookiecutter Data Science