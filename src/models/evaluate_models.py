import pandas as pd
import numpy as np
import joblib
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, mean_absolute_percentage_error

from config import settings
from config.database import get_engine
from src.features.build_features import load_and_prep_data
from src.models.features import (
    get_season_cols,
    get_price_features,
    get_stress_features
)


def evaluate(engine):
    """Evaluates the performance of the trained models on the most recent data."""
    df = load_and_prep_data(engine)
    
    # Define Test Set (Last 12 Months)
    # Logic: If we are in Production mode (Cutoff=0), we fallback to 12 months for the report
    test_months = settings.TEST_MONTHS_CUTOFF or 12
    test_months = min(test_months, len(df))

    # if test_months == 0:
    #     print("⚠️  Production Mode detected (Cutoff=0). Using last 12 months for sanity check.")
    #     test_months = 12

    test_df = df.iloc[-test_months:].copy()

    if test_df.empty:
        raise ValueError("❌ Test dataset is empty.")
    
    season_cols = get_season_cols(df.columns)

    print(f"\n🔎 EVALUATION REPORT (Testing on last {test_months} months)")
    print("=" * 85)
    print(f"{'CROP':<15} | {'MAE (₦)':<12} | {'RMSE (₦)':<12} | {'MAPE (%)':<10} | {'R² Score':<10}")
    print("-" * 85)
    
    avg_mae = []
    avg_mape = []

    # --- 1. EVALUATE CROP PRICES ---
    for crop in settings.CROPS:
        model_path = settings.MODELS_DIR / f"model_{crop}.pkl"
        
        if not model_path.exists():
            print(f"⚠️ {crop}: Model not found at {model_path}")
            continue

        # Load Model
        model = joblib.load(model_path)
        features = get_price_features(crop, season_cols, df.columns)
        
        # Predict Difference
        X_test = test_df.reindex(columns=features)
        pred_diff = model.predict(X_test)
        
        # Reconstruct Price (Pred = Prev_Price + Pred_Diff)
        pred_price = test_df[f'{crop}_Lag1'] + pred_diff
        actual_price = test_df[crop]
        
        # 3. Calculate Metrics
        mae = mean_absolute_error(actual_price, pred_price)
        rmse = np.sqrt(mean_squared_error(actual_price, pred_price))
        r2 = r2_score(actual_price, pred_price)
        mape = mean_absolute_percentage_error(actual_price, pred_price) * 100  # Convert to percentage  
        
        avg_mae.append(mae)
        avg_mape.append(mape)

        print(f"{crop.replace('Price_', ''):<15} | {mae:,.0f}         | {rmse:,.0f}         | {mape:.2f}%     | {r2:.2f}")
    
    print("-" * 85)
    if avg_mae:
        print(f"🏆 Average Error across all crops: ₦{np.mean(avg_mae):,.0f} | Average MAPE: {np.mean(avg_mape):.2f}%")
    
    # --- 2. EVALUATE VEGETATION STRESS MODEL ---

    print(f"\n🌱 ENVIRONMENTAL EVALUATION REPORT (Last {test_months} months)")
    print("=" * 85)
    
    stress_model_path = settings.MODELS_DIR / "model_stress_ndvi.pkl"
    if stress_model_path.exists():
        stress_model = joblib.load(stress_model_path)
        
        # Features must match the training and inference pipeline exactly
        stress_features = get_stress_features(test_df.columns)
        
        pred_stress = stress_model.predict(test_df[stress_features])
        actual_stress = test_df[settings.STRESS_TARGET]
        
        stress_mae = mean_absolute_error(actual_stress, pred_stress)
        stress_rmse = np.sqrt(mean_squared_error(actual_stress, pred_stress))
        stress_r2 = r2_score(actual_stress, pred_stress)
        
        print(f"{'NDVI Anomaly':<15} | MAE: {stress_mae:.4f}  | RMSE: {stress_rmse:.4f}  | R²: {stress_r2:.2f}")
    else:
        print(f"⚠️ Stress Model not found at {stress_model_path}")
        
    print("=" * 85)
    print("\n✅ Full System Evaluation Complete.")
if __name__ == "__main__":
    engine = get_engine()
    evaluate(engine)