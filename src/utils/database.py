import os
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()

def get_bq_client():
    """Initializes a BigQuery client using the Project ID from environment variables."""
    project_id = os.getenv("BQ_PROJECT_ID")
    return bigquery.Client(project=project_id)

def get_bq_config(category, is_raw=False):
    """
    Constructs the BigQuery table ID and load configuration based on the data tier.
    
    Args:
        category (str): The vehicle category (e.g., 'yellow', 'green').
        is_raw (bool): If True, targets the Staging area. If False, targets the Data Warehouse.
        
    Returns:
        tuple: (table_id, job_config)
    """
    project_id = os.getenv("BQ_PROJECT_ID")
    
    if is_raw:
        # TIER 1: Raw Data -> Staging Dataset (Immutable source)
        dataset_id = os.getenv("BQ_STAGING_DATASET_ID", "nyc_taxi_staging")
        table_id = f"{project_id}.{dataset_id}.raw_{category}"
    else:
        # TIER 2: Cleaned Data -> Production DW Dataset (Star Schema)
        dataset_id = os.getenv("BQ_DATASET_ID", "nyc_taxi_dw")
        # Route cleaned data to the unified Fact tables
        table_name = "Fact_Trips" if "agg" not in category else "Fact_Demand_Hourly"
        table_id = f"{project_id}.{dataset_id}.{table_name}"

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.PARQUET,
        autodetect=True,
        write_disposition="WRITE_APPEND",
        # Enable schema evolution for the Wide Fact Table strategy
        schema_update_options=[
            bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION,
            bigquery.SchemaUpdateOption.ALLOW_FIELD_RELAXATION
        ],
    )
    return table_id, job_config
