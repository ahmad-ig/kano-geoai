import pandas as pd
from datetime import datetime
from calendar import monthrange
import ee

from config import settings
from config.database import get_engine

def fetch_satellite_data(engine):
    print("🌍 Initializing Google Earth Engine...")

    try:
        # Project ID from settings
        ee.Initialize(project=settings.GEE_PROJECT_ID)
    except Exception as e:
        print("⚠️ GEE not initialized. Authenticating...")
        ee.Authenticate()
        ee.Initialize(project=settings.GEE_PROJECT_ID)

    # --- 1. DEFINITIONS ---
    print("📍 Defining Region of Interest (Kano State)...")
    # FAO GAUL Dataset - Level 2 = LGAs
    gaul = ee.FeatureCollection("projects/geoai-final-year-project/assets/gadm41_NGA_2")
    kano_lgas = gaul.filter(ee.Filter.eq('NAME_1', 'Kano'))

    # Time Range (From 2017 to Current Month)
    start_date = '2017-01-01'
    end_date = datetime.now().strftime('%Y-%m-%d')
    print(f"⏳ Time Range: {start_date} to {end_date}")

    # --- 2. THE STABLE CROP MASK OF ACTIVE AGRICULTURAL LANDS ---
    print("🌾 Calculating Stable Crop Mask (Dynamic World)...")
    # Load Dynamic World dataset for the whole period
    dw = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")\
            .filterDate('2017-01-01', '2026-12-31')\
            .filterBounds(kano_lgas)
    
    # Calculate the MODE (most frequent label) for every pixel
    # Label 4 = Crops. Creating a binary mask (1=Crop, 0=Non-Crop)
    crop_mask = dw.select('label').mode().eq(4).clip(kano_lgas)

    # --- 3. HELPER FUNCTIONS ---
    def mask_s2_clouds_and_filter(image):
        # Using SCL (Scene Classification Layer) as per the GEE script
        # 4 = Vegetation, 5 = Bare Soils. We keep both.
        scl = image.select('SCL')
        mask = scl.eq(4).Or(scl.eq(5))
        return image.updateMask(mask)

    def add_indices(image):
        ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
        ndmi = image.normalizedDifference(['B8', 'B11']).rename('NDMI')
        return image.addBands([ndvi, ndmi])

    # --- 4. DATA COLLECTIONS ---
    print("Setting up Sentinel-2 & CHIRPS Collections...")
    s2 = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
          .filterDate(start_date, end_date)
          .filterBounds(kano_lgas)
          .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30)) # Match GEE script
          .map(mask_s2_clouds_and_filter)
          .map(add_indices)
          .select(['NDVI', 'NDMI']))

    chirps = (ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY") # Using DAILY to match sum logic
              .filterDate(start_date, end_date)
              .select('precipitation'))

    # --- 5. MONTHLY AGGREGATION & REDUCTION ---
    # Note: The GEE script used 10-day (Dekadal). We aggregate to MONTHLY here
    # to match the frequency of the Price Data (FEWS NET is monthly).
    
    all_data = []
    dates = pd.date_range(start=start_date, end=end_date, freq='MS')
    
    print(f"⚙️ Processing {len(dates)} months...")
    
    for date in dates:
        y = date.year
        m = date.month
        
        # Define month start and end
        month_start = f"{y}-{m:02d}-01"
        _, last_day = monthrange(y, m)
        month_end = f"{y}-{m:02d}-{last_day}"

        # 1. Vegetation (Median to remove outliers, similar to GEE script)
        # Crucial: We apply the .updateMask(crop_mask) here!
        s2_month = s2.filterDate(month_start, month_end).median().updateMask(crop_mask)
        
        # 2. Rainfall (Sum)
        rain_month = chirps.filterDate(month_start, month_end).sum().rename('Rainfall')
        
        # Combine s2 and rain into a single image for reduction
        combined = s2_month.addBands(rain_month)
        
        # Reduce to LGA Regions (Mean)
        # We process locally to avoid GEE memory limits on large loops
        try:
            stats = combined.reduceRegions(
                collection=kano_lgas,
                reducer=ee.Reducer.mean(),
                scale=500,  # 500m scale for speed (approx match to MODIS/LGA scale)
                tileScale=4 # Helps prevent memory errors
            )
            
            # Extract data
            feature_list = stats.select(['NAME_2', 'NDVI', 'NDMI', 'Rainfall'], retainGeometry=False).getInfo()['features']
            
            if not feature_list:
                print(f"   ⚠️ No data found for {month_start}")
                continue

            for feat in feature_list:
                props = feat['properties']
                all_data.append({
                    'period_start': date,
                    'LGA_NAME': props.get('NAME_2'),
                    'NDVI': props.get('NDVI'),
                    'NDMI': props.get('NDMI'),
                    'Rainfall': props.get('Rainfall')
                })
                
            print(f"   ✅ Processed: {month_start}")
            
        except Exception as e:
            print(f"   ❌ Error processing {month_start}: {e}")

    # --- 6. SAVE BACKUPS & TO DATABASE ---
    print("💾 Converting to DataFrame and cleaning...")
    df = pd.DataFrame(all_data)
    
    # Clean up any missing values from the fetch
    # Nasarawa is a small urban LGA, it is highly urbanized (Kano city area)
    # therefore it has less agricultural land which makes the crop_mask to removes most of the NDVI pixes
    # to avoid losing the LGA from the dataset, we will keep all LGAs even if NDVI is missing. This will allow 
    # us to have a complete dataset for all LGAs and we can handle missing NDVI values later during analysis.
    # df = df.dropna(subset=['NDVI']) 

    # Keep all LGAa, even if NDVI is missing
    df = df.copy()
    
    # Save a CSV backup
    df.to_csv(settings.RAW_ENV_PATH, index=False)
    print(f"📁 Local backup saved to {settings.RAW_ENV_PATH.name}")

    # Save to PostgreSQL
    print(f"💾 Saving data to PostgreSQL database...")
    try:
        df.to_sql(
            name='raw_env_data',
            con=engine,
            if_exists='replace',
            index=False
        )
        print("✅Success! Live satellite data saved to PostgreSQL database.")

    except  Exception as e:
        print(f"❌ Database Error: {e}")

if __name__ == "__main__":
    engine = get_engine()
    fetch_satellite_data(engine)