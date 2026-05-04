# System Architecture

## Overview
The architecture of the NYC Taxi Trip Data Warehouse and Decision Support System is designed to be highly scalable, modular, and automated. It integrates robust data engineering pipelines with advanced machine learning capabilities to forecast travel demand.

## Components
1. **Data Sources**: 
    - NYC TLC Trip Record Data (Parquet).
    - Weather Data (CSV/API).
    - Spatial lookup tables and maps.

2. **Data Warehouse (BigQuery)**:
    - Centralized storage for structured data (dimensional modeling with Fact and Dimension tables).

3. **ETL / Data Pipeline**:
    - **Extract**: Ingesting raw data using local extraction and API fetchers.
    - **Transform**: Polars/Pandas-based processing for cleaning, handling anomalies, and aggregating data.
    - **Load**: Pushing clean data into BigQuery.

4. **Machine Learning Pipeline**:
    - Queries processed historical data from BigQuery.
    - Applies feature engineering (temporal, cyclical, lag features).
    - Trains multiple algorithms (Random Forest, XGBoost, LSTM).
    - Persists best models as artifacts for inference.

5. **Presentation / Decision Support**:
    - Streamlit web application (`app/main.py`) for interactive forecasting and visualizations.
    - PowerBI Dashboard (`visual/nyc-dss.pbix`) for enterprise reporting.
