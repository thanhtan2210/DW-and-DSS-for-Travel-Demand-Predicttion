# System Architecture

## Overview
The architecture of the NYC Taxi Trip Data Warehouse and Decision Support System is designed to be highly scalable, modular, and automated. It integrates robust data engineering pipelines with advanced machine learning capabilities to forecast travel demand using a hybrid Local/Cloud approach.

## Components
1. **Data Sources**: 
    - **NYC TLC Trip Record Data**: Historical and current taxi/FHV trip data in Parquet format.
    - **Weather Data**: Historical CSV data (`nyc_weather_2025.csv`) and real-time/forecasted weather via API or CSV (`weather_data_20260507.csv`).
    - **Spatial Lookup Tables**: Official Taxi Zone maps and coordinate mappings for geospatial visualization.

2. **Data Warehouse (Google BigQuery)**:
    - Centralized storage using a Star Schema.
    - **Fact Tables**: `Fact_Trips` (transactional) and `Fact_Demand_Hourly` (aggregated).
    - **Dimension Tables**: `Dim_Time`, `Dim_Location`, `Dim_Service_Type`, and `Dim_Weather`.

3. **Hybrid ETL / ELT Pipeline**:
    - **Local Engine (Polars)**: Utilizes the Polars Streaming API for memory-efficient cleaning and aggregation on local hardware. Uses a "Two-Pass" strategy to avoid RAM overflow.
    - **Cloud Engine (BigQuery)**: Utilizes SQL-based ELT for massive scalability, transforming raw data directly within the warehouse.
    - **Standardization**: Enforces a unified "Gold Schema" across Yellow, Green, FHV, and FHVHV datasets.

4. **Machine Learning Pipeline**:
    - Queries `Fact_Demand_Hourly` from BigQuery.
    - Applies feature engineering including temporal (cyclical), lag-based, and weather-exogenous features.
    - Trains and evaluates Ensemble models (**Random Forest**, **XGBoost**) and Deep Learning (**LSTM**).
    - Persists models and scalers as artifacts in `saved_models/` for real-time inference.

5. **Decision Support Systems (DSS)**:
    - **Streamlit Application**: 
        - `1_OLAP_Dashboard.py`: Interactive temporal, spatial, and financial analysis.
        - `2_ML_Predictor.py`: Real-time demand forecasting using trained ML models.
        - `3_Model_Performance.py`: Model evaluation metrics and feature importance.
        - `4_Data_Health_Monitor.py`: Pipeline auditing and data quality tracking.
    - **PowerBI Dashboard**: High-level executive reporting and advanced DAX-based time-intelligence analysis.
