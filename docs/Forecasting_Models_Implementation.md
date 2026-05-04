# Machine Learning Forecasting: Implementation & MLOps Strategy

This document outlines the workflow for training and deploying forecasting models using cleaned data from Google BigQuery, specifically designed for systems with limited RAM.

---

## 1. Data Acquisition (BigQuery to Python)
To ensure high-quality predictions, always pull data from the **Aggregated Fact Table** (`Fact_Demand_Hourly`) which has already been processed by the SQL engine.

### Python Code to Fetch Data:
```python
from google.cloud import bigquery
import pandas as pd

client = bigquery.Client()
query = """
SELECT 
    f.*, 
    t.Is_Rush_Hour, t.Is_Weekend, t.Shift_Name, t.Day_of_Week_Number,
    w.Temperature, w.Precipitation
FROM `{{PROJECT_ID}}.{{DW_DATASET}}.Fact_Demand_Hourly` f
LEFT JOIN `{{PROJECT_ID}}.{{DW_DATASET}}.Dim_Time` t ON f.pickup_time_key = t.Time_Key
LEFT JOIN `{{PROJECT_ID}}.{{DW_DATASET}}.Dim_Weather` w ON f.pickup_time_key = w.Weather_Key
WHERE f.pickup_time_key BETWEEN 2025060100 AND 2025113023
"""
df = client.query(query).to_dataframe()
```

---

## 2. RAM Optimization Strategy (Memory-Safe MLOps)

### 2.1. Numerical Downcasting
Reduce RAM usage by 60%+ by compressing data types immediately after loading:
```python
def optimize_memory(df):
    for col in df.select_dtypes(include=['float64']).columns:
        df[col] = df[col].astype('float32')
    for col in df.select_dtypes(include=['int64']).columns:
        df[col] = df[col].astype('int32')
    import gc
    gc.collect()
    return df

df = optimize_memory(df)
```

### 2.2. Selective Training (Top Zones)
If processing all 265 zones causes a crash, filter for the top 50 zones by volume:
```python
top_zones = df.groupby('pulocation_id')['total_demand'].sum().nlargest(50).index
df_filtered = df[df['pulocation_id'].is_in(top_zones)]
```

---

## 3. Model Persistence (Artifact Storage)
Always save both the **Model** and the **Scaler** to ensure prediction consistency.

| Artifact Type | Storage Location | Recommended Library |
| :--- | :--- | :--- |
| Pre-processing Scalers | `saved_models/scalers/` | `joblib` |
| Tree Models (XGB/RF) | `saved_models/xgboost/` | `joblib` |
| Deep Learning (LSTM) | `saved_models/lstm/` | `keras` (Native) |

---

## 4. Operational Workflow (The Training Loop)
1.  **Extract**: Pull `Fact_Demand_Hourly` from BigQuery.
2.  **Clean/Pre-process**: 
    - Convert Categorical features (`Shift_Name`) to One-Hot encoding.
    - Scale numerical features using `MinMaxScaler`.
3.  **Train**: Execute XGBoost, Random Forest, or LSTM.
4.  **Validate**: Use **Time-Based Splitting** (Train on Jun-Oct, Test on Nov).
5.  **Save**: Export `.joblib` or `.keras` artifacts to the `saved_models/` directory.

---

## 5. Future Inference
To predict demand for new dates, load the saved artifacts from the `saved_models/` directory and apply them to newly fetched weather/time features without retraining.
