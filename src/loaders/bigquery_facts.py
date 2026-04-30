import os
from google.cloud import bigquery as bq
from ..utils.database import get_bq_client, get_bq_config

def load_to_fact_trips(file_path):
    """Nạp dữ liệu chi tiết vào bảng Fact_Trips trong DW."""
    client = get_bq_client()
    # Sử dụng config chuẩn để lấy Table ID
    table_id, job_config = get_bq_config("trips", is_raw=False)
    
    # Đảm bảo Dataset tồn tại
    dataset_ref = ".".join(table_id.split(".")[:2])
    client.create_dataset(dataset_ref, exists_ok=True)
    
    with open(file_path, "rb") as source_file:
        job = client.load_table_from_file(source_file, table_id, job_config=job_config)
        job.result()
    
    print(f"   [BQ] DW: Fact_Trips <- {os.path.basename(file_path)}")

def load_to_fact_demand_hourly(file_path):
    """Nạp dữ liệu tổng hợp vào bảng Fact_Demand_Hourly trong DW."""
    client = get_bq_client()
    # Sử dụng category có chứa 'agg' để get_bq_config chọn đúng bảng
    table_id, job_config = get_bq_config("agg_demand", is_raw=False)
    
    with open(file_path, "rb") as source_file:
        job = client.load_table_from_file(source_file, table_id, job_config=job_config)
        job.result()
    
    print(f"   [BQ] DW: Fact_Demand_Hourly <- {os.path.basename(file_path)}")
