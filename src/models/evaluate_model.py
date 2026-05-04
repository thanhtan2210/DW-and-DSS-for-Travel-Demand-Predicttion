import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error

def segmented_evaluation(y_true, y_pred, df_test):
    """
    Performs multi-dimensional model evaluation across spatial and temporal segments.
    Provides targeted error analysis for specific business domains (e.g., High-Demand vs Low-Demand).
    """
    results = df_test.copy()
    results['actual'] = y_true
    results['prediction'] = y_pred
    results['error'] = np.abs(results['actual'] - results['prediction'])
    
    # 1. Global Metrics (System-wide performance)
    total_rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    print(f"--- GLOBAL PERFORMANCE METRICS ---")
    print(f"Total RMSE: {total_rmse:.2f}")
    
    # 2. Spatial Segmentation (Evaluating high-volume vs peripheral performance)
    if 'borough' in results.columns:
        manhattan_mask = results['borough'] == 'Manhattan'
        manhattan = results[manhattan_mask]
        others = results[~manhattan_mask]
        
        rmse_m = np.sqrt(mean_squared_error(manhattan['actual'], manhattan['prediction']))
        rmse_o = np.sqrt(mean_squared_error(others['actual'], others['prediction']))
        
        print(f"\n--- SPATIAL SEGMENT ANALYSIS ---")
        print(f"RMSE Manhattan (High Volume Area): {rmse_m:.2f}")
        print(f"RMSE Peripheral Boroughs: {rmse_o:.2f}")
    
    # 3. Temporal Segmentation (Evaluating Peak vs Off-Peak robustness)
    if 'is_rush_hour' in results.columns:
        rush_mask = results['is_rush_hour'] == True
        rush = results[rush_mask]
        normal = results[~rush_mask]
        
        rmse_r = np.sqrt(mean_squared_error(rush['actual'], rush['prediction']))
        rmse_n = np.sqrt(mean_squared_error(normal['actual'], normal['prediction']))
        
        print(f"\n--- TEMPORAL SEGMENT ANALYSIS ---")
        print(f"RMSE Peak Hours (Rush): {rmse_r:.2f}")
        print(f"RMSE Normal Operating Hours: {rmse_n:.2f}")

    return total_rmse
