import streamlit as st
import pandas as pd
import polars as pl
import plotly.express as px
from google.cloud import bigquery
import os
import time
from datetime import datetime
from dotenv import load_dotenv

# Robust path setup to find .env at project root
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
dotenv_path = os.path.join(root_dir, '.env')
load_dotenv(dotenv_path)

st.set_page_config(page_title="NYC Analytics Master", page_icon="📊", layout="wide")

# --- Custom Styling ---
st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] { font-weight: bold; padding: 10px 20px; font-size: 1.1rem; }
    .status-box { padding: 10px; border-radius: 5px; background-color: #1E2130; border-left: 5px solid #00D1FF; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 NYC Taxi Insight Center (Professional Suite)")

# --- DATA ENGINES ---

@st.cache_data(ttl=3600, show_spinner=False)
def load_borough_summary():
    """Fetches high-level aggregated data for macro-trend analysis (Tabs 1-3)."""
    client = bigquery.Client()
    project_id = os.getenv("BQ_PROJECT_ID")
    dataset_id = os.getenv("BQ_DATASET_ID", "nyc_taxi_dw")
    query = f"""
    SELECT 
        t.Full_Date, t.Hour, t.Day_of_Week_Name,
        l.Borough, l.Zone, s.Service_Name,
        SUM(f.total_demand) as total_trips,
        SUM(f.total_revenue_generated) as total_revenue,
        AVG(f.average_trip_distance) as avg_dist
    FROM `{project_id}.{dataset_id}.Fact_Demand_Hourly` f
    JOIN `{project_id}.{dataset_id}.Dim_Time` t ON f.pickup_time_key = t.Time_Key
    JOIN `{project_id}.{dataset_id}.Dim_Location` l ON f.pulocationid = l.Location_ID
    JOIN `{project_id}.{dataset_id}.Dim_Service_Type` s ON f.service_type_key = s.Service_Type_Key
    GROUP BY 1, 2, 3, 4, 5, 6
    """
    df = client.query(query).to_dataframe(create_bqstorage_client=True)
    df['Full_Date'] = pd.to_datetime(df['Full_Date'])
    df['Borough'] = df['Borough'].str.strip().str.title()
    return pl.from_pandas(df)

@st.cache_data(ttl=3600, show_spinner=False)
def load_zone_detail(zone_name):
    """Lazy-loads granular neighborhood data only when requested (Tab 4)."""
    client = bigquery.Client()
    project_id = os.getenv("BQ_PROJECT_ID")
    dataset_id = os.getenv("BQ_DATASET_ID", "nyc_taxi_dw")
    query = f"""
    SELECT t.Full_Date, f.total_demand, s.Service_Name 
    FROM `{project_id}.{dataset_id}.Fact_Demand_Hourly` f
    JOIN `{project_id}.{dataset_id}.Dim_Time` t ON f.pickup_time_key = t.Time_Key
    JOIN `{project_id}.{dataset_id}.Dim_Location` l ON f.pulocationid = l.Location_ID
    JOIN `{project_id}.{dataset_id}.Dim_Service_Type` s ON f.service_type_key = s.Service_Type_Key
    WHERE l.Zone = @zn
    """
    job_config = bigquery.QueryJobConfig(query_parameters=[bigquery.ScalarQueryParameter("zn", "STRING", zone_name)])
    return client.query(query, job_config=job_config).to_dataframe(create_bqstorage_client=True)

# --- EXECUTION ---
with st.spinner("🚀 Streaming cloud analytics..."):
    df = load_borough_summary()

# Borough Centroid Mapping for Visualization
borough_coordinates = pd.DataFrame([
    {'Borough': 'Manhattan', 'lat': 40.7831, 'lon': -73.9712},
    {'Borough': 'Brooklyn', 'lat': 40.6782, 'lon': -73.9442},
    {'Borough': 'Queens', 'lat': 40.7282, 'lon': -73.7949},
    {'Borough': 'Bronx', 'lat': 40.8448, 'lon': -73.8648},
    {'Borough': 'Staten Island', 'lat': 40.5795, 'lon': -74.1502}
])

# --- SIDEBAR CONTROL CENTER ---
st.sidebar.title("Global Control Panel")
all_boros = sorted(df["Borough"].unique().to_list())
selected_boros = st.sidebar.multiselect("Active Regions", options=all_boros, default=all_boros, key="boro_ms")
data_filtered = df.filter(pl.col("Borough").is_in(selected_boros))

# KPIs
k1, k2, k3 = st.columns(3)
k1.metric("Total Volume", f"{data_filtered['total_trips'].sum():,.0f} rides")
k2.metric("Gross Revenue", f"${data_filtered['total_revenue'].sum():,.2f}")
k3.metric("Avg Trip Length", f"{data_filtered['avg_dist'].mean():.2f} mi")

st.markdown("<br>", unsafe_allow_html=True)

# --- THE 4 TABS ARCHITECTURE ---
tab1, tab2, tab3, tab4 = st.tabs(["🕒 Temporal Dynamics", "🌍 Unified Spatial View", "💰 Financial Flows", "🔍 Zone Deep Dive"])

with tab1:
    st.subheader("Time-Series Demand Patterns")
    col1, col2 = st.columns([2, 1])
    with col1:
        daily_trend = data_filtered.group_by("Full_Date").agg(pl.col("total_trips").sum()).sort("Full_Date")
        st.plotly_chart(px.line(daily_trend.to_pandas(), x='Full_Date', y='total_trips', 
                               title="Volume Timeline", template="plotly_dark", color_discrete_sequence=['#FF4B4B']), width="stretch")
    with col2:
        heat_data = data_filtered.group_by(["Day_of_Week_Name", "Hour"]).agg(pl.col("total_trips").sum()).to_pandas()
        heat_pivot = heat_data.pivot(index='Day_of_Week_Name', columns='Hour', values='total_trips').reindex(['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'])
        st.plotly_chart(px.imshow(heat_pivot, color_continuous_scale="Viridis", title="Peak Hour Intensity"), width="stretch")

with tab2:
    st.subheader("🌍 Multi-Service Spatial Distribution")
    service_types = sorted(df["Service_Name"].unique().to_list())
    selected_services = st.multiselect("Compare Vehicle Categories:", options=service_types, default=service_types, key="svc_ms")
    
    # Map Aggregation
    map_data = data_filtered.filter(pl.col("Service_Name").is_in(selected_services)).group_by(["Borough", "Service_Name"]).agg(pl.col("total_trips").sum()).to_pandas()
    map_data = map_data.merge(borough_coordinates, on='Borough', how='inner')
    
    if not map_data.empty:
        fig_map = px.scatter_mapbox(
            map_data, lat="lat", lon="lon", size="total_trips", color="Service_Name",
            zoom=9, height=550, mapbox_style="open-street-map", template="plotly_dark",
            title="NYC Demand Heat-Map (Size by Volume | Color by Service)"
        )
        fig_map.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
        st.plotly_chart(fig_map, width="stretch")
    else:
        st.warning("No data available for the selected filters.")

with tab3:
    st.subheader("Hierarchical Revenue Structure")
    st.plotly_chart(px.sunburst(data_filtered.to_pandas(), path=['Borough', 'Service_Name'], values='total_revenue', 
                               color='total_revenue', color_continuous_scale='YlOrRd', 
                               title="Revenue Distribution: Borough > Category", template="plotly_dark"), width="stretch")

with tab4:
    st.subheader("🔍 Micro-Neighborhood Explorer")
    # Quick metadata fetch for zone list
    client = bigquery.Client()
    project_id = os.getenv("BQ_PROJECT_ID")
    dataset_id = os.getenv("BQ_DATASET_ID", "nyc_taxi_dw")
    zone_list = sorted(client.query(f"SELECT DISTINCT Zone FROM `{project_id}.{dataset_id}.Dim_Location`").to_dataframe()['Zone'].tolist())
    
    target_zone = st.selectbox("Select a Neighborhood to Inspect:", options=zone_list, key="zone_sel")
    if target_zone:
        with st.spinner(f"Analyzing {target_zone} heartbeat..."):
            df_z = load_zone_detail(target_zone)
            if not df_z.empty:
                zc1, zc2 = st.columns(2)
                zc1.metric(f"Total Volume for {target_zone}", f"{df_z['total_demand'].sum():,.0f} trips")
                zc2.plotly_chart(px.pie(df_z, names='Service_Name', values='total_demand', hole=0.5, 
                                       title="Vehicle Mix", template="plotly_dark"), width="stretch")
                st.plotly_chart(px.area(df_z.sort_values('Full_Date'), x='Full_Date', y='total_demand', 
                                       title=f"Demand Waveform: {target_zone}", template="plotly_dark"), width="stretch")
            else:
                st.info("No granular records found for the selected zone.")
