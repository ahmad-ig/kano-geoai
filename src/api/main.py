"""
Kano GeoAI Food Security API
=============================
FastAPI backend that wraps the existing inference pipeline (src/inference/predict.py)
and DB query layer (src/db/queries.py) so a React frontend can consume it over HTTP.

This file is meant to live at: src/api/main.py  (same level as src/inference, src/db)
so that the existing "sys.path" project-root imports keep working unchanged.

Run locally:
    uvicorn src.api.main:app --reload --port 8000
"""

import sys
import os

# Match the same project-root import trick used by predict.py / the Streamlit app.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from datetime import date
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from config.database import get_engine

from src.inference.predict import (
    load_latest_context,
    prepare_next_month_features,
    predict_stress,
    predict_prices,
)
from src.db.queries import get_processed_features, get_lga_map_data

from src.api.schemas import (
    ForecastResponse,
    StressForecast,
    CropForecast,
    CurrentInputs,
    HistoricalResponse,
    MapDataResponse,
    LgaDataPoint,
    CropInfo,
)
from src.api.services.cache import TTLCache
from src.api.services import data_service, forecast_service

# --------------------------------------------------------------------------
# App setup
# ------------------------------------------------------------------

app = FastAPI(
    title="Kano GeoAI Food Security API",
    description="Serves crop price forecasts, vegetation stress predictions, "
    "historical trends, and LGA map data for the Kano GeoAI dashboard.",
    version="1.0.0",
)

# Allow the React dev server (and any origin you configure) to call this API.
# In production, replace "*" with your actual frontend origin(s).
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# A single shared engine + a small TTL cache mirroring the @st.cache_resource /
# @st.cache_data(ttl=3600) behaviour from the Streamlit app.
_engine = get_engine()
_cache = TTLCache(ttl_seconds=3600)


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------

@app.get("/api/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/crops", response_model=list[CropInfo])
def list_crops():
    """Returns the crop codes + display names for populating a dropdown."""
    return [
        CropInfo(code=crop, label=crop.replace("Price_", ""))
        for crop in settings.CROPS
    ]


@app.get("/api/forecast", response_model=ForecastResponse)
def get_forecast(
    exchange_rate: Optional[float] = Query(None, description="Scenario override: NGN/USD"),
    ndvi_anomaly: Optional[float] = Query(None, description="Scenario override: NDVI anomaly"),
    ndmi_anomaly: Optional[float] = Query(None, description="Scenario override: NDMI anomaly"),
    rainfall_anomaly: Optional[float] = Query(None, description="Scenario override: Rainfall anomaly"),
    crop: Optional[str] = Query(None, description="Crop code to override current price for, e.g. Price_Maize"),
    crop_price: Optional[float] = Query(None, description="Scenario override: current price for `crop`"),
):
    """
    Predicts next-month vegetation stress (NDVI) and crop prices.
    Optional query params let the frontend run "what-if" scenarios,
    equivalent to the Streamlit sidebar's Scenario Simulator.
    """
    overrides = {}
    if exchange_rate is not None:
        overrides["Exchange_Rate"] = exchange_rate
    if ndvi_anomaly is not None:
        overrides["NDVI_Anomaly"] = ndvi_anomaly
    if ndmi_anomaly is not None:
        overrides["NDMI_Anomaly"] = ndmi_anomaly
    if rainfall_anomaly is not None:
        overrides["Rainfall_Anomaly"] = rainfall_anomaly
    if crop is not None and crop_price is not None:
        overrides[crop] = crop_price

    try:
        result = forecast_service.run_forecast(_engine, overrides or None)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forecast failed: {e}")

    stress_val = result["stress"]
    status_label, status_color = forecast_service.classify_stress(stress_val)

    prices = [
        CropForecast(
            crop=c,
            label=c.replace("Price_", ""),
            current=v["current"],
            predicted=v["pred"],
            change=v["change"],
            change_pct=(v["change"] / v["current"] * 100.0) if v["current"] else 0.0,
        )
        for c, v in result["prices"].items()
    ]

    last_row = result["last_row"]

    return ForecastResponse(
        current_date=result["last_date"].date(),
        forecast_date=result["next_date"].date(),
        stress=StressForecast(value=stress_val, status=status_label, severity=status_color),
        prices=prices,
        current_inputs=CurrentInputs(
            exchange_rate=last_row.get("Exchange_Rate"),
            ndvi_anomaly=last_row["NDVI_Anomaly"],
            ndmi_anomaly=last_row["NDMI_Anomaly"],
            rainfall_anomaly=last_row["Rainfall_Anomaly"],
        ),
    )


@app.get("/api/historical", response_model=HistoricalResponse)
def get_historical(months: int = Query(24, ge=1, le=240, description="How many most recent months to return")):
    """Returns the last N months of raw feature data (prices, NDVI/NDMI/rainfall anomalies, exchange rate)."""
    try:
        df = _cache.get_or_set("historical_features", lambda: get_processed_features(_engine))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load historical data: {e}")

    records = data_service.dataframe_tail_to_records(df, months)
    return HistoricalResponse(months=len(records), records=records)


@app.get("/api/map-data", response_model=MapDataResponse)
def get_map_data():
    """Returns LGA boundary geojson plus the latest NDVI/Rainfall reading per LGA."""
    try:
        geojson, lga_df = _cache.get_or_set(
            "map_data", lambda: data_service.load_lga_map_data(_engine, get_lga_map_data)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load map data: {e}")

    points = [
        LgaDataPoint(lga_name=row["LGA_NAME"], ndvi=row["NDVI"], rainfall=row["Rainfall"])
        for _, row in lga_df.iterrows()
    ]
    return MapDataResponse(geojson=geojson, lga_data=points)
