# Machine Learning Pipeline Documentation

This document outlines the end-to-end Machine Learning pipeline used for the Travel Demand Prediction project.

### 1. Data Sources
The primary data source is the **Aggregated Fact Table** (`Fact_Demand_Hourly`) stored in Google BigQuery. This table integrates:
- **NYC TLC Trip Records** (Yellow, Green, FHV, FHVHV).
- **Historical Weather Data** (Temperature and Precipitation).

### 2. Data Preprocessing
- **Datetime Parsing:** Converting `pickup_time_key` into granular temporal components.
- **Numerical Downcasting:** Converting 64-bit types to 32-bit to optimize RAM usage during training.
- **Scaling:** Applying `MinMaxScaler` or `StandardScaler` to numerical inputs (Temperature, Precipitation, Lags).

### 3. Feature Engineering (The Demand Heartbeat)
A robust feature set is engineered to capture complex temporal and spatial dynamics:
- **Cyclical Temporal Features:** `hour_sin` and `hour_cos` to ensure the model understands that hour 23 is adjacent to hour 0.
- **Lag Features:** Historical demand at **1h, 2h, 24h (yesterday), and 168h (last week)** prior. These are the strongest predictors of future demand.
- **Exogenous Weather:** Real-time temperature and precipitation impacts on urban mobility.

### 4. Model Selection (Regression Focus)
The project evaluates three distinct approaches to handle non-linear time-series data:
- **XGBoost Regressor:** Advanced gradient boosting, optimized for tabular data with high feature interaction.
- **Random Forest Regressor:** Robust ensemble baseline, excellent for handling outliers.
- **LSTM (Long Short-Term Memory):** Deep learning architecture designed to capture deep sequential dependencies across time.

### 5. Training & Evaluation
- **Chronological Data Splitting:** Training on historical periods and testing on a strictly future "hold-out" set to prevent data leakage.
- **Metrics:** Performance is benchmarked using **RMSE** (penalizes large errors), **MAE** (average magnitude of error), and **R²** (explained variance).

### 6. Deployment & Inference
Post-training, models and scalers are registered in `saved_models/`. The Streamlit `ML_Predictor.py` page loads these artifacts to provide real-time forecasts based on user inputs and fetched weather forecasts.

