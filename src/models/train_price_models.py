import joblib
import xgboost as xgb

from config.database import get_engine
from src.features.build_features import load_and_prep_data

from config import settings
from src.models.features import get_season_cols, get_price_features


def train_price_models(df):
    """
    Trains Price Models for all crops defined in settings.CROPS.
    Uses 'Difference' strategy: Target = Current_Price - Prev_Price
    """
    
    season_cols = get_season_cols(df.columns)

    for crop in settings.CROPS:
        print(f"\n🌽 Training Price Model for: {crop}")
        
        # Define Features & Target
        features = get_price_features(crop, season_cols, df.columns)
        target = f'{crop}_Diff'

        if target not in df.columns:
            raise ValueError(f"❌ Missing target column: {target}")
        
        X = df[features] # XGBoost depends on column order
        y = df[target]

        # Train Model
        model = xgb.XGBRegressor(**settings.XGB_PARAMS)
        model.fit(X, y)
        
        # Save Model
        save_path = settings.MODELS_DIR / f"model_{crop}.pkl"
        joblib.dump(model, save_path)

        print(f"💾 {crop} model saved to: {save_path}")


if __name__ == "__main__":
    engine = get_engine()

    # 1. Load the full dataset
    full_df = load_and_prep_data(engine)

    # 2. Apply Train/Test split logic (if TEST_MONTHS_CUTOFF > 0, we only train on the training set)
    if settings.TEST_MONTHS_CUTOFF > 0:
        train_df = full_df.iloc[:-settings.TEST_MONTHS_CUTOFF].copy()
        print(f"📉 Training Mode: Using first {len(train_df)} months (Holding back last {settings.TEST_MONTHS_CUTOFF}).")
    else:
        train_df = full_df.copy()
        print(f"🚀 Production Mode: Training on FULL dataset ({len(train_df)} months).")
    
    # 3. Train models only on the training subset
    train_price_models(train_df)