import pandas as pd
import numpy as np

def create_lag_features(df, lags=[1, 2, 24, 168]):
    """
    Tạo các biến trễ (Lag) cho cột demand.
    1h trước, 2h trước, 1 ngày trước (24h), 1 tuần trước (168h).
    """
    df = df.sort_values(['pulocation_id', 'pickup_time_key'])
    
    for lag in lags:
        df[f'lag_demand_{lag}h'] = df.groupby('pulocation_id')['total_demand'].shift(lag)
    
    # Loại bỏ các dòng Null do không có dữ liệu trễ
    return df.dropna()

def create_temporal_features(df):
    """Làm giàu dữ liệu thời gian và biến đổi Chu kỳ (Cyclical Features)."""
    # Giả sử pickup_time_key có dạng YYYYMMDDHH
    df['hour'] = (df['pickup_time_key'] % 100).astype(int)
    
    # Biến đổi Chu kỳ cho Giờ (24h)
    df['hour_sin'] = np.sin(df['hour'] * (2. * np.pi / 24))
    df['hour_cos'] = np.cos(df['hour'] * (2. * np.pi / 24))
    
    # Biến đổi Chu kỳ cho Thứ (7 ngày)
    if 'day_of_week_number' in df.columns:
        df['day_sin'] = np.sin(df['day_of_week_number'] * (2. * np.pi / 7))
        df['day_cos'] = np.cos(df['day_of_week_number'] * (2. * np.pi / 7))
        
    return df
