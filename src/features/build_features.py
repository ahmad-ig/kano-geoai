### FEATURE ENGINEERING

import pandas as pd
import numpy as np

from config import settings
from config.database import get_engine, get_processed_features
from src.data.load_training_data import load_training_data

#rom src.db.queries import get_processed_features

def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Engineer temporal, seasonal, and price-difference features.
    """

    print("Engineering training features...")

    df = df.copy()

    # 1. Set Date as index
    df = df.set_index('Date').sort_index()

    # 2. Validate monthly continuity
    expected_dates = pd.date_range(
        start=df.index.min(),
        end=df.index.max(),
        freq="MS",
    )

    if not df.index.equals(expected_dates):
        raise ValueError(
            "Dataset does not contain a continuous monthly date index."
        )
    
    # 3. Temporal Features
    df['Trend_Index'] = range(len(df))

    # 4. Seasonal Features
    df['Month'] = df.index.month

    for month in range(2, 13):
        df[f"Seas_{month}"] = (
            df["Month"] == month
        ).astype(int)

    df = df.drop(columns=['Month'])

    for col in settings.CROPS:

        if col in df.columns:
            df[f'{col}_Diff'] = df[col] - df[col].shift(1)
        else:
            print(f"Warning: Column {col} not found in dataset.")

    # 3. Remove rows with missing values (created by differencing)
    df_clean = df.dropna().copy()

    print(f"Feature engineering complete. Dataset shape: {df_clean.shape}")
    
    return df_clean


if __name__ == "__main__":

    raw_df = load_training_data()

    df = build_features(raw_df)

    print(df.head())
