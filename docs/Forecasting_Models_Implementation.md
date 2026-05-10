# Machine Learning Forecasting: Implementation & MLOps Strategy

This document outlines the workflow for training and deploying forecasting models using aggregated data from Google BigQuery.

---

## 1. Data Acquisition (BigQuery to Python)
To ensure high-quality predictions, always pull data from the **Aggregated Fact Table** (`Fact_Demand_Hourly`).

### Python Code to Fetch Data:
```python
query = """
SELECT 
    f.*, 
    t.Hour, t.Day_of_Week_Number, t.Is_Weekend,
    w.Temperature, w.Precipitation
FROM `{{PROJECT_ID}}.{{DW_DATASET}}.Fact_Demand_Hourly` f
LEFT JOIN `{{PROJECT_ID}}.{{DW_DATASET}}.Dim_Time` t ON f.pickup_time_key = t.Time_Key
LEFT JOIN `{{PROJECT_ID}}.{{DW_DATASET}}.Dim_Weather` w ON f.pickup_time_key = w.Weather_Key
"""
df = client.query(query).to_dataframe()
```

---

## 2. RAM Optimization Strategy (Memory-Safe MLOps)

### 2.1. Numerical Downcasting
Reduce RAM usage by 60%+ by compressing data types immediately after loading. This is critical for handling multi-zone time-series data:
```python
def optimize_memory(df):
    for col in df.select_dtypes(include=['float64']).columns:
        df[col] = df[col].astype('float32')
    for col in df.select_dtypes(include=['int64']).columns:
        df[col] = df[col].astype('int32')
    import gc; gc.collect()
    return df

df = optimize_memory(df)
```

---

## 3. Model Persistence (Artifact Registry)
The system persists models and their corresponding scaling artifacts to ensure mathematical consistency during inference.

| Model Type | Extension | Scaler Required? | Path |
| :--- | :--- | :--- | :--- |
| **XGBoost** | `.joblib` | Yes | `saved_models/xgboost/` |
| **Random Forest**| `.joblib` | Yes | `saved_models/random_forest/` |
| **LSTM** | `.keras` | Yes | `saved_models/lstm/` |
| **Scalers** | `.pkl` | N/A | `saved_models/scalers/` |

---

## 4. Evaluation Strategy
1.  **Time-Based Splitting**: Preserves chronological order (e.g., Train on June-October, Test on November).
2.  **Lag-Feature Engineering**: Models consume historical "heartbeats" (1h, 2h, 24h, 168h lags) to capture short and long-term seasonality.
3.  **Metrics**: Evaluation is conducted via RMSE, MAE, and R² Score.
