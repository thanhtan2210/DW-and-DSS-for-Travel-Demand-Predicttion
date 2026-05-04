import os
from google.cloud import bigquery as bq
from ..utils.database import get_bq_client

def execute_sql_file(sql_file_path, params=None):
    """Đọc file SQL, thay thế biến và thực thi trên BigQuery."""
    client = get_bq_client()
    
    if not os.path.exists(sql_file_path):
        print(f"   [BQ Engine] ERROR: Không tìm thấy file {sql_file_path}")
        return

    with open(sql_file_path, 'r', encoding='utf-8') as file:
        query = file.read()
    
    # Thay thế các biến môi trường và tham số
    project_id = os.getenv("BQ_PROJECT_ID")
    staging_ds = os.getenv("BQ_STAGING_DATASET_ID", "nyc_taxi_staging")
    dw_ds = os.getenv("BQ_DATASET_ID", "nyc_taxi_dw")
    
    query = query.replace("{{PROJECT_ID}}", project_id)
    query = query.replace("{{STAGING_DATASET}}", staging_ds)
    query = query.replace("{{DW_DATASET}}", dw_ds)
    
    if params:
        for key, value in params.items():
            query = query.replace("{{" + key + "}}", str(value))
    
    print(f"   [BQ Engine] Đang thực thi {os.path.basename(sql_file_path)}...")
    try:
        job = client.query(query)
        job.result() # Đợi truy vấn hoàn tất
        print(f"   [BQ Engine] SUCCESS!")
    except Exception as e:
        print(f"   [BQ Engine] FAILED: {e}")
        raise e
