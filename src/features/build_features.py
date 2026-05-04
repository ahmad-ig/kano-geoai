### FEATURE ENGINEERING

import pandas as pd
import numpy as np

from config import settings
from config.database import get_engine
from src.db.queries import get_processed_features

def load_and_prep_data(engine, filepath=None):
    """
    Loads processed data from PostgreSQL, sets index, and creates necessary
    Diff/Seasonality features for model training.
    """

    print("🔄 Loading and preprocessing data for training from Database...")
    
    # 1. Load Data from PostgreSQL
    df = get_processed_features(engine)

    # Convert Date column to datetime and set as index
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date').set_index('Date')
    df.index.freq = 'MS'  # Set frequency to Month Start

    # --- FEATURE ENGINEERING ---
    # 2. Temporal Features (Trend + Seasonality)
    # Create a linear trend (0, 1, 2, 3...)
    df['Trend_Index'] = range(len(df))

    # Create One-Hot Encoding for Month (Seas_2, Seas_3... Seas_12)
    df['Month'] = df.index.month
    df = pd.get_dummies(df, columns=['Month'], prefix='Seas', drop_first=True)

    # 3. Target Engineering (Price Differences)
    # We predict the CHANGE in price, not the raw price
    for col in settings.CROPS:
        if col in df.columns:
            df[f'{col}_Diff'] = df[col] - df[col].shift(1)
        else:
            print(f"⚠️ Warning: Column {col} not found in dataset.")

    # 4. Cleanup
    # Drop NaNs created by lags (differencing)
    df_clean = df.dropna().copy()

    # 5. Train/Test Split Logic
    if settings.TEST_MONTHS_CUTOFF > 0:
        train_df = df_clean.iloc[:-settings.TEST_MONTHS_CUTOFF]
        print(f"📉 Training Mode: Using first {len(train_df)} months (Holding back last {settings.TEST_MONTHS_CUTOFF}).")
    else:
        train_df = df_clean
        print(f"🚀 Production Mode: Training on FULL dataset ({len(train_df)} months).")
    
    print(f"✅ Data preparation complete. Training shape: {train_df.shape}")
    return train_df


if __name__ == "__main__":
    engine = get_engine()
    # Test run
    df = load_and_prep_data(engine)
    #print("\nSample Data:")
    #print(df.head())