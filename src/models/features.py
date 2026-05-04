### FEATURE SELECTION

def get_stress_features(columns):
    """Returns the list of features needed for the stress model."""
    stress_features = [
        'Rainfall_Anomaly_Lag1', 'Rainfall_Anomaly_Lag2',
        'NDMI_Anomaly_Lag1', 'NDMI_Anomaly_Lag2',
        'NDVI_Anomaly_Lag1'  # Auto-regressive term
    ]
    missing_features = [f for f in stress_features if f not in columns]
    if missing_features:
        raise ValueError(f"❌ Missing features for stress model: {missing_features}")
    
    return stress_features

def get_season_cols(columns):
    """Dynamically get seasonality columns (Seas_2, Seas_3, etc.)"""
    return [c for c in columns if c.startswith('Seas_')]

def get_price_features(crop, season_cols, columns):
    """Returns the list of features needed for a specific crop."""
    features = [
        f'{crop}_Lag1', f'{crop}_Lag2', 
        'NDVI_Anomaly_Lag1', 'NDVI_Anomaly_Lag2',
        'NDMI_Anomaly_Lag1', 'NDMI_Anomaly_Lag2',
        'Rainfall_Anomaly_Lag1', 'Rainfall_Anomaly_Lag2', 
        'Trend_Index'
    ]
    # Add Exchange Rate + season columns
    if 'Exchange_Rate_Lag1' in columns:
        features.extend(['Exchange_Rate_Lag1', 'Exchange_Rate_Lag2'])

    full_features = features + season_cols

    missing = [f for f in full_features if f not in columns]
    if missing:
        raise ValueError(f"❌ Missing features for {crop}: {missing}")

    return full_features