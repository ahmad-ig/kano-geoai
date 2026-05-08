import sys
import os
# Add the project root directory to Python's search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))


import json
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

#import src.inference.predict as predict
from src.inference.predict import predict_stress, predict_prices, prepare_next_month_features, load_latest_context

from config import paths
from config import settings
#from config.database import get_engine
#from src.db.queries import get_processed_features, get_lga_map_data


# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Kano Food Security AI", page_icon="🌾", layout="wide")

# --- CSS STYLING ---
st.markdown("""
<style>
    .metric-card { background-color: #f0f2f6; color: #000; padding: 20px; border-radius: 10px; border-left: 5px solid #2e7d32; }
    .warning-card { background-color: #ffebee; color: #000; padding: 20px; border-radius: 10px; border-left: 5px solid #c62828; }
    .metric-card h3, .warning-card h3 { color: #000 !important; }
    .metric-card p, .warning-card p { color: #333 !important; }
</style>
""", unsafe_allow_html=True)

# --- USER GUIDE EXPANDER ---
with st.expander("📖 Dashboard Navigation & Input Guide"):
    st.markdown("""
    ### Welcome to the Kano GeoAI Food Security Dashboard
    This interactive dashboard serves as an early-warning system, combining satellite environmental data with macroeconomic indicators to forecast staple grain prices (Maize, Sorghum, Millet) and crop stress across Kano State.

    ---

    ### 🧭 How to Navigate the System

    **1. The LGA Spatial Heatmap (Environmental Monitoring)**
    * **What it shows:** A live, color-coded map of Kano State's 44 Local Government Areas (LGAs).
    * **How to use it:** Hover your mouse over any LGA to view its specific environmental metrics. The colors indicate the current **Vegetation Stress (NDVI Anomaly)**. Darker or warmer colors indicate areas experiencing prolonged dry spells or crop degradation, while greener areas indicate healthy agricultural zones.

    **2. The Scenario Simulator (The Predictive Engine)**
    * **Where to find it:** Located on the left-hand sidebar.
    * **What it does:** This is the core machine learning engine. It allows you to bypass data delays and instantly test "What-If" scenarios to see how weather and the economy will affect next month's prices.

    **3. Grain Price Trajectories (Market Output)**
    * **What it shows:** Interactive time-series charts displaying wholesale prices at the Dawanau International Market.
    * **How to use it:** The solid lines represent the historical baseline prices. The dashed line at the end of the chart represents the **GeoAI Forecast**, calculated based on the exact inputs you provided in the Scenario Simulator.

    ---

    ### 🎛️ Understanding the Inputs & Valid Ranges
    To ensure the predictive engine provides accurate forecasts, please keep your simulation inputs within the realistic boundaries of the Kano State market and climate ecosystem.

    **1. Current Crop Price (₦)**
    * **What it is:** The baseline wholesale price for a 100kg bag of grain at the Dawanau Market.
    * **Valid Range:** Must be a positive number reflecting current market realities.

    **2. Exchange Rate (NGN/USD)**
    * **What it is:** The macroeconomic indicator representing currency inflation or stabilization.
    * **Valid Range:** **800 to 2,500 NGN/USD**. 
    * *Note:* Entering an extreme, impossible crash (e.g., 20,000 NGN/USD) will cause the model to cap at its highest known training parameter, as tree-based models cannot extrapolate to infinity.

    **3. Environmental Anomalies (Rainfall, NDVI, NDMI)**
    * **What they are:** These inputs use **Z-scores**. They do not represent raw values (like millimeters of rain), but rather how far the current weather deviates from the 7-year historical average. 
    * **Valid Range:** **-3.0 to +3.0**
        * **0.0 (Normal):** Exactly average historical conditions.
        * **+1.0 to +3.0 (Surplus):** Above-average conditions (e.g., heavy rainfall, excellent soil moisture).
        * **-1.0 to -3.0 (Deficit):** Below-average conditions (e.g., severe drought, dying crops).

    ---
    
    **💡 Pro-Tip for Policymakers:** To test the resilience of the local market, try setting the Rainfall slider to "Normal" (0.0 anomaly) but increase the Exchange Rate slider to simulate high inflation. The model will demonstrate the "macroeconomic blind spot"—showing how prices will still spike despite perfect weather conditions.
    """)

# --- 1. LOAD DATA ---
@st.cache_data(ttl=3600)
def get_predictions(manual_overrides=None):
    try:
        last_row, last_date, all_cols = load_latest_context()
        if manual_overrides:
            last_row = last_row.copy()  # Avoid modifying the original cached data
            for col, val in manual_overrides.items():
                last_row[col] = val

        input_df, season_cols = prepare_next_month_features(last_row, last_date, all_cols)
        stress_val = predict_stress(input_df)
        price_preds = predict_prices(input_df, last_row, season_cols)
        next_date = last_date + pd.DateOffset(months=1)
        
        return last_row, last_date, next_date, stress_val, price_preds
    except Exception as e:
        st.error(f"Error running inference: {e}")
        return None, None, None, None, None

@st.cache_data(ttl=3600)
def load_historical_data():
    """Load historical data for charts."""
    return pd.read_csv(paths.PROCESSED_DATA_PATH, parse_dates=['Date'])


@st.cache_data(ttl=3600)
def load_lga_map_data():
    """Load LGA map + latest NDVI data from DB."""

    with open(paths.PROCESSED_LGA_MAP_PATH) as f:
        kano_geojson = json.load(f)

    lga_df = pd.read_csv(paths.PROCESSED_ENV_DATA_PATH)

    # Clean the names to ensure perfect matching with the Shapefile
    if not lga_df.empty:
        lga_df['LGA_NAME'] = lga_df['LGA_NAME'].str.strip()
    
    return kano_geojson, lga_df

# --- 2. SIDEBAR ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2909/2909564.png", width=100)
st.sidebar.title("Kano GeoAI System")
st.sidebar.markdown("---")

crop_options = [c.replace('Price_', '') for c in settings.CROPS]
selected_crop_name = st.sidebar.selectbox("Select Crop to Analyze", crop_options)
selected_crop = f"Price_{selected_crop_name}"

st.sidebar.markdown("---")
st.sidebar.subheader("🔮 Forecast Simulator")
enable_sim = st.sidebar.checkbox("Enable Scenario Mode")

manual_overrides = {}

if enable_sim:
    st.sidebar.info("Adjust inputs to simulate scenarios.")
    base_row, _, _, _, _ = get_predictions()
    
    if base_row is not None:
        # Enforce positive values for grain prices
        manual_overrides[selected_crop] = st.sidebar.number_input(
            f"Current {selected_crop_name} Price (₦)", 
            value=float(base_row[selected_crop]), 
            min_value=0.0, 
            step=500.0
        )
        
        # Enforce realistic exchange rate bounds (e.g., 500 to 3500) to prevent the Extrapolation Trap
        if 'Exchange_Rate' in base_row:
            manual_overrides['Exchange_Rate'] = st.sidebar.number_input(
                "Exchange Rate (NGN/USD)", 
                value=float(base_row['Exchange_Rate']), 
                min_value=500.0, 
                max_value=3500.0, 
                step=50.0
            )
            
        # Enforce Z-Score physics limits (-4.0 to +4.0) for climate variables
        manual_overrides['NDVI_Anomaly'] = st.sidebar.number_input(
            "NDVI Anomaly", 
            value=float(base_row['NDVI_Anomaly']), 
            min_value=-4.0, 
            max_value=4.0, 
            step=0.1
        )
        manual_overrides['NDMI_Anomaly'] = st.sidebar.number_input(
            "NDMI Anomaly", 
            value=float(base_row['NDMI_Anomaly']), 
            min_value=-4.0, 
            max_value=4.0, 
            step=0.1
        )
        manual_overrides['Rainfall_Anomaly'] = st.sidebar.number_input(
            "Rainfall Anomaly", 
            value=float(base_row['Rainfall_Anomaly']), 
            min_value=-4.0, 
            max_value=4.0, 
            step=0.1
        )
        
# --- 3. MAIN DASHBOARD ---
last_row, last_date, next_date, stress_val, price_preds = get_predictions(manual_overrides)
history_df = load_historical_data()
kano_geojson, lga_df = load_lga_map_data()

if price_preds and not history_df.empty:
    st.title(f"🌾 Kano State GeoAI Food Security Dashboard")
    st.markdown(f"**Forecast Target:** {next_date.strftime('%B %Y')} | **Current Data:** {last_date.strftime('%B %Y')}")
    st.markdown("---")

    # -- TOP ROW: KPIs --
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("🌱 Forecasted Vegetation")
        color, status = ("red", "🔴 HIGH DROUGHT RISK") if stress_val < -1.0 else ("orange", "🟡 MILD STRESS") if stress_val < -0.5 else ("green", "🟢 NORMAL CONDITIONS")
        st.markdown(f"""<div class="{'warning-card' if color == 'red' else 'metric-card'}">
            <h3 style="color:{color}; margin:0;">{status}</h3><p style="font-size:24px; margin:0;">Index: {stress_val:.3f}</p></div>""", unsafe_allow_html=True)

    pred_data = price_preds[selected_crop]
    change = pred_data['change']
    with col2:
        st.subheader(f"💰 {selected_crop_name} Price Forecast")
        st.metric("Predicted Price (100kg)", f"₦{pred_data['pred']:,.0f}", f"{change:+,.0f} ({(change/pred_data['current'])*100:.1f}%)", delta_color="inverse" if change > 0 else "normal")

    with col3:
        st.subheader("📊 Market Trend")
        st.markdown(f"""<div class="metric-card"><h3>{"Inflationary" if change > 0 else "Deflationary"} Trend</h3>
            <p>Current: ₦{pred_data['current']:,.0f}</p><small>Simulated Input if Active</small></div>""", unsafe_allow_html=True)

    st.markdown("---")

    # -- MIDDLE ROW: MAP & CHART --
    col_map, col_chart = st.columns([1, 1])

    with col_map:
        st.subheader("🗺️ Live Crop Health Heatmap")
        st.caption("Vegetation Health (NDVI) across Kano State LGAs")
        
        if lga_df.empty or kano_geojson is None:
            st.warning("⚠️ No map data available for the current month.")
        else:
            # Build the Plotly Choropleth Map
            fig_map = px.choropleth_mapbox(
                lga_df,
                geojson=kano_geojson,
                locations="LGA_NAME",               # DataFrame column
                # ⚠️ IMPORTANT: If your shapefile's column for LGA names is NOT "ADM2_NAME", 
                # you MUST change the line below to match your shapefile (e.g., "properties.LGA_NAME")
                featureidkey="properties.lga_name", 
                color="NDVI",
                color_continuous_scale="RdYlGn",     # Red = Bad, Green = Good
                range_color=[lga_df['NDVI'].min(), lga_df['NDVI'].max()], # Dynamic scaling
                mapbox_style="carto-positron",
                zoom=7.2,
                center={"lat": 11.7, "lon": 8.5},    # Centered tightly on Kano
                opacity=0.8,
                hover_name="LGA_NAME",              # Big bold text on hover
                hover_data={"LGA_NAME": False, "NDVI": True, "Rainfall": True} # Tooltip details
            )
            
            # Force white borders around LGAs so it doesn't look like a blob
            fig_map.update_traces(marker_line_width=1, marker_line_color="white")
            
            fig_map.update_layout(
                margin={"r":0,"t":0,"l":0,"b":0},
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            
            st.plotly_chart(fig_map, use_container_width=True)

    with col_chart:
        st.subheader(f"📈 24-Month Trajectory: {selected_crop_name}")
        st.caption("Historical trends vs AI Prediction")
        
        chart_data = history_df.tail(24).copy()
        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(x=chart_data['Date'], y=chart_data[selected_crop], mode='lines+markers', name='History', line=dict(color='#1f77b4', width=3)))
        start_y = pred_data['current'] if enable_sim else chart_data.iloc[-1][selected_crop]
        fig_line.add_trace(go.Scatter(x=[chart_data.iloc[-1]['Date'], next_date], y=[start_y, pred_data['pred']], mode='lines+markers', name='Forecast', line=dict(color='#d62728', width=3, dash='dot'), marker=dict(size=10, symbol='star')))
        fig_line.update_layout(xaxis_title="Date", yaxis_title="Price (NGN)", hovermode="x unified", template="plotly_white", margin={"t":0})
        st.plotly_chart(fig_line, use_container_width=True)