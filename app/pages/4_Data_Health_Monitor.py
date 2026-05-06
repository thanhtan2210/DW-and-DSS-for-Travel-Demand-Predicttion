import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="Data Health Monitor", page_icon="🩺", layout="wide")

st.title("🩺 Data Health & Pipeline Monitor")

# Status check (Mock)
col1, col2, col3 = st.columns(3)
col1.metric("Pipeline Status", "Healthy", delta="Operational")
col2.metric("Last Data Update", "2026-05-07 00:00")
col3.metric("Data Quality Score", "98.5%")

st.subheader("Data Pipeline Logs")
logs = pd.DataFrame({
    'Timestamp': ['2026-05-07 00:00:01', '2026-05-06 23:55:00', '2026-05-06 23:50:00'],
    'Component': ['Weather Fetcher', 'BigQuery Ingest', 'Model Retrain'],
    'Status': ['SUCCESS', 'SUCCESS', 'SUCCESS'],
    'Message': ['Weather data updated', 'Table Dim_Location refreshed', 'Weather model trained']
})

st.table(logs)

st.subheader("System Warnings")
st.warning("No anomalies detected in the last 24 hours.")
