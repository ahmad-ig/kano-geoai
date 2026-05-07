import pandas as pd
import joblib


from config import settings
from config.database import get_engine
from src.db.queries import get_processed_features
from src.models.features import (
    get_stress_features,
    get_price_features,
)


def load_latest_context(engine):
    """Loads the full dataset from PostgreSQL and applies the global cutoff."""
    print("🔄 Loading latest data context from Database...")

    if settings.DATA_SOURCE == "csv":
        print("📂 Loading processed features from CSV (for Streamlit deployment)...")
        df = pd.read_csv(settings.PROCESSED_DATA_PATH, parse_dates=['Date'])
    else:
        df = get_processed_features(engine)

    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date').set_index('Date')
    
    # --- THE TIME MACHINE (Synchronized with settings.py) ---
    if hasattr(settings, 'TEST_MONTHS_CUTOFF') and settings.TEST_MONTHS_CUTOFF > 0:
        print(f"⏪ Time Machine Active: Rolling back {settings.TEST_MONTHS_CUTOFF} months to match training validation state.")
        # Chop off the test months so the "last row" is exactly where training ended
        df = df.iloc[:-settings.TEST_MONTHS_CUTOFF]
        
        if df.empty:
            raise ValueError(f"❌ Error: Rolling back {settings.TEST_MONTHS_CUTOFF} months left the dataset empty!")

    # Feature Engineering (Must match training logic)
    df['Trend_Index'] = range(len(df))
    df['Month'] = df.index.month
    df = pd.get_dummies(df, columns=['Month'], prefix='Seas', drop_first=True)
    
    # Get the very last row (The "Current" situation right before the cutoff)
    last_row = df.iloc[-1]
    last_date = df.index[-1]
    
    return last_row, last_date, df.columns

def prepare_next_month_features(last_row, last_date, all_columns):
    """
    Constructs the feature vector for the NEXT month.
    Logic: Today's "Value" becomes Tomorrow's "Lag1".
    """
    # 1. Determine Next Month
    next_date = last_date + pd.DateOffset(months=1)
    next_month_num = next_date.month
    
    print(f"📅 Predicting for: {next_date.strftime('%B %Y')}")
    print(f"   (Based on data ending: {last_date.strftime('%Y-%m-%d')})")

    features = {}

    # --- Lag Features (The Time Travel Logic) ---
    # Environmental Lags
    features['NDVI_Anomaly_Lag1'] = last_row['NDVI_Anomaly']
    features['NDVI_Anomaly_Lag2'] = last_row.get('NDVI_Anomaly_Lag1', last_row['NDVI_Anomaly']) 

    features['NDMI_Anomaly_Lag1'] = last_row['NDMI_Anomaly']
    features['NDMI_Anomaly_Lag2'] = last_row.get('NDMI_Anomaly_Lag1', last_row['NDMI_Anomaly'])

    features['Rainfall_Anomaly_Lag1'] = last_row['Rainfall_Anomaly']
    features['Rainfall_Anomaly_Lag2'] = last_row.get('Rainfall_Anomaly_Lag1', last_row['Rainfall_Anomaly'])
    
    # Macroeconomic Lag (Exchange Rate)
    if 'Exchange_Rate' in last_row:
        features['Exchange_Rate_Lag1'] = last_row['Exchange_Rate']
        features['Exchange_Rate_Lag2'] = last_row.get('Exchange_Rate_Lag1', last_row['Exchange_Rate'])
    
    # Crop Lags
    for crop in settings.CROPS:
        features[f'{crop}_Lag1'] = last_row[crop]
        features[f'{crop}_Lag2'] = last_row.get(f'{crop}_Lag1', last_row[crop])

    # --- Temporal Features ---
    features['Trend_Index'] = last_row['Trend_Index'] + 1
    
    # Seasonality
    season_cols = [c for c in all_columns if c.startswith('Seas_')]
    for col in season_cols:
        features[col] = 0 # Reset all to 0
        
    # Set the bit for the next month
    target_season_col = f'Seas_{next_month_num}'
    if target_season_col in features:
        features[target_season_col] = 1

    return pd.DataFrame([features]), season_cols


def predict_stress(input_df):
    """Predicts NDVI anomaly (Vegetation Health)."""
    model_path = settings.MODELS_DIR / "model_stress_ndvi.pkl"

    if not model_path.exists():
        print(f"⚠️ Stress Model not found at {model_path}")
        return None

    model = joblib.load(model_path)
    
    # Exactly what the stress model was trained on
    cols = get_stress_features(input_df.columns)
    
    # Ensure dataframe columns are in the correct order
    X = input_df.reindex(columns=cols)

    return model.predict(X)[0]


def predict_prices(input_df, last_row, season_cols):
    """Predicts the price change for all crops and calculates the new absolute price."""
    predictions = {}
    
    for crop in settings.CROPS:
        model_path = settings.MODELS_DIR / f"model_{crop}.pkl"

        if not model_path.exists():
            print(f"⚠️ {crop} Model not found at {model_path}")
            continue
            
        model = joblib.load(model_path)

        # Exact Feature Order (Must match train_prices.py)
        feature_order = get_price_features(crop, season_cols, input_df.columns)
        
        # Predict Change
        X = input_df.reindex(columns=feature_order)
        pred_diff = model.predict(X)[0]

        # Reconstruct Price
        current_price = last_row[crop]
        predicted_price = current_price + pred_diff
        
        predictions[crop] = {
            'pred': predicted_price,
            'change': pred_diff,
            'current': current_price
        }
        
    return predictions


def run_forecast(engine):
    last_row, last_date, all_cols = load_latest_context(engine)
    input_df, season_cols = prepare_next_month_features(last_row, last_date, all_cols)

    stress_val = predict_stress(input_df)
    price_preds = predict_prices(input_df, last_row, season_cols)

    return {
        "date": last_date,
        "stress": stress_val,
        "prices": price_preds
    }


if __name__ == "__main__":

    engine = get_engine()

    print("\n🚀 KANO GEO-AI SYSTEM: FORECAST ENGINE")
    print("=" * 45)
    
    try:
        # 1. Load Context (Automatically respects settings.TEST_MONTHS_CUTOFF)
        last_row, last_date, all_cols = load_latest_context(engine)
        
        # 2. Build Future Features
        input_df, season_cols = prepare_next_month_features(last_row, last_date, all_cols)
        
        # 3. Predict
        stress_val = predict_stress(input_df)
        price_preds = predict_prices(input_df, last_row, season_cols)
        
        # 4. Report
        print("\n" + "="*45)
        next_month = last_date.month + 1
        next_year = last_date.year
        if next_month > 12:
            next_month = 1
            next_year += 1
            
        print(f"📊 REPORT FOR: {next_month}/{next_year}")
        print("="*45)
        
        if stress_val is not None:
            status = "🟢 NORMAL"
            if stress_val < -1.0: status = "🔴 DROUGHT RISK"
            elif stress_val < -0.5: status = "🟡 MILD STRESS"
            print(f"🌱 VEGETATION INDEX: {stress_val:.3f} ({status})")
        
        print("\n💰 PRICE FORECAST (Kano Dawanau)")
        print(f"{'CROP':<10} | {'CURRENT':<12} | {'FORECAST':<12} | {'TREND'}")
        print("-" * 55)
        
        for crop, res in price_preds.items():
            name = crop.replace('Price_', '')
            arrow = "🔺" if res['change'] > 0 else "🔻"
            print(f"{name:<10} | ₦{res['current']:<10,.0f} | ₦{res['pred']:<10,.0f} | {arrow} {res['change']:+,.0f}")
            
        print("\n✅ Forecast Generated.")

    except Exception as e:
        print(f"\n❌ Error: {e}")