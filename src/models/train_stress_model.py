import joblib
import xgboost as xgb
import numpy as np

from config import settings
from config.database import get_engine
from src.features.build_features import load_and_prep_data
from src.models.features import get_stress_features

def train_stress_model(df):
    """
    Trains the NDVI Stress Forecast Model using XGBoost.
    """
    print(f"\n🌱 Training Stress Model (Target: {settings.STRESS_TARGET})...")
    
    if df.empty:
        raise ValueError("❌ Training dataset is empty.")

    if settings.STRESS_TARGET not in df.columns:
        raise ValueError(f"❌ Missing target column: {settings.STRESS_TARGET}")
    
    # Ensure model directory exists
    settings.MODELS_DIR.mkdir(parents=True, exist_ok=True)

    # Define Features for Stress Prediction
    stress_features = get_stress_features(df.columns)

    X = df[stress_features]
    y = df[settings.STRESS_TARGET]

    # model training
    stress_model = xgb.XGBRegressor(**settings.XGB_PARAMS)
    stress_model.fit(X, y)

    # save model
    save_path = settings.MODELS_DIR / "model_stress_ndvi.pkl"
    joblib.dump(stress_model, save_path)
    
    print(f"💾 Stress model saved to: {save_path}")

if __name__ == "__main__":
    # Test run (requires data_loader to work first)
    engine = get_engine()
    df = load_and_prep_data(engine)
    train_stress_model(df)