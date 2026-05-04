import time
import pandas as pd

from config import settings
from config.database import get_engine


def fetch_prices(engine):
    """
    Fetches raw market price data directly from the FEWS NET API, 
    saves a local backup, and stores it in the PostgreSQL database.
    """
    print("🌐 Connecting to FEWS NET Data Explorer API...")

    try:
        # 1. Download data using the URL from settings
        # pandas will read a csv file direcltly from the web URL
        print(f"📥 Downloading data... (This might take a moment depending on the dataset size)")

        start_time = time.time()
        # Read the CSV directly from the API endpoint
        df = pd.read_csv(settings.FEWSNET_API_URL, low_memory=False)
        print(f"✅ Downloaded {len(df)} rows and {len(df.columns)} columns in {time.time() - start_time:.1f} seconds.")

        # 2. Save a backup
        df.to_csv(settings.RAW_PRICE_PATH, index=False)
        print(f"📁 Local backup saved to {settings.RAW_PRICE_PATH}")

        # 3. Save to PostgreSQL
        print("💾 Saving data to PostgreSQL database...")
        df.to_sql(
            name='raw_fewsnet_prices',
            con=engine,
            if_exists='replace',
            index=False
        )

        print("✅ SUCCESS! FEWS NET Price Data is stored in the database.")

    except Exception as e:
        print(f"❌ An error occurred: {e}")
      

if __name__ == "__main__":
    engine = get_engine()  # Initialize the database engine
    fetch_prices(engine)