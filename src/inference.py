import os
import joblib
import pandas as pd
import numpy as np
from .features.build_features import engineer_features

class DemandPredictor:
    """
    Standardized MLOps Predictor class for production environments.
    Automates tensor reshaping and feature scaling for tree-based and deep learning models.
    """
    def __init__(self, model_type='xgboost'):
        self.model_type = model_type
        self.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
        self.model = self._load_model()
        
        # Required input features for tree-based models (XGBoost/RandomForest)
        self.features_cols = [
            'PULocation_Key', 'Hour', 'DayOfWeek', 'Is_Weekend', 'hour_sin', 'hour_cos',
            'lag_1h', 'lag_2h', 'lag_24h', 'lag_168h', 'rolling_mean_6h',
            'Temperature', 'Precipitation'
        ]
        
        # Required input features for Deep Learning (LSTM)
        self.lstm_features = ['total_demand', 'Hour', 'DayOfWeek']
        
        # Load specialized scaler for neural network inputs
        if self.model_type == 'lstm':
            scaler_path = os.path.join(self.root_dir, 'saved_models/scalers/lstm_scaler.pkl')
            self.scaler = joblib.load(scaler_path)

    def _load_model(self):
        """Retrieves serialized model artifacts from the 'saved_models/' directory."""
        try:
            if self.model_type == 'xgboost':
                path = os.path.join(self.root_dir, 'saved_models/xgboost/xgb_demand_model_v1.joblib')
                return joblib.load(path)
            elif self.model_type == 'random_forest':
                path = os.path.join(self.root_dir, 'saved_models/random_forest/rf_baseline_model.joblib')
                return joblib.load(path)
            elif self.model_type == 'lstm':
                import tensorflow as tf
                path = os.path.join(self.root_dir, 'saved_models/lstm/lstm_demand_model_v1.keras')
                return tf.keras.models.load_model(path)
        except Exception as e:
            raise Exception(f"Initialization failure for model '{self.model_type}'. Trace: {e}")

    def predict(self, raw_input_df):
        """
        Executes model inference.
        Handles internal data transformations to ensure compatibility with model input layers.
        """
        if self.model_type == 'lstm':
            # 1. Feature extraction
            data = raw_input_df[self.lstm_features].values
            # 2. Scaling
            scaled_data = self.scaler.transform(data)
            # 3. 3D Tensor Reshaping [Batch, TimeSteps, Features]
            # Simulate 24-hour historical window by repeating current state
            input_3d = np.repeat(scaled_data[np.newaxis, :, :], 24, axis=1)
            
            # 4. Neural Network Inference
            pred_scaled = self.model.predict(input_3d, verbose=0)
            
            # 5. Inverse scaling to raw demand units
            temp_df = np.zeros((1, len(self.lstm_features)))
            temp_df[0, 0] = pred_scaled[0, 0]
            prediction = self.scaler.inverse_transform(temp_df)[0, 0]
            return [prediction]
        else:
            # Standard tree-based inference
            X_input = raw_input_df[self.features_cols]
            return self.model.predict(X_input)

if __name__ == "__main__":
    print("Inference engine ready for deployment.")
