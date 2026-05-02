import joblib
import pandas as pd
from .features.build_features import engineer_features

class DemandPredictor:
    """
    Class MLOps chuẩn hóa để gọi Model trong môi trường Production.
    Hỗ trợ Software Engineer tích hợp vào Web/App dễ dàng.
    """
    def __init__(self, model_type='xgboost'):
        self.model_type = model_type
        self.model = self._load_model()
        
        # Danh sách tính năng (Features) bắt buộc phải có khi đưa vào Model
        self.features_cols = [
            'PULocation_Key', 'Hour', 'DayOfWeek', 'Is_Weekend', 'hour_sin', 'hour_cos',
            'lag_1h', 'lag_2h', 'lag_24h', 'lag_168h', 'rolling_mean_6h',
            'Temperature', 'Precipitation'
        ]

    def _load_model(self):
        """Tải mô hình từ đĩa cứng lên RAM."""
        if self.model_type == 'xgboost':
            path = 'saved_models/xgboost/xgb_demand_model_v1.joblib'
        else:
            path = 'saved_models/random_forest/rf_baseline_model.joblib'
            
        try:
            return joblib.load(path)
        except Exception as e:
            raise Exception(f"Không thể tải Model từ {path}. Lỗi: {e}")

    def predict(self, raw_input_df):
        """
        Hàm được gọi bởi Frontend/API.
        Nhận dữ liệu thô -> Tự động tạo đặc trưng -> Dự báo.
        """
        # 1. Đi qua cùng một bộ máy Feature Engineering như lúc Huấn luyện
        # Đảm bảo KHÔNG bao giờ có sự sai lệch logic giữa Train và Prod
        processed_df = engineer_features(raw_input_df)
        
        # 2. Lấy đúng các cột cần thiết
        X_input = processed_df[self.features_cols]
        
        # 3. Trả về kết quả dự báo
        predictions = self.model.predict(X_input)
        
        return predictions

# Ví dụ cách sử dụng (Inference Code)
if __name__ == "__main__":
    print("Khởi tạo API Dự báo...")
    predictor = DemandPredictor(model_type='xgboost')
    print("Sẵn sàng nhận dữ liệu!")
