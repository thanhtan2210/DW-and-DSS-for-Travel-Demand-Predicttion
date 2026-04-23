import os
import pandas as pd
from google.cloud import bigquery as bq
from ..utils.database import get_bq_client

def load_dim_location_to_bq(csv_path):
    """Nạp bảng DimLocation lên BigQuery từ file CSV lookup."""
    client = get_bq_client()
    project_id = os.getenv("BQ_PROJECT_ID")
    dataset_id = os.getenv("BQ_DATASET_ID")
    table_id = f"{project_id}.{dataset_id}.DimLocation"
    
    df = pd.read_csv(csv_path)
    df.columns = ['locationid', 'borough', 'zone', 'service_zone']
    
    job_config = bq.LoadJobConfig(write_disposition="WRITE_APPEND") # Hoặc TRUNCATE nếu muốn làm mới
    client.load_table_from_dataframe(df, table_id, job_config=job_config).result()
    print(f"[BQ] DimLocation nạp thành công.")

def load_dim_time_to_bq(start_date='2025-06-01', end_date='2025-11-30'):
    """Tạo và nạp bảng DimTime lên BigQuery cho dải thời gian dự án."""
    client = get_bq_client()
    project_id = os.getenv("BQ_PROJECT_ID")
    dataset_id = os.getenv("BQ_DATASET_ID")
    table_id = f"{project_id}.{dataset_id}.DimTime"
    
    dates = pd.date_range(start_date, end_date, freq='h')
    dim_time = pd.DataFrame({
        'time_key': dates.strftime('%Y%m%d%H').astype(int),
        'full_datetime': dates,
        'hour': dates.hour,
        'day': dates.day,
        'month': dates.month,
        'year': dates.year,
        'day_of_week': dates.dayofweek + 1,
        'is_weekend': (dates.dayofweek >= 5).astype(int)
    })
    
    job_config = bq.LoadJobConfig(write_disposition="WRITE_APPEND")
    client.load_table_from_dataframe(dim_time, table_id, job_config=job_config).result()
    print(f"[BQ] DimTime nạp thành công: {len(dim_time)} dòng.")
