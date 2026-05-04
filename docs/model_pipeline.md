# Machine Learning Pipeline Documentation

This document outlines the end-to-end Machine Learning pipeline used for the Travel Demand Prediction project.

### 1. Data Sources
The primary data source is the **NYC TLC Trip Record dataset** (comprising various taxi types) stored locally as Parquet files or fetched via BigQuery. Supplementary data includes **Weather data** (`nyc_weather_2025.csv`) which provides Temperature and Precipitation features.

### 2. Data Preprocessing
Preprocessing ensures high-quality input for models:
- **Datetime Parsing:** Converting raw timestamp strings into datetime objects.
- **Missing Value Imputation:** Null temperatures are filled with the dataset's mean, while null precipitation is filled with 0.
- **Row Dropping:** Null values generated from lagging operations (e.g., `lag_168h`) are dropped to avoid training on incomplete historical contexts.

### 3. Feature Extraction & Engineering
A robust set of features is generated to capture complex temporal dynamics:
- **Temporal Features:** `Hour`, `DayOfWeek`, `Is_Weekend`.
- **Cyclical Features:** `hour_sin`, `hour_cos` to represent the cyclical nature of time continuously.
- **Lag Features:** Historical demand at 1 hour (`lag_1h`), 2 hours (`lag_2h`), 24 hours (`lag_24h`), and 168 hours (`lag_168h`) prior.
- **Rolling Aggregations:** A 6-hour moving average (`rolling_mean_6h`) to capture short-term trends.

### 4. Classification
*Note: The problem addressed in this project is estimating the continuous value of future trip demand. Therefore, it is structured as a **Regression / Time-Series Forecasting** problem, and Classification techniques are not applicable here.*

### 5. Model Selection
We implemented and evaluated three distinct regression approaches:
- **Random Forest Regressor:** A robust baseline tree-based ensemble.
- **XGBoost Regressor:** An advanced gradient boosting model optimized for tabular data.
- **LSTM (Long Short-Term Memory):** A Recurrent Neural Network architecture specifically designed to capture deep sequential dependencies.

### 6. Training
- **Data Splitting:** A chronological split is utilized to prevent data leakage (e.g., training on data prior to November 2025, and testing on data from November 2025 onwards).
- **Execution:** Models are trained using `scikit-learn` and `xgboost` APIs for tree ensembles, and `TensorFlow/Keras` with `TimeseriesGenerator` for LSTM.
- **Evaluation Metrics:** Root Mean Squared Error (RMSE), Mean Absolute Error (MAE), and R² Score are used to benchmark performance.

### 7. Artifacts and Model Registry
Post-training, the best parameters and configurations are persistently stored in the `saved_models/` directory:
- Tree-based models (Random Forest, XGBoost) and scalers are saved using `joblib` (`.joblib`, `.pkl`).
- The LSTM model architecture and weights are saved in the modern Keras format (`.keras`).

### 8. Clustering
*Note: No clustering algorithms (such as K-Means or DBSCAN) have been employed in this version of the pipeline. The current focus is strictly on supervised forecasting.*
