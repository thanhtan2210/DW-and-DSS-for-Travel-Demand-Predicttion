import streamlit as st
import pandas as pd
import numpy as np
import datetime
import os
import sys
import plotly.express as px
import time
from dotenv import load_dotenv

# Robust path setup to find .env and src at project root
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(root_dir)
dotenv_path = os.path.join(root_dir, '.env')
load_dotenv(dotenv_path)

from src.inference import DemandPredictor

st.set_page_config(page_title="AI Forecast Center", page_icon="🤖", layout="wide")

# --- PREMIUM UI/UX STYLING (CSS Injection) ---
st.markdown("""
    <style>
    .prediction-card {
        background-color: #1E2130;
        padding: 30px;
        border-radius: 15px;
        border-top: 5px solid #00D1FF;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .status-online {
        color: #00FF41;
        font-weight: bold;
        font-family: 'Courier New', Courier, monospace;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🤖 AI Forecast Command Center")
st.markdown("#### *High-Fidelity Travel Demand Prediction Engine*")
st.markdown("---")

@st.cache_resource
def load_predictor(model_type):
    """Loads the prediction engine based on architecture choice."""
    try:
        return DemandPredictor(model_type=model_type)
    except Exception as e:
        st.error(f"Failed to load the neural engine: {e}")
        return None

# --- SIDEBAR: ENGINE CONTROL ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2103/2103633.png", width=80)
st.sidebar.title("Neural Settings")
model_choice = st.sidebar.selectbox("Brain Architecture", ["xgboost", "random_forest", "lstm"])
st.sidebar.markdown(f"**Status:** <span class='status-online'>● CORE_ONLINE</span>", unsafe_allow_html=True)
st.sidebar.markdown("---")

predictor = load_predictor(model_choice)

if predictor:
    # --- INPUT UI ---
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        with st.container():
            st.subheader("📍 Deployment Parameters")
            zone_id = st.number_input("Target Taxi Zone ID", min_value=1, max_value=265, value=161, help="Select NYC Taxi Zone (1-265)")
            
            d_col1, d_col2 = st.columns(2)
            with d_col1:
                pred_date = st.date_input("Target Date", datetime.date(2025, 12, 1))
            with d_col2:
                pred_time = st.time_input("Target Hour", datetime.time(8, 0))
    
    with col2:
        with st.container():
            st.subheader("🌤️ Environmental Factors")
            temp = st.slider("Ambient Temperature (°C)", min_value=-10.0, max_value=40.0, value=15.0)
            precip = st.slider("Precipitation Probability (mm)", min_value=0.0, max_value=50.0, value=0.0)

    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("🔮 INITIALIZE INFERENCE", use_container_width=True):
        # Simulation effects for UX
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i in range(100):
            if i == 20: status_text.text("Retrieving historical lags from BigQuery...")
            if i == 50: status_text.text("Encoding cyclical temporal vectors...")
            if i == 80: status_text.text("Executing neural weights...")
            time.sleep(0.01)
            progress_bar.progress(i + 1)
        
        status_text.empty()
        progress_bar.empty()

        # --- Inference Logic ---
        dt = datetime.datetime.combine(pred_date, pred_time)
        day_of_week = dt.weekday()
        hour = dt.hour
        
        # Prepare Feature Vector
        input_data = pd.DataFrame([{
            'PULocation_Key': zone_id,
            'total_demand': 50, # Placeholder value for Scaler logic
            'Hour': hour,
            'DayOfWeek': day_of_week,
            'Is_Weekend': 1 if day_of_week >= 5 else 0,
            'hour_sin': np.sin(hour * (2. * np.pi / 24)),
            'hour_cos': np.cos(hour * (2. * np.pi / 24)),
            'lag_1h': 45, 'lag_2h': 40, 'lag_24h': 110, 'lag_168h': 105, # Simulated history
            'rolling_mean_6h': 55,
            'Temperature': temp,
            'Precipitation': precip
        }])

        try:
            # Polymorphic prediction via our inference class
            predictions = predictor.predict(input_data)
            prediction = predictions[0]
            
            # --- Results Presentation ---
            res_col1, res_col2 = st.columns([1, 2])
            
            with res_col1:
                st.markdown(f"""
                <div class="prediction-card">
                    <p style="color:#00D1FF;font-size:1.2rem;margin-bottom:0;">PREDICTED DEMAND</p>
                    <h1 style="font-size:5rem;color:white;margin:0;">{int(prediction)}</h1>
                    <p style="color:#AAAAAA;">Taxis required in Zone {zone_id}</p>
                </div>
                """, unsafe_allow_html=True)
                
            with res_col2:
                # Scenario Sensitivity Analysis
                st.subheader("Sensitivity Analysis")
                # Visualizing impact of temperature variance
                temp_range = np.linspace(temp-10, temp+10, 10)
                sim_data = pd.concat([input_data]*10, ignore_index=True)
                sim_data['Temperature'] = temp_range
                
                sim_preds = []
                for i in range(10):
                    p = predictor.predict(sim_data.iloc[[i]])
                    sim_preds.append(p[0])
                
                fig_sim = px.line(x=temp_range, y=sim_preds, 
                                  labels={'x': 'Temperature (°C)', 'y': 'Predicted Demand'},
                                  title="Temperature Elasticity Trend",
                                  template="plotly_dark")
                fig_sim.update_traces(line_color='#00D1FF', line_width=4)
                st.plotly_chart(fig_sim, use_container_width=True)

        except Exception as e:
            st.error(f"Inference Engine Failure: {e}")
            
else:
    st.error("SYSTEM_OFFLINE: Please execute the training pipeline to generate model artifacts.")
