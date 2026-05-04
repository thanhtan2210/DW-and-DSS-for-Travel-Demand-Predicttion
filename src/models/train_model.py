import os
import pandas as pd
import numpy as np
import joblib
from google.cloud import bigquery
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from dotenv import load_dotenv

from ..features.build_features import engineer_features

def fetch_data_from_bq():
    """Tự động kéo dữ liệu sạch từ BigQuery."""
    load_dotenv('../.env')
    client = bigquery.Client()
    project_id = os.getenv("BQ_PROJECT_ID")
    dataset_id = os.getenv("BQ_DATASET_ID", "nyc_taxi_dw")

    query = f"""
    SELECT 
        f.pickup_time_key as Time_Key, 
        f.pulocationid as PULocation_Key, 
        f.total_demand,
        w.Temperature,
        w.Precipitation
    FROM `{project_id}.{dataset_id}.Fact_Demand_Hourly` f
    LEFT JOIN `{project_id}.{dataset_id}.Dim_Weather` w ON f.pickup_time_key = w.Weather_Key
    WHERE f.service_type_key = 1
    ORDER BY PULocation_Key, Time_Key
    """
    print(">>> Kéo dữ liệu từ BigQuery...")
    return client.query(query).to_dataframe()

def evaluate_model(model_name, y_true, y_pred):
    """In ra các chỉ số đánh giá."""
    print(f"--- Kết quả {model_name} ---")
    print(f"RMSE: {np.sqrt(mean_squared_error(y_true, y_pred)):.2f}")
    print(f"MAE:  {mean_absolute_error(y_true, y_pred):.2f}")
    print(f"R2 Score: {r2_score(y_true, y_pred):.2f}\n")

def run_automated_training():
    """Luồng MLOps: Tự động hóa quá trình huấn luyện và lưu trữ."""
    
    # 1. Lấy dữ liệu
    df_raw = fetch_data_from_bq()
    
    # 2. Kỹ thuật Đặc trưng (Sử dụng chung hàm với Inference)
    df_features = engineer_features(df_raw)
    
    # 3. Chia tập Train/Test theo mốc thời gian
    train_df = df_features[df_features['Datetime'] < '2025-11-01']
    test_df = df_features[df_features['Datetime'] >= '2025-11-01']

    features_cols = [
        'PULocation_Key', 'Hour', 'DayOfWeek', 'Is_Weekend', 'hour_sin', 'hour_cos',
        'lag_1h', 'lag_2h', 'lag_24h', 'lag_168h', 'rolling_mean_6h'
    ]
    if 'Temperature' in df_features.columns:
        features_cols.extend(['Temperature', 'Precipitation'])

    target_col = 'total_demand'

    X_train, y_train = train_df[features_cols], train_df[target_col]
    X_test, y_test = test_df[features_cols], test_df[target_col]
    
    print(f"Kích thước Train: {len(X_train)} | Test: {len(X_test)}")

    # 4. Huấn luyện Random Forest (Baseline)
    print(">>> Huấn luyện Random Forest...")
    rf_model = RandomForestRegressor(n_estimators=50, max_depth=10, random_state=42, n_jobs=-1)
    rf_model.fit(X_train, y_train)
    rf_preds = rf_model.predict(X_test)
    evaluate_model("Random Forest", y_test, rf_preds)

    # 5. Huấn luyện XGBoost (Advanced)
    print(">>> Huấn luyện XGBoost...")
    xgb_model = XGBRegressor(n_estimators=200, learning_rate=0.05, max_depth=7, subsample=0.8, random_state=42, n_jobs=-1)
    xgb_model.fit(X_train, y_train)
    xgb_preds = xgb_model.predict(X_test)
    evaluate_model("XGBoost", y_test, xgb_preds)

    # 6. Lưu trữ Model (MLOps Artifacts)
    os.makedirs('../saved_models/random_forest', exist_ok=True)
    os.makedirs('../saved_models/xgboost', exist_ok=True)
    
    joblib.dump(rf_model, '../saved_models/random_forest/rf_baseline_model.joblib')
    joblib.dump(xgb_model, '../saved_models/xgboost/xgb_demand_model_v1.joblib')
    
    print(">>> [MLOps] Đã lưu mô hình thành công vào thư mục saved_models/")

if __name__ == "__main__":
    run_automated_training()
