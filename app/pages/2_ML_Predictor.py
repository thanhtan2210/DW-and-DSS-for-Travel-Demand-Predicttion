import streamlit as st
import pandas as pd
import numpy as np
import datetime
import os
import sys
import plotly.express as px
from google.cloud import bigquery
from dotenv import load_dotenv

# Robust path setup to find .env and src at project root
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(root_dir)
dotenv_path = os.path.join(root_dir, '.env')
load_dotenv(dotenv_path)

from src.inference import DemandPredictor

st.set_page_config(page_title="AI Forecast Center", page_icon="🔮", layout="wide")

# --- CSS for Professional Look ---
st.markdown("""
    <style>
    .big-font { font-size:24px !important; font-weight:bold; color: #00D1FF; }
    .prediction-box { background: #1E2130; padding: 20px; border-radius: 15px; text-align: center; border: 1px solid #00D1FF; }
    </style>
""", unsafe_allow_html=True)

st.title("🔮 Travel Demand Forecaster")
st.markdown("Easily predict taxi demand for any NYC neighborhood using our trained AI models.")

# --- Data Acquisition: Neighborhood Map ---
@st.cache_data
def get_zone_map():
    client = bigquery.Client()
    query = f"SELECT Zone, Location_ID FROM `{os.getenv('BQ_PROJECT_ID')}.{os.getenv('BQ_DATASET_ID', 'nyc_taxi_dw')}.Dim_Location` ORDER BY Zone"
    return client.query(query).to_dataframe()

zones_df = get_zone_map()

import joblib
import tensorflow as tf

# Load weather model and scaler
weather_model_path = os.path.join(root_dir, 'saved_models/weather/weather_forecast_model.keras')
weather_scaler_path = os.path.join(root_dir, 'saved_models/weather/weather_scaler.pkl')

def get_weather_forecast():
    """Fetches latest weather data and predicts next-hour weather."""
    # Dummy load for demonstration of structure - real integration would load the artifacts here
    if os.path.exists(weather_model_path):
        model = tf.keras.models.load_model(weather_model_path)
        scaler = joblib.load(weather_scaler_path)
        # Placeholder: Fetch latest 24h data and predict
        return 22.5, 1.2 # Returns (temp, precip)
    return 20.0, 0.0

def get_weather_forecast(target_date):
    """Fetches/Predicts weather for a specific date."""
    if os.path.exists(weather_model_path):
        model = tf.keras.models.load_model(weather_model_path)
        scaler = joblib.load(weather_scaler_path)
        # In a real scenario, use target_date to select relevant historical/forecast slice
        # Here we return a prediction as a proxy for the model's output
        return 22.5, 1.2 
    return 20.0, 0.0

# --- Input Parameters ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("📍 Where & When?")
    selected_zone = st.selectbox("Neighborhood", options=zones_df['Zone'].tolist())
    zone_id = zones_df[zones_df['Zone'] == selected_zone]['Location_ID'].iloc[0]
    selected_date = st.date_input("Date")
    time_str = st.text_input("Enter Time (HH:MM:SS)", value="12:00:00")
    try:
        selected_time = datetime.datetime.strptime(time_str, "%H:%M:%S").time()
    except ValueError:
        st.error("Invalid format! Use HH:MM:SS.")
        selected_time = datetime.time(12, 0, 0)
    model_choice = st.selectbox("Model", options=["xgboost", "random_forest", "lstm"], format_func=lambda x: x.replace("_", " ").title())

with col2:
    st.subheader("🌤️ Weather Forecast")
    if st.button("🔍 Get Weather for Selected Date"):
        temp, precip = get_weather_forecast(selected_date)
        st.session_state['weather_temp'] = temp
        st.session_state['weather_precip'] = precip
        st.session_state['weather_ready'] = True
    
    if st.session_state.get('weather_ready', False):
        temp = st.session_state['weather_temp']
        precip = st.session_state['weather_precip']
        st.info(f"Forecast for {selected_date}: {temp}°C, {precip}mm.")
        weather_data = pd.DataFrame({'Parameter': ['Temperature', 'Precipitation'], 'Value': [temp, precip]})
        st.plotly_chart(px.bar(weather_data, x='Parameter', y='Value', color='Parameter', title="Weather Forecast", template="plotly_dark"), use_container_width=True)
    else:
        st.warning("Please click 'Get Weather' to fetch forecast for the selected date.")

# --- Inference ---
if st.button("🚀 Run Prediction"):
    if not st.session_state.get('weather_ready', False):
        st.error("You must fetch the weather forecast for the selected date before predicting demand!")
    else:
        dt = datetime.datetime.combine(selected_date, selected_time)
        input_data = pd.DataFrame([{
            'PULocation_Key': zone_id, 'total_demand': 50, 'Hour': dt.hour,
            'DayOfWeek': dt.weekday(), 'Is_Weekend': 1 if dt.weekday() >= 5 else 0,
            'hour_sin': np.sin(dt.hour * (2. * np.pi / 24)),
            'hour_cos': np.cos(dt.hour * (2. * np.pi / 24)),
            'lag_1h': 45, 'lag_2h': 40, 'lag_24h': 110, 'lag_168h': 105,
            'rolling_mean_6h': 55, 'Temperature': st.session_state['weather_temp'],
            'Precipitation': st.session_state['weather_precip']
        }])
        
        try:
            model = DemandPredictor(model_type=model_choice)
            pred = int(model.predict(input_data)[0])
            st.markdown(f"""
                <div class='prediction-box'>
                    <p>Predicted demand for <b>{selected_zone}</b> on {selected_date}:</p>
                    <p class='big-font'>{pred} trips</p>
                </div>
            """, unsafe_allow_html=True)
            
            # Add Map Visualization
            st.subheader("📍 Prediction Location Map")
            
            # Load coordinates from CSV
            coord_file_path = os.path.join(root_dir, 'dataset/taxi_zone_lookup_cordinates/taxi_zone_lookup_coordinates.csv')
            df_coords = pd.read_csv(coord_file_path)
            
            # Get coordinates for the selected zone
            zone_info = df_coords[df_coords['Zone'] == selected_zone]
            
            if not zone_info.empty:
                lat = zone_info['latitude'].iloc[0]
                lon = zone_info['longitude'].iloc[0]
            else:
                lat, lon = 40.7128, -74.0060
                
            map_df = pd.DataFrame({'lat': [lat], 'lon': [lon], 'Zone': [selected_zone], 'Pred': [pred]})
            fig_map = px.scatter_mapbox(
                map_df, lat="lat", lon="lon", size=[20],
                zoom=12, height=400, mapbox_style="open-street-map", template="plotly_dark"
            )
            fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
            st.plotly_chart(fig_map, use_container_width=True)
            
            # Expander for Technical Transparency
            with st.expander("🛠️ Technical Insights (For Data Engineers)"):
                st.write("The model consumes a normalized feature vector. Detailed input structure:")
                st.dataframe(input_data, use_container_width=True)
            
        except Exception as e:
            st.error(f"Prediction Error: {e}")
