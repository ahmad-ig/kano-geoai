import sys
import os
import json
import pandas as pd
import numpy as np
import math
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

# Import your existing modules
from config import settings
from config.database import get_engine
from src.inference.predict import predict_stress, predict_prices, prepare_next_month_features, load_latest_context
from src.db.queries import get_processed_features, get_lga_map_data

# 1. Initialize FastAPI
app = FastAPI(title="Kano GeoAI API")

# 2. Configure CORS (Crucial for React to talk to Python)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"], # Standard React/Vite ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = get_engine()

def safe_float(val):
    """Converts NaN/Inf to None so JSON doesn't crash."""
    if val is None or math.isnan(float(val)) or math.isinf(float(val)):
        return None
    return float(val)

@app.get("/api/dashboard")
async def get_dashboard_data(
    crop: str = Query(..., description="The crop to analyze (e.g., Maize)"),
    sim: bool = Query(False, description="Whether simulation mode is active"),
    current_price: float = Query(None),
    ndvi_anomaly: float = Query(None),
    ndmi_anomaly: float = Query(None),
    rainfall_anomaly: float = Query(None)
):
    """
    Runs the inference pipeline and returns all data needed for the React dashboard.
    """
    try:
        selected_crop_col = f"Price_{crop}"
        
        # --- 1. RUN PREDICTIONS ---
        last_row, last_date, all_cols = load_latest_context(engine)
        
        # --- APPLY SIMULATION OVERRIDES ---
        if sim:
            if current_price is not None: last_row[selected_crop_col] = current_price
            if ndvi_anomaly is not None: last_row['NDVI_Anomaly'] = ndvi_anomaly
            if ndmi_anomaly is not None: last_row['NDMI_Anomaly'] = ndmi_anomaly
            if rainfall_anomaly is not None: last_row['Rainfall_Anomaly'] = rainfall_anomaly
            
        input_df, season_cols = prepare_next_month_features(last_row, last_date, all_cols)
        stress_val = safe_float(predict_stress(input_df))
        price_preds = predict_prices(input_df, last_row, season_cols)
        
        # Extract specific crop prediction
        crop_pred_data = price_preds.get(selected_crop_col, {"current": 0, "pred": 0, "change": 0})

        # --- 2. GET MAP DATA ---
        gdf = get_lga_map_data(engine)
        kano_geojson = json.loads(gdf.to_json())
        
        query = """
        SELECT "LGA_NAME", "NDVI", "Rainfall"
        FROM raw_env_data
        WHERE period_start = (SELECT period_start FROM raw_env_data ORDER BY period_start DESC LIMIT 1)
        """
        lga_df = pd.read_sql(query, con=engine)
        if not lga_df.empty:
            lga_df['LGA_NAME'] = lga_df['LGA_NAME'].str.strip()

        # --- 3. GET HISTORICAL DATA (Last 24 Months) ---
        history_df = get_processed_features(engine)
        history_df['Date'] = pd.to_datetime(history_df['Date'])
        history_df = history_df.sort_values('Date').tail(24)

        # --- 4. FORMAT FOR REACT (JSON Serialization) ---
        # React's Plotly component expects simple arrays for x and y axes
        return {
            "stress_val": safe_float(stress_val),
            "price_preds": {
                "current": safe_float(crop_pred_data.get('current', 0)),
                "pred": safe_float(crop_pred_data.get('pred', 0)),
                "change": safe_float(crop_pred_data.get('change', 0))
            },
            "kano_geojson": kano_geojson,
            "map_data": {
                "lga_names": lga_df['LGA_NAME'].tolist() if not lga_df.empty else [],
                # Replace Pandas NaNs with None for JSON compatibility
                "ndvi_values": lga_df['NDVI'].replace({np.nan: None}).tolist() if not lga_df.empty else [],
                "rainfall_values": lga_df['Rainfall'].replace({np.nan: None}).tolist() if not lga_df.empty else []
            },
            "history_data": {
                "dates": history_df['Date'].dt.strftime('%Y-%m-%d').tolist(),
                # Replace Pandas NaNs with None
                "prices": history_df[selected_crop_col].replace({np.nan: None}).tolist() if selected_crop_col in history_df else []
            }
        }
        
    except Exception as e:
        return {"error": str(e)}