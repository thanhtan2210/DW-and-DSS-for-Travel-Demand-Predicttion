import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error

def segmented_evaluation(y_true, y_pred, df_test):
    """
    Đánh giá mô hình chi tiết theo Phân khúc: Khu vực và Thời gian.
    """
    results = df_test.copy()
    results['actual'] = y_true
    results['prediction'] = y_pred
    results['error'] = np.abs(results['actual'] - results['prediction'])
    
    # 1. RMSE Tổng quát
    total_rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    print(f"--- GLOBAL METRICS ---")
    print(f"Total RMSE: {total_rmse:.2f}")
    
    # 2. RMSE theo Khu vực (Manhattan vs Others)
    # Giả sử borough được lấy từ Dim_Location khi JOIN
    if 'borough' in results.columns:
        manhattan = results[results['borough'] == 'Manhattan']
        others = results[results['borough'] != 'Manhattan']
        
        rmse_m = np.sqrt(mean_squared_error(manhattan['actual'], manhattan['prediction']))
        rmse_o = np.sqrt(mean_squared_error(others['actual'], others['prediction']))
        
        print(f"\n--- SPATIAL SEGMENTS ---")
        print(f"RMSE Manhattan (High Demand): {rmse_m:.2f}")
        print(f"RMSE Other Boroughs (Low Demand): {rmse_o:.2f}")
    
    # 3. RMSE theo Giờ (Rush Hour vs Normal)
    if 'is_rush_hour' in results.columns:
        rush = results[results['is_rush_hour'] == True]
        normal = results[results['is_rush_hour'] == False]
        
        rmse_r = np.sqrt(mean_squared_error(rush['actual'], rush['prediction']))
        rmse_n = np.sqrt(mean_squared_error(normal['actual'], normal['prediction']))
        
        print(f"\n--- TEMPORAL SEGMENTS ---")
        print(f"RMSE Rush Hour: {rmse_r:.2f}")
        print(f"RMSE Normal Hours: {rmse_n:.2f}")

    return total_rmse
