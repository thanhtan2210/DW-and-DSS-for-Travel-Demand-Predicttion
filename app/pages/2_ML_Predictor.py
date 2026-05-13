import streamlit as st
import pandas as pd
import numpy as np
import datetime
import os
import sys
import plotly.express as px
from google.cloud import bigquery
from dotenv import load_dotenv
import joblib
import tensorflow as tf

# Robust path setup
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

# --- Weather AI Engine (Recursive Timeline) ---
WEATHER_MODEL_PATH = os.path.join(root_dir, 'saved_models/weather/weather_forecast_model.keras')
WEATHER_SCALER_PATH = os.path.join(root_dir, 'saved_models/weather/weather_scaler.pkl')

@st.cache_resource
def load_weather_artifacts():
    if os.path.exists(WEATHER_MODEL_PATH) and os.path.exists(WEATHER_SCALER_PATH):
        return tf.keras.models.load_model(WEATHER_MODEL_PATH), joblib.load(WEATHER_SCALER_PATH)
    return None, None

@st.cache_data(ttl=3600)
def get_historical_context():
    weather_file = os.path.join(root_dir, 'dataset/weather_forecast/weather_data_20260510.csv')
    if os.path.exists(weather_file):
        df_w = pd.read_csv(weather_file)
        df_w['time'] = pd.to_datetime(df_w['time'])
        return df_w.sort_values('time')
    return pd.DataFrame()

def predict_weather_timeline(target_dt, steps=24):
    """Predicts weather sequence using recursive LSTM with cyclical time features."""
    model, scaler = load_weather_artifacts()
    df_hist = get_historical_context()
    if model is None or df_hist.empty:
        return pd.DataFrame({'time': [target_dt], 'temp': [20.0], 'precip': [0.0]})

    target_dt = target_dt.replace(tzinfo=None)
    last_hist_dt = df_hist['time'].max()
    
    # 1. Prepare initial sequence (24h)
    context = df_hist.tail(24).copy()
    context['hour'] = context['time'].dt.hour
    context['day_of_year'] = context['time'].dt.dayofyear
    context['hour_sin'] = np.sin(2 * np.pi * context['hour'] / 24)
    context['hour_cos'] = np.cos(2 * np.pi * context['hour'] / 24)
    context['day_sin'] = np.sin(2 * np.pi * context['day_of_year'] / 365)
    context['day_cos'] = np.cos(2 * np.pi * context['day_of_year'] / 365)
    
    # Features order must match training: [temp, precip, h_sin, h_cos, d_sin, d_cos]
    feature_values = context[['temperature_2m', 'precipitation', 'hour_sin', 'hour_cos', 'day_sin', 'day_cos']].values
    current_seq = scaler.transform(feature_values)
    
    curr_time = last_hist_dt
    
    # 2. Recursive Prediction Loop
    # We bridge the gap to target_dt first, then generate the 24h forecast
    total_steps = steps
    if target_dt > last_hist_dt:
        gap_hours = int((target_dt - last_hist_dt).total_seconds() / 3600)
        total_steps += gap_hours

    all_predictions = []
    for i in range(total_steps):
        # Predict next step (returns scaled [temp, precip])
        pred_raw = model.predict(np.expand_dims(current_seq, axis=0), verbose=0)
        
        # Clipping to prevent values from blowing up in recursive loops
        pred_scaled = np.clip(pred_raw, 0, 1)
        
        # Move time forward
        curr_time += datetime.timedelta(hours=1)
        
        # Calculate time features for the new step
        h_sin = np.sin(2 * np.pi * curr_time.hour / 24)
        h_cos = np.cos(2 * np.pi * curr_time.hour / 24)
        d_sin = np.sin(2 * np.pi * curr_time.timetuple().tm_yday / 365)
        d_cos = np.cos(2 * np.pi * curr_time.timetuple().tm_yday / 365)
        
        # Construct full scaled vector for the next input
        # We must scale the time features manually since they are raw
        time_feats_raw = np.array([[0, 0, h_sin, h_cos, d_sin, d_cos]])
        time_feats_scaled = scaler.transform(time_feats_raw)[0, 2:]
        
        new_entry_scaled = np.zeros((1, 6))
        new_entry_scaled[0, :2] = pred_scaled[0]
        new_entry_scaled[0, 2:] = time_feats_scaled
        
        # Update sequence
        current_seq = np.append(current_seq[1:], new_entry_scaled, axis=0)
        
        # If we are within the requested forecast window, store results
        if curr_time >= target_dt:
            # IMPORTANT: Inverse transform the scaled prediction to get real units
            full_scaled_vec = np.zeros((1, 6))
            full_scaled_vec[0, :2] = pred_scaled[0]
            real_values = scaler.inverse_transform(full_scaled_vec)[0]
            
            all_predictions.append({
                'time': curr_time,
                'temp': real_values[0],
                'precip': max(0, real_values[1])
            })
            
        if len(all_predictions) >= steps:
            break
            
    return pd.DataFrame(all_predictions)

# --- UI Layout ---
col1, col2 = st.columns([1, 2])

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
    st.subheader("🌤️ AI Weather Timeline (24h Forecast)")
    dt_combine = datetime.datetime.combine(selected_date, selected_time)
    
    # Automatic Weather Generation
    with st.spinner("AI Syncing Weather Timeline..."):
        weather_df = predict_weather_timeline(dt_combine)
        st.session_state['weather_temp'] = weather_df['temp'].iloc[0]
        st.session_state['weather_precip'] = weather_df['precip'].iloc[0]
        st.session_state['weather_ready'] = True

    fig_w = px.line(weather_df, x='time', y='temp', title="Temperature Trend (°C)", template="plotly_dark")
    fig_w.add_bar(x=weather_df['time'], y=weather_df['precip'], name="Rain (mm)")
    st.plotly_chart(fig_w, use_container_width=True)
    st.info(f"Target Conditions: **{st.session_state['weather_temp']:.1f}°C**, **{st.session_state['weather_precip']:.2f}mm** rain.")

st.markdown("---")

# --- Inference (Exactly your requested logic and map coloring) ---
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
            'rolling_mean_6h': 55, 
            'Temperature': st.session_state['weather_temp'],
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
            
            # Add Map Visualization (Restored and Kept Coloring)
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
            
        except Exception as e:
            st.error(f"Prediction Error: {e}")
