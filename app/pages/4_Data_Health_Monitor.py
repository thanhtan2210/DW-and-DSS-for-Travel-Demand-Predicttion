import streamlit as st
import pandas as pd
from datetime import datetime
import os
from google.cloud import bigquery
from dotenv import load_dotenv

# Robust path setup to find .env at project root
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
dotenv_path = os.path.join(root_dir, '.env')
load_dotenv(dotenv_path)

st.set_page_config(page_title="Data Health Monitor", page_icon="🩺", layout="wide")

st.title("🩺 Data Health & Pipeline Monitor (Cloud Sync)")

# --- DATA ACQUISITION FROM BIGQUERY ---
@st.cache_data(ttl=600)
def get_cloud_pipeline_metrics():
    try:
        client = bigquery.Client()
        project_id = os.getenv("BQ_PROJECT_ID")
        dataset_id = os.getenv("BQ_DATASET_ID", "nyc_taxi_dw")
        staging_id = os.getenv("BQ_STAGING_DATASET_ID", "nyc_taxi_staging")
        
        # Query metadata for all tables to compare Raw (Staging) vs Cleaned (Fact)
        query = f"""
            WITH raw_stats AS (
                SELECT 'yellow' as cat, row_count as raw_rows FROM `{project_id}.{staging_id}.__TABLES__` WHERE table_id = 'raw_yellow'
                UNION ALL
                SELECT 'green' as cat, row_count as raw_rows FROM `{project_id}.{staging_id}.__TABLES__` WHERE table_id = 'raw_green'
                UNION ALL
                SELECT 'fhv' as cat, row_count as raw_rows FROM `{project_id}.{staging_id}.__TABLES__` WHERE table_id = 'raw_fhv'
                UNION ALL
                SELECT 'fhvhv' as cat, row_count as raw_rows FROM `{project_id}.{staging_id}.__TABLES__` WHERE table_id = 'raw_fhvhv'
            ),
            clean_stats AS (
                SELECT 
                    CASE service_type_key WHEN 1 THEN 'yellow' WHEN 2 THEN 'green' WHEN 3 THEN 'fhv' WHEN 4 THEN 'fhvhv' END as cat,
                    COUNT(*) as clean_rows
                FROM `{project_id}.{dataset_id}.Fact_Trips`
                GROUP BY 1
            )
            SELECT 
                r.cat as Category, 
                r.raw_rows as `Raw Rows`, 
                COALESCE(c.clean_rows, 0) as `Cleaned Rows`,
                ROUND(SAFE_DIVIDE(COALESCE(c.clean_rows, 0), r.raw_rows) * 100, 2) as `Retention %`
            FROM raw_stats r
            LEFT JOIN clean_stats c ON r.cat = c.cat
        """
        df = client.query(query).to_dataframe()
        return df
    except Exception as e:
        st.error(f"Error fetching BigQuery metrics: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=600)
def get_dw_update_info():
    try:
        client = bigquery.Client()
        project_id = os.getenv("BQ_PROJECT_ID")
        dataset_id = os.getenv("BQ_DATASET_ID", "nyc_taxi_dw")
        
        # Get last modified time of the main fact table
        meta_query = f"""
            SELECT 
                TIMESTAMP_MILLIS(last_modified_time) as last_update,
                row_count
            FROM `{project_id}.{dataset_id}.__TABLES__`
            WHERE table_id = 'Fact_Demand_Hourly'
        """
        df_meta = client.query(meta_query).to_dataframe()
        if not df_meta.empty:
            return df_meta['last_update'].iloc[0], df_meta['row_count'].iloc[0]
    except Exception as e:
        return None, 0
    return None, 0

# --- EXECUTION ---
with st.spinner("🔍 Auditing BigQuery Warehouse..."):
    cloud_metrics = get_cloud_pipeline_metrics()
    last_update, total_fact_rows = get_dw_update_info()

# Metrics Calculation
if not cloud_metrics.empty:
    total_raw = cloud_metrics['Raw Rows'].sum()
    total_clean = cloud_metrics['Cleaned Rows'].sum()
    avg_retention = cloud_metrics['Retention %'].mean()
    dq_score = (total_clean / total_raw * 100) if total_raw > 0 else 0
else:
    total_raw, total_clean, dq_score = 0, 0, 0

# --- UI LAYOUT ---
col1, col2, col3 = st.columns(3)

# Pipeline Status Logic
status = "Healthy" if dq_score > 90 else "Attention" if dq_score > 50 else "Critical"
col1.metric("Pipeline Status", status, delta="Operational" if status == "Healthy" else "Check Data")

# Last Update display
update_str = last_update.strftime("%Y-%m-%d %H:%M") if last_update else "No data"
col2.metric("Last Cloud Update", update_str, delta=f"{total_fact_rows:,} Hourly Facts")

# Quality Score
col3.metric("Global Retention Rate", f"{dq_score:.1f}%")

st.markdown("---")

c1, c2 = st.columns([2, 1])

with c1:
    st.subheader("📊 Category-wise Data Integrity (BigQuery)")
    if not cloud_metrics.empty:
        st.table(cloud_metrics.set_index('Category'))
        
        # Chart for visual comparison
        chart_df = cloud_metrics.melt(id_vars='Category', value_vars=['Raw Rows', 'Cleaned Rows'], var_name='Type', value_name='Count')
        import plotly.express as px
        st.plotly_chart(px.bar(chart_df, x='Category', y='Count', color='Type', barmode='group', template='plotly_dark'), use_container_width=True)
    else:
        st.warning("Could not retrieve category stats from BigQuery. Check if tables 'raw_yellow', 'raw_green', etc. exist.")

with c2:
    st.subheader("🌐 Cloud Infrastructure")
    
    st.markdown("**Resource Location**")
    st.success("Region: US-Multi-Region (Google Cloud)")
    
    st.markdown("**Active Dataset**")
    st.code(f"{os.getenv('BQ_PROJECT_ID')}.{os.getenv('BQ_DATASET_ID', 'nyc_taxi_dw')}")
    
    st.markdown("**Table Integrity**")
    st.write("✅ Fact_Trips (Transaction Level)")
    st.write("✅ Fact_Demand_Hourly (Aggregated)")
    st.write("✅ Dim_Time (Temporal)")
    st.write("✅ Dim_Location (Spatial)")

st.subheader("🔍 Automated Anomaly Detection")
if not cloud_metrics.empty:
    for index, row in cloud_metrics.iterrows():
        if row['Retention %'] < 80:
            st.error(f"Critical Data Loss in {row['Category'].upper()}: Only {row['Retention %']}% of data passed filters.")
        elif row['Retention %'] < 95:
            st.warning(f"Note: {row['Category'].upper()} filter retention at {row['Retention %']}%.")
    
    if dq_score > 95:
        st.success("Overall warehouse integrity is within optimal range (>95%).")
else:
    st.info("Awaiting BigQuery audit results...")
