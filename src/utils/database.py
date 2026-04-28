import os
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()

def get_bq_client():
    """Tạo client BigQuery dựa trên Project ID từ biến môi trường."""
    project_id = os.getenv("BQ_PROJECT_ID")
    return bigquery.Client(project=project_id)

def get_bq_config(category, is_raw=False):
    """Lấy cấu hình nạp dữ liệu lên BigQuery (Hỗ trợ cả Raw và Cleaned)."""
    project_id = os.getenv("BQ_PROJECT_ID")
    # Lựa chọn Dataset ID dựa trên loại dữ liệu
    if is_raw:
        dataset_id = os.getenv("BQ_DATASET_ID", "nyc_taxi_raw")
        table_id = f"{project_id}.{dataset_id}.raw_{category}"
    else:
        dataset_id = os.getenv("BQ_CLEANED_DATASET_ID", "nyc_taxi_cleaned")
        table_id = f"{project_id}.{dataset_id}.clean_{category}"
    
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.PARQUET,
        write_disposition="WRITE_APPEND",
        autodetect=True,
        # Cho phép tự động thêm cột mới nếu Schema thay đổi
        schema_update_options=[
            bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION,
            bigquery.SchemaUpdateOption.ALLOW_FIELD_RELAXATION
        ],
    )
    return table_id, job_config
