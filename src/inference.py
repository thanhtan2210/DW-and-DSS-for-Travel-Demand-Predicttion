import joblib
import os
import pandas as pd
from google.cloud import bigquery
from .utils.database import get_bq_client

def load_prediction_artifacts(model_type='xgboost'):
    """Tải bộ Scaler và Model từ thư mục saved_models."""
    scaler_path = 'saved_models/scalers/minmax_scaler.pkl'
    
    if model_type == 'xgboost':
        model_path = 'saved_models/xgboost/xgb_demand_model_v1.joblib'
    elif model_type == 'random_forest':
        model_path = 'saved_models/random_forest/rf_baseline_model.joblib'
    else:
        raise ValueError("Model type not supported in this script yet.")

    scaler = joblib.load(scaler_path)
    model = joblib.load(model_path)
    
    return scaler, model

def predict_demand(input_features, model_type='xgboost'):
    """Thực hiện dự báo nhu cầu dựa trên dữ liệu đầu vào."""
    scaler, model = load_prediction_artifacts(model_type)
    
    # Scale dữ liệu mới dựa trên hệ số của dữ liệu training cũ
    scaled_features = scaler.transform(input_features)
    
    # Dự báo
    predictions = model.predict(scaled_features)
    return predictions

if __name__ == "__main__":
    print("Inference module ready. Load models from 'saved_models/' to start predicting.")
