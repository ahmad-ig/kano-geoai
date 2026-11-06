import pandas as pd

from config import settings

def load_training_data() -> pd.DataFrame:
    """
    Loads the training dataset from a Parquet snapshot.
    This is used for model training and evaluation.
    """
    print("Loading training data from Parquet snapshot...")
    
    # Load from Parquet snapshot for training
    snapshot_path = settings.SNAPSHOT_PROCESSED_DATA_PATH
    
    df = pd.read_parquet(snapshot_path)

    if df.empty:
        raise ValueError("The training dataset is empty.")

    if "Date" not in df.columns:
        raise ValueError("The training dataset has no Date column.")

    df["Date"] = pd.to_datetime(df["Date"])

    df = df.sort_values("Date").reset_index(drop=True)

    if df["Date"].duplicated().any():
        raise ValueError("Duplicate dates detected in training data.")

    print(f"Dataset loaded successfully: {df.shape}")
    
    
    return df

#load_training_data()