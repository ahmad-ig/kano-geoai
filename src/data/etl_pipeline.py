import pandas as pd
import numpy as np

from config import settings
from config.database import get_engine
from src.db.queries import get_env_data, get_price_data, get_processed_features

def process_environmental_data(engine):
    """
    Reads raw climate data from PostgreSQL, aggregates to monthly LGA level, 
    calculates Z-Score Anomalies, and then aggregates to State Level.
    """
    print("🌍 Processing Environmental Data...")
    
    # 1. Load Data from PostgreSQL
    env_df = get_env_data(engine)

    env_df['period_start'] = pd.to_datetime(env_df['period_start'])
    env_df['Month_Year'] = env_df['period_start'].dt.to_period('M')

    # 2. Aggregating to Monthly Level per LGA
    # Logic: Mean for Vegetation/Moisture, Sum for Rainfall
    monthly_env = env_df.groupby(['LGA_NAME', 'Month_Year']).agg({
        'NDVI': 'mean', 
        'NDMI': 'mean', 
        'Rainfall': 'sum'
    }).reset_index()

    # Convert Month_Year back to timestamp for extraction
    monthly_env['Date'] = monthly_env['Month_Year'].dt.to_timestamp()
    monthly_env['Month_Num'] = monthly_env['Date'].dt.month

    # 3. Calculate Long-Term Normals (Mean & Std per Month per LGA)
    stats = monthly_env.groupby(['LGA_NAME', 'Month_Num'])[['NDVI', 'NDMI', 'Rainfall']].agg(['mean', 'std']).reset_index()
    stats.columns = ['LGA_NAME', 'Month_Num', 'NDVI_Mean', 'NDVI_Std', 'NDMI_Mean', 'NDMI_Std', 'Rain_Mean', 'Rain_Std']

    # 4. Merge Normals back to calculate Anomalies
    merged_env = pd.merge(monthly_env, stats, on=['LGA_NAME', 'Month_Num'], how='left')

    # 5. Calculate Z-Scores (Anomaly = (Val - Mean) / Std)
    # fillna(0) handles cases where Std Dev is 0 (e.g., consistent 0 rainfall in dry season)
    merged_env['NDVI_Anomaly'] = ((merged_env['NDVI'] - merged_env['NDVI_Mean']) / merged_env['NDVI_Std'].replace(0, np.nan)).fillna(0)
    merged_env['NDMI_Anomaly'] = ((merged_env['NDMI'] - merged_env['NDMI_Mean']) / merged_env['NDMI_Std'].replace(0, np.nan)).fillna(0)
    merged_env['Rainfall_Anomaly'] = ((merged_env['Rainfall'] - merged_env['Rain_Mean']) / merged_env['Rain_Std'].replace(0, np.nan)).fillna(0)

    # 6. Aggregate to State Level (Mean of all LGAs)
    # We need one signal for the whole state to match the Market Price
    state_env = merged_env.groupby('Date')[['NDVI_Anomaly', 'NDMI_Anomaly', 'Rainfall_Anomaly']].mean().reset_index()
    
    return state_env

def process_price_data(engine):
    """
    Reads raw price data from PostgreSQL, filters for Wholesale at Kano Dawanau,
    extracts & inverts exchange rate, pivots crops to columns,
    and handles missing values via interpolation.
    """
    print("💰 Processing Price Data...")
    
    # 1. Load Data from PostgreSQL
    df = get_price_data(engine)

    # price_df = pd.read_csv(filepath) # Loads from backup CSV

    # 2. Date Formatting (Create Month_Year period)
    df['period_date'] = pd.to_datetime(df['period_date'])
    df['Month_Year'] = df['period_date'].dt.to_period('M')

    # 3. Filter for Target Market, Target Crops, and Wholesale
    target_crops_raw = list(settings.CROP_RENAME_MAP.keys())
    wholesale_df = df[
        (df['market'] == settings.TARGET_MARKET) & 
        (df['product'].isin(target_crops_raw)) &
        (df['price_type'] == 'Wholesale')
    ].copy()

    # 4. Pivot: Crops become columns
    price_wide = (
        wholesale_df
        .groupby(['Month_Year', 'product'])['value']
        .mean()
        .unstack()
        .reset_index()
    )

    # Clean up column names and rename using settings map
    price_wide.columns.name = None
    price_wide = price_wide.rename(columns=settings.CROP_RENAME_MAP)
    price_wide = price_wide.set_index('Month_Year')

    # Interpolate Missing Crop Prices
    cols_to_fix = list(settings.CROP_RENAME_MAP.values())
    price_wide[cols_to_fix] = price_wide[cols_to_fix].interpolate(method='linear', limit_direction='both')

    # 5. Extract, Invert, and Interpolate Macroeconomic features (Exchange Rate)
    # Grouping from the main df ensures we don't miss months where crops were missing
    exchange_rate_df = df.groupby('Month_Year')['exchange_rate'].mean()
    exchange_rate_df = (1 / exchange_rate_df).rename('Exchange_Rate')
    exchange_rate_df = exchange_rate_df.interpolate(method='linear', limit_direction='both')

    # 6. Join Prices and Exchange Rate
    # Using OUTER join prevents data shortening (keeps the full 96 months)
    dawanau_price_df = price_wide.join(exchange_rate_df, how='outer')

    # 7. Final Formatting: Convert Month_Year back to timestamp (Date) for merging with Env data
    dawanau_price_df = dawanau_price_df.reset_index()
    dawanau_price_df['Date'] = dawanau_price_df['Month_Year'].dt.to_timestamp()

    # Drop the period object as it's no longer needed
    dawanau_price_df = dawanau_price_df.drop(columns=['Month_Year'])

    return dawanau_price_df

def merge_and_engineer_features(state_env, price_wide):
    """
    Merges env and price data, ensures time continuity (filling missing months),
    and generates Lag features.
    """
    print("⚙️ Merging and Engineering Features...")

    # 1. Merge on Date
    full_df = pd.merge(price_wide, state_env, on='Date', how='inner')
    full_df = full_df.set_index('Date').sort_index()

    # 2. Handle Missing Months (Time Continuity)
    # This inserts rows for missing months (e.g., if 2018-07 is missing) filled with NaNs
    full_df = full_df.asfreq('MS')

    # 3. Fill the new NaNs with Linear Interpolation
    numeric_cols = full_df.select_dtypes(include=['number']).columns
    full_df[numeric_cols] = full_df[numeric_cols].interpolate(method='linear', limit_direction='both')

    # Reset Index to get Date back as column
    full_df = full_df.reset_index()
    full_df['Month_Year'] = full_df['Date'].dt.to_period('M')

    # 4. Generate Lags including Exchange_Rate (The "Time Travel" Features)
    # We combine the crop columns (from settings) with the environmental columns
    lag_features = settings.CROPS + ['NDVI_Anomaly', 'NDMI_Anomaly', 'Rainfall_Anomaly']
    if 'Exchange_Rate' in full_df.columns:
        lag_features.append('Exchange_Rate')

    for col in lag_features:
        if col in full_df.columns:
            full_df[f'{col}_Lag1'] = full_df[col].shift(1)
            full_df[f'{col}_Lag2'] = full_df[col].shift(2)

    # 5. Drop rows with NaNs (The first 2 months will be empty due to lags)
    final_df = full_df.dropna()
    
    return final_df

if __name__ == "__main__":
    try:
        engine = get_engine()  # Initialize the database engine

        # 1. Process Environment (from DB)
        env_data = process_environmental_data(engine)
        
        # 2. Process Prices (from DB)
        price_data = process_price_data(engine)
        
        # 3. Merge & Feature Engineering
        final_dataset = merge_and_engineer_features(env_data, price_data)
        
        # Drop the Period object before saving to DB
        if 'Month_Year' in final_dataset.columns:
            final_dataset = final_dataset.drop(columns=['Month_Year'])

        # 4. Save to Database
        print("💾 Saving processed features to PostgreSQL...")
        final_dataset.to_sql(
            name='processed_features',
            con=engine,
            if_exists='replace',
            index = False
        )
        print("✅ Successfully saved to database table: 'processed_features'")

        # 5. CSV backup
        final_dataset.to_csv(settings.PROCESSED_DATA_PATH, index=False)
        print(f"\n✅ ETL Complete! Backup saved to: {settings.PROCESSED_DATA_PATH}")
        print(f"   Final Shape: {final_dataset.shape}")

    except Exception as e:
        print(f"\n❌ ETL Pipeline Failed: {e}")
        
