import pandas as pd
import geopandas as gpd

from config.database import get_engine


# GEO DATA (PostGIS)
def get_lga_map_data(engine):
    """Fetch LGA boundaries for Kano as a GeoDataFrame (PostGIS-native)."""

    query = """
    SELECT name_2 AS lga_name, geom
    FROM lga_map_data
    WHERE name_1 = 'Kano'
    """

    try:
        gdf = gpd.read_postgis(query, con=engine, geom_col='geom')
    except Exception as e:
        raise RuntimeError(f"❌ Error loading LGA map data: {e}")

    if gdf.empty:
        raise ValueError("❌ No LGA data found for Kano.")

    # Ensure CRS is WGS84 (required for Plotly)
    if gdf.crs is None:
        gdf.set_crs(epsg=4326, inplace=True)
    else:
        gdf = gdf.to_crs(epsg=4326)

    return gdf

# RAW ENV DATA
def get_env_data(engine):
    """Fetch raw environmental data."""
    query = "SELECT * FROM raw_env_data"

    try:
        df = pd.read_sql(query, con=engine)
    except Exception as e:
        raise RuntimeError(f"❌ Error loading env data: {e}")

    if df.empty:
        raise ValueError("❌ 'raw_env_data' table is empty.")

    return df
    
def get_price_data(engine):
    """Fetch raw price data."""
    query = "SELECT * FROM raw_fewsnet_prices"

    try:
        df = pd.read_sql(query, con=engine)
    except Exception as e:
        raise RuntimeError(f"❌ Error loading price data: {e}")

    if df.empty:
        raise ValueError("❌ 'raw_fewsnet_prices' table is empty.")

    return df

# PROCESSED FEATURES
def get_processed_features(engine):
    """Fetch processed ML features."""
    query = "SELECT * FROM processed_features"

    try:
        df = pd.read_sql(query, con=engine)
    except Exception as e:
        raise RuntimeError(f"❌ Error loading processed features: {e}")

    if df.empty:
        raise ValueError("❌ 'processed_features' table is empty.")

    return df


# SAVE PREDICTIONS
def save_predictions(engine, df):
    """Save model predictions to database."""
    try:
        df.to_sql(
            name="predictions",
            con=engine,
            if_exists="append",
            index=False
        )
    except Exception as e:
        raise RuntimeError(f"❌ Error saving predictions: {e}")


# TEST RUN
if __name__ == "__main__":
    engine = get_engine()

    print("🔍 Testing DB module...\n")

    try:
        gdf = get_lga_map_data(engine)
        print("✅ LGA Map Data Loaded")
        print(gdf.head())
    except Exception as e:
        print(e)