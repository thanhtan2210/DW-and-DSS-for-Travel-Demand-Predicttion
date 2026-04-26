import os
from ..utils.database import get_bq_client, get_bq_config

def load_parquet_to_bq(file_path, category, is_raw=False):
    """Nạp file Parquet lên BigQuery (Hỗ trợ Raw hoặc Cleaned)."""
    client = get_bq_client()
    table_id, job_config = get_bq_config(category, is_raw=is_raw)
    
    with open(file_path, "rb") as source_file:
        file_name = os.path.basename(file_path)
        tag = "[RAW]" if is_raw else "[CLEANED]"
        print(f"   {tag} Đang đẩy {file_name} -> {table_id}...")
        
        job = client.load_table_from_file(source_file, table_id, job_config=job_config)
        job.result()  # Đợi nạp xong
        
    print(f"   {tag} SUCCESS! Đã nạp xong {file_name}")
