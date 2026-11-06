import time
import pandas as pd

from config import settings
from config.database import get_engine


def fetch_prices(engine):
    """
    Download FEWS NET price data and store it in PostgreSQL.
    """
    print("Connecting to FEWS NET Data Explorer API...")

    try:
        # 1. Download data using the URL from settings
        # pandas will read a csv file direcltly from the web URL
        print(f"Downloading data... (This might take a moment depending on the dataset size)")

        start_time = time.time()
        # Read the CSV directly from the API endpoint
        df = pd.read_csv(
            settings.FEWSNET_API_URL, 
            low_memory=False
        )

        if df.empty:
            raise ValueError("Downloaded data is empty. Please check the API endpoint or your internet connection.")
        
        print(f"Downloaded {len(df)} rows and {len(df.columns)} columns in {time.time() - start_time:.1f} seconds.")

        # 2. Save a local CSV backup
        df.to_csv(
            settings.RAW_PRICE_DATA_PATH, 
            index=False
        )
        print(f"CSV backup saved to {settings.RAW_PRICE_DATA_PATH}")

       
        # 3. Store the downloaded data in PostgreSQL
        print("Saving price data to PostgreSQL...")

        with engine.begin() as connection:
            df.to_sql(
                name='raw_fewsnet_prices',
                con=connection,
                if_exists='replace',
                index=False
            )

        print("Successfully stored FEWS NET Price Data in PostgreSQL.")

    except Exception as exc:
        print(f"Price ingestion failed: {exc}")
      

if __name__ == "__main__":
    engine = get_engine()

    try:
        fetch_prices(engine)
    finally:
        engine.dispose()