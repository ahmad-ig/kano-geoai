import pandas as pd

from config import paths
from config.database import get_engine
from src.db.queries import get_processed_features, get_lga_map_data


def export_data():
    engine = get_engine()
    df = get_processed_features(engine)
    df.to_csv(paths.PROCESSED_DATA_PATH, index=False)

    # Export latest LGA env data
    query ="""
    SELECT "LGA_NAME", "NDVI", "NDMI", "Rainfall", "period_start"
    FROM raw_env_data
    WHERE period_start = (
        SELECT period_start FROM raw_env_data ORDER BY period_start DESC LIMIT 1)
    """
    lga_df = pd.read_sql(query, con=engine)
    lga_df.to_csv(paths.PROCESSED_ENV_DATA_PATH, index=False)

    # Export LGA map data
    gdf = get_lga_map_data(engine)
    gdf.to_file(paths.PROCESSED_LGA_MAP_PATH, driver="GeoJSON")

    print("✅ Static data exported for Streamlit deployment.")

if __name__ == "__main__":
    export_data()