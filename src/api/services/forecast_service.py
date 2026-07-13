"""
Wraps src/inference/predict.py so the API route stays thin.
This mirrors exactly what the Streamlit get_predictions() function did,
minus the st.cache_data/st.error bits (handled by main.py / cache.py instead).
"""

from typing import Optional

import pandas as pd

from src.inference.predict import (
    load_latest_context,
    prepare_next_month_features,
    predict_stress,
    predict_prices,
)


def run_forecast(engine, manual_overrides: Optional[dict] = None) -> dict:
    last_row, last_date, all_cols = load_latest_context(engine)

    if manual_overrides:
        last_row = last_row.copy()
        for col, val in manual_overrides.items():
            if col in last_row:
                last_row[col] = val
            # Silently ignore unknown override keys rather than raising —
            # keeps the endpoint tolerant of frontend/back-end drift.

    input_df, season_cols = prepare_next_month_features(last_row, last_date, all_cols)

    stress_val = predict_stress(input_df)
    price_preds = predict_prices(input_df, last_row, season_cols)
    next_date = last_date + pd.DateOffset(months=1)

    return {
        "last_row": last_row,
        "last_date": last_date,
        "next_date": next_date,
        "stress": stress_val,
        "prices": price_preds,
    }


def classify_stress(stress_val: float) -> tuple[str, str]:
    """Same thresholds used in the Streamlit dashboard and predict.py CLI report."""
    if stress_val is None:
        return "UNKNOWN", "gray"
    if stress_val < -1.0:
        return "DROUGHT RISK", "red"
    if stress_val < -0.5:
        return "MILD STRESS", "orange"
    return "NORMAL", "green"
