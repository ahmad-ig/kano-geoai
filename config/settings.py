from config.paths import *
from config.secrets import *

# BUSINESS LOGIC
TARGET_MARKET = 'Kano, Dawanau'

CROPS = ['Price_Maize', 'Price_Sorghum', 'Price_Millet']
STRESS_TARGET = 'NDVI_Anomaly'

# Map original CSV names to our clean internal names
CROP_RENAME_MAP = {
    'Maize Grain (White)': 'Price_Maize', 
    'Sorghum (White)': 'Price_Sorghum', 
    'Millet (Pearl)': 'Price_Millet'
}

# MODEL CONFIG
XGB_PARAMS = {
    'n_estimators': 500,
    'learning_rate': 0.05,
    'max_depth': 3,
    'random_state': 42,
    'n_jobs': -1
}

# VALIDATION STRATEGY
# Set to last 12 months for experimentation, 0 for production deployment
TEST_MONTHS_CUTOFF = 0 