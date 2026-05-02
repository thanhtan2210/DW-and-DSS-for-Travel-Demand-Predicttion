import pandas as pd
import numpy as np

def engineer_features(data):
    """
    Quy trình Feature Engineering chuẩn xác từ Môi trường Nghiên cứu.
    Được sử dụng chung cho cả Huấn luyện (Train) và Dự báo (Inference).
    """
    df = data.copy()
    
    # 1. Xử lý Thời gian (Temporal Processing)
    df['Datetime'] = pd.to_datetime(df['Time_Key'].astype(str), format='%Y%m%d%H')
    df['Hour'] = df['Datetime'].dt.hour
    
    # Đảm bảo có cột DayOfWeek (Lấy từ Time_Key nếu chưa có)
    if 'DayOfWeek' not in df.columns:
        df['DayOfWeek'] = df['Datetime'].dt.dayofweek
        
    df['Is_Weekend'] = (df['DayOfWeek'] >= 5).astype(int)
    
    # 2. Biến đổi Chu kỳ (Cyclical Encoding) - 24h
    df['hour_sin'] = np.sin(df['Hour'] * (2. * np.pi / 24))
    df['hour_cos'] = np.cos(df['Hour'] * (2. * np.pi / 24))
    
    # 3. Sắp xếp để tính Lag
    # Đảm bảo cột Location có tên chuẩn
    loc_col = 'PULocation_Key' if 'PULocation_Key' in df.columns else 'pulocationid'
    
    df = df.sort_values(by=[loc_col, 'Datetime']).reset_index(drop=True)
    
    # 4. Lag Features (Trí nhớ của mô hình)
    if 'total_demand' in df.columns:
        grouped = df.groupby(loc_col)['total_demand']
        df['lag_1h'] = grouped.shift(1)
        df['lag_2h'] = grouped.shift(2)
        df['lag_24h'] = grouped.shift(24)
        df['lag_168h'] = grouped.shift(168)
        
        # 5. Trung bình trượt (Rolling Window)
        df['rolling_mean_6h'] = grouped.transform(lambda x: x.rolling(window=6, min_periods=1).mean())
        
        # 6. Loại bỏ NaN sinh ra từ Lag
        df = df.dropna(subset=['lag_168h'])
    
    # 7. Xử lý thời tiết (Imputation)
    if 'Temperature' in df.columns:
        df['Temperature'] = df['Temperature'].fillna(df['Temperature'].mean())
    if 'Precipitation' in df.columns:
        df['Precipitation'] = df['Precipitation'].fillna(0)
        
    return df
