from pathlib import Path

# PROJECT ROOT SETUP (Goes up 2 levels to the base directory)
BASE_DIR = Path(__file__).resolve().parent.parent

# DATA PATHS (holds csv and pkl backups)
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"

RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

# Input Files
RAW_ENV_DATA_PATH = RAW_DIR / "Kano_StateWide_Vegetation_Data.csv"
RAW_PRICE_DATA_PATH = RAW_DIR / "FEWS_NET_Staple_Food_Price_Data.csv"

# Processed Output
PROCESSED_DATA_PATH = PROCESSED_DIR / "processed_kano_food_security_data.csv"
PROCESSED_ENV_DATA_PATH = PROCESSED_DIR / "latest_lga_env_data.csv"
PROCESSED_LGA_MAP_PATH = PROCESSED_DIR / "kano_lga_map.geojson"

# Shapefile for Kano LGAs (for mapping)
LGA_SHP_FILE_PATH = PROCESSED_DIR / "kano_shp" / "kano_lga.shp"

# Ensure folders exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)