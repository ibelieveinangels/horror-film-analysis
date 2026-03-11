from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

# Load environment variables from .env file if it exists
load_dotenv()

# Paths
PROJ_ROOT = Path(__file__).resolve().parents[1]
logger.info(f"PROJ_ROOT path is: {PROJ_ROOT}")

DATA_DIR = PROJ_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
INTERIM_DATA_DIR = DATA_DIR / "interim"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EXTERNAL_DATA_DIR = DATA_DIR / "external"

MODELS_DIR = PROJ_ROOT / "models"

REPORTS_DIR = PROJ_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

# ── Rotten Tomatoes source files ──
RT_MOVIES_PATH  = RAW_DATA_DIR / "rotten_tomatoes_movies.csv"
RT_REVIEWS_PATH = RAW_DATA_DIR / "rotten_tomatoes_movie_reviews.csv"

# ── IMDb source files ──
IMDB_BASICS_PATH  = RAW_DATA_DIR / "title_basics.csv"
IMDB_RATINGS_PATH = RAW_DATA_DIR / "title_ratings.csv"

# ── 04_merge_imdb_data.py output files ──
BASICS_CLEAN_PATH    = PROCESSED_DATA_DIR / "imdb_title_basics_clean.csv"
RATINGS_CLEAN_PATH   = PROCESSED_DATA_DIR / "imdb_title_ratings_clean.csv"
QUALITY_REPORT_PATH  = PROCESSED_DATA_DIR / "data_quality_report.csv"
ERROR_LOG_PATH       = PROCESSED_DATA_DIR / "error_log.csv"
FUZZY_REVIEW_PATH    = PROCESSED_DATA_DIR / "fuzzy_review.csv"
INTEGRATION_LOG_PATH = PROCESSED_DATA_DIR / "data_integration.log"

# ── Database ──
DB_PATH = INTERIM_DATA_DIR / "horror_analysis.db"

# ── Pipeline tuning ──
FUZZY_THRESHOLD = 80      # Minimum rapidfuzz score to accept a fuzzy title match
CHUNK_SIZE      = 10_000  # Rows per chunk when reading large files
LARGE_FILE_MB   = 5       # Files above this size (MB) trigger chunked reading

# If tqdm is installed, configure loguru with tqdm.write
# https://github.com/Delgan/loguru/issues/135
try:
    from tqdm import tqdm

    logger.remove(0)
    logger.add(lambda msg: tqdm.write(msg, end=""), colorize=True)
except ModuleNotFoundError:
    pass