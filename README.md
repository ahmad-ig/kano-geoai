Kano GeoAI Food Security System
Overview
The Kano GeoAI Food Security System is an end-to-end Geospatial Artificial Intelligence pipeline designed to analyze and predict the relationship between environmental conditions, macroeconomic volatility, and staple food prices in Kano State, Nigeria.

The system integrates satellite remote sensing, market price data, and machine learning to generate actionable insights on crop stress and price dynamics at the Local Government Area (LGA) level.

Problem Statement
Food security remains a critical challenge in developing economies. In Kano State, traditional monitoring fails because it isolates physical crop health from the reality of economic hyperinflation. This project addresses the question:

How can we mathematically unify environmental signals (satellite data) with macroeconomic indicators (currency devaluation) to proactively predict crop stress and food price shocks?

System Architecture
Plaintext
Satellite Data (NDVI/Rainfall)      Market Data (Prices) & Macro (NGN/USD)
                │                               │
                └────────── Data Fusion ────────┘
                                │
                 ETL & Feature Engineering Pipeline
                                │
         XGBoost Machine Learning Models (Prices & Stress)
                                │
                 PostgreSQL + PostGIS Database
                                │
            Streamlit Dashboard & Scenario Simulator
Key Components
1. Data Ingestion
Satellite Data: Sentinel-2 (NDVI, NDMI), CHIRPS (Rainfall), Dynamic World (Stable Crop Masking) via Google Earth Engine API.

Market & Economic Data: Wholesale staple food prices (Maize, Sorghum, Millet) and NGN/USD Exchange Rates via the FEWS NET API.

2. Geospatial Processing
Region of Interest: 44 LGAs in Kano State.

Stable Crop Masking: Isolating active agricultural land to remove urban/desert noise.

Monthly spatial aggregation of environmental anomalies (Z-scores).

3. Feature Engineering
Temporal Lags: Autoregressive "Time Travel" features feeding historical weather and pricing into the model.

Advanced Differencing: Target transformation predicting the month-to-month change (Δ price) to stabilize hyper-inflationary data.

4. Machine Learning
Algorithm: Gradient-Boosted Decision Trees (XGBRegressor).

Price Models: Predicts market trajectories for Maize, Sorghum, and Millet (Achieved 13.27% MAPE).

Stress Model: An auto-regressive model forecasting future Vegetation Health / NDVI Anomalies.

5. Database Layer
PostgreSQL + PostGIS: Stores processed datasets, serialized models, and spatial geometries (LGA Shapefiles) for map rendering.

6. Visualization (Deployment)
Interactive frontend built with Streamlit, GeoPandas, and Plotly Mapbox.

Features an LGA-level Vegetation Health Heatmap and a real-time Scenario Simulator allowing policymakers to adjust exchange rates/rainfall to forecast future price shocks.

Project Structure
Plaintext
Kano_GeoAI_System/
│
├── config/                # Configuration (paths, settings, database, secrets)
├── src/
│   ├── data/              # Data ingestion pipelines (GEE, FEWS NET)
│   ├── features/          # ETL & Feature engineering
│   ├── models/            # XGBoost training scripts (Prices & Stress)
│   ├── app/               # Inference engine & Streamlit Dashboard
│
├── data/                  # Raw & processed data (ignored in Git)
├── models/                # Trained .pkl models (ignored in Git)
├── .env                   # Environment variables (ignored)
├── requirements.txt
├── README.md
Setup Instructions
1. Clone Repository
Bash
git clone https://github.com/your-username/Kano_GeoAI_System.git
cd Kano_GeoAI_System
2. Create Environment
Bash
conda create -n geoai python=3.10
conda activate geoai
pip install -r requirements.txt
3. Configure Environment Variables
Create a .env file in the root directory:

Plaintext
DB_USER=postgres
DB_PASS=yourpassword
DB_HOST=localhost
DB_PORT=5432
DB_NAME=geoai_final_year_project_db

GEE_PROJECT_ID=your_project_id
FEWSNET_API_URL=https://fdw.fews.net/api/marketpricefacts/?country_code=NG&format=csv
Running the Pipeline
Step 1: Data Ingestion

Bash
python -m src.data.fetch_prices_api
python -m src.data.fetch_satellite_api
Step 2: ETL & Feature Engineering

Bash
python -m src.features.etl_pipeline
Step 3: Train Machine Learning Models

Bash
python -m src.models.train_price_models
python -m src.models.train_stress_model
Step 4: Launch the Dashboard

Bash
streamlit run src/app/dashboard.py
Future Improvements
Migration from static evaluation to a fully automated MLOps pipeline (Prefect/MLflow).

Deployment of PostgreSQL database to cloud infrastructure (Supabase/Neon).

Integration of Natural Language Processing (NLP) to quantify localized socio-political insecurity (banditry).

Author
Ahmad Ibrahim
GeoAI & Machine Learning Engineer

License
This project is for academic and research purposes.