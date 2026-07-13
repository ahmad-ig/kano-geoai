"""
Helpers for /api/historical and /api/map-data.
"""

import json
import math
from typing import Callable

import pandas as pd


def dataframe_tail_to_records(df: pd.DataFrame, months: int) -> list[dict]:
    """
    Mirrors `history_df.tail(24)` from the Streamlit chart, but returns
    JSON-safe records (ISO date strings, NaN -> None) for the API response.
    """
    tail = df.tail(months).copy()

    if "Date" not in tail.columns:
        # get_processed_features() may return Date as the index (as it does
        # after predict.py's load_latest_context sets it) — normalize either way.
        tail = tail.reset_index()

    tail["Date"] = pd.to_datetime(tail["Date"]).dt.strftime("%Y-%m-%d")

    records = tail.to_dict(orient="records")

    # Replace NaN/inf with None so it serializes cleanly as JSON.
    for record in records:
        for key, value in record.items():
            if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
                record[key] = None

    return records


def load_lga_map_data(engine, get_lga_map_data_fn: Callable):
    """
    Mirrors Streamlit's load_lga_map_data(): fetches LGA geometry + the most
    recent NDVI/Rainfall reading per LGA, and converts geometry to GeoJSON.
    """
    gdf = get_lga_map_data_fn(engine)
    kano_geojson = json.loads(gdf.to_json())

    query = """
    SELECT "LGA_NAME", "NDVI", "Rainfall"
    FROM raw_env_data
    WHERE period_start = (
        SELECT period_start FROM raw_env_data ORDER BY period_start DESC LIMIT 1
    )
    """
    lga_df = pd.read_sql(query, con=engine)

    if not lga_df.empty:
        lga_df["LGA_NAME"] = lga_df["LGA_NAME"].str.strip()

    return kano_geojson, lga_df
