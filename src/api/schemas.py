from datetime import date
from typing import Any, Dict, List

from pydantic import BaseModel


class CropInfo(BaseModel):
    code: str            # e.g. "Price_Maize"
    label: str            # e.g. "Maize"


class StressForecast(BaseModel):
    value: float
    status: str            # "NORMAL" | "MILD STRESS" | "DROUGHT RISK"
    severity: str           # "green" | "orange" | "red" — for frontend styling


class CropForecast(BaseModel):
    crop: str
    label: str
    current: float
    predicted: float
    change: float
    change_pct: float


class CurrentInputs(BaseModel):
    """Latest raw readings, used by the frontend to prefill scenario-simulator inputs."""
    exchange_rate: float | None = None
    ndvi_anomaly: float
    ndmi_anomaly: float
    rainfall_anomaly: float


class ForecastResponse(BaseModel):
    current_date: date
    forecast_date: date
    stress: StressForecast
    prices: List[CropForecast]
    current_inputs: CurrentInputs


class HistoricalResponse(BaseModel):
    months: int
    # Each record is one month's row: {"Date": "...", "Price_Maize": ..., "NDVI_Anomaly": ..., ...}
    records: List[Dict[str, Any]]


class LgaDataPoint(BaseModel):
    lga_name: str
    ndvi: float
    rainfall: float


class MapDataResponse(BaseModel):
    geojson: Dict[str, Any]
    lga_data: List[LgaDataPoint]
