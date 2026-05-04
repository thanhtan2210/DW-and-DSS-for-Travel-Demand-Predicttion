import streamlit as st
import os
from dotenv import load_dotenv

# Robust path setup to find .env at project root
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../.env'))
load_dotenv(dotenv_path)

st.set_page_config(
    page_title="NYC Taxi DSS",
    page_icon="🚕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for Premium Look ---
st.markdown("""
    <style>
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    .main {
        background-color: #0E1117;
    }
    
    /* Feature Card Styling */
    .feature-card {
        padding: 30px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        background: linear-gradient(145deg, #1E2130 0%, #262a3f 100%);
        margin-bottom: 20px;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        height: 100%;
    }
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.4);
        border: 1px solid rgba(0, 209, 255, 0.5);
    }
    .feature-card h3 {
        color: #00D1FF;
        margin-top: 0;
    }
    .feature-card li {
        margin-bottom: 10px;
        color: #E0E0E0;
    }
    </style>
""", unsafe_allow_html=True)

# --- Hero Section ---
st.title("🚕 NYC Urban Mobility Decision Support System")
st.markdown("#### *Enterprise-Grade Data Engineering & AI Forecasting Platform*")

st.image("https://images.unsplash.com/photo-1518235506717-e1ed3306a89b?auto=format&fit=crop&w=1200&q=80", width="stretch")

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="feature-card">
        <h3>📊 OLAP Dashboard</h3>
        <p>Analyze millions of historical records with sub-second latency. Explore trends across boroughs and peak hours.</p>
        <ul>
            <li><strong>Direct BigQuery Storage API</strong> integration for high-speed loading</li>
            <li><strong>Interactive Heatmaps</strong> & Spatial Mapbox rendering</li>
            <li><strong>Polars Engine</strong> for optimized in-memory filtering</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-card">
        <h3>🤖 AI Predictor</h3>
        <p>Deploy trained XGBoost & LSTM models to forecast future demand based on environmental factors.</p>
        <ul>
            <li><strong>Weather-aware</strong> forecasting and what-if sensitivity analysis</li>
            <li><strong>Temporal cyclical encoding</strong> for deep learning precision</li>
            <li><strong>Production-grade MLOps</strong> pipeline architecture</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
st.sidebar.success("👆 Select a dashboard from the menu above to begin.")
