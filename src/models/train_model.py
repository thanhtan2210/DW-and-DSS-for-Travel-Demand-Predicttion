import pandas as pd
import numpy as np
import joblib
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error
from ..features.build_features import create_lag_features

def time_series_split(df, split_time_key=2025110100):
    """
    Chia dữ liệu theo thời gian để tránh rò rỉ dữ liệu.
    Mặc định: Trước tháng 11 là Train, từ tháng 11 là Test.
    """
    train = df[df['pickup_time_key'] < split_time_key]
    test = df[df['pickup_time_key'] >= split_time_key]
    from .evaluate_model import segmented_evaluation
    from ..features.build_features import create_lag_features, create_temporal_features

    def train_and_save(df, model_name='xgb_demand_v1'):
        """Quy trình huấn luyện nâng cao: Cyclical Features + Segmented Eval."""

        # 1. Feature Engineering (Lags + Cyclical)
        df = create_lag_features(df)
        df = create_temporal_features(df)

        # 2. Split (Time-based)
        train, test = time_series_split(df)

        # Định nghĩa danh sách features mới (bao gồm Sine/Cosine)
        features = [c for c in df.columns if 'lag_' in c] + \
                   ['hour_sin', 'hour_cos', 'day_sin', 'day_cos']
        target = 'total_demand'

        X_train, y_train = train[features], train[target]
        X_test, y_test = test[features], test[target]

        # 3. Target Transformation (Log1p)
        y_train_log = np.log1p(y_train)

        # 4. Train
        model = XGBRegressor(n_estimators=200, max_depth=8, learning_rate=0.05)
        model.fit(X_train, y_train_log)

        # 5. Segmented Evaluation
        preds_log = model.predict(X_test)
        preds = np.expm1(preds_log)

        segmented_evaluation(y_test, preds, test)

        # 6. Save Artifacts
        joblib.dump(model, f'saved_models/xgboost/{model_name}.joblib')

        return model

