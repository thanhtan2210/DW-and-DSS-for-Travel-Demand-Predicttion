import os
from google.cloud import bigquery as bq
from ..utils.database import get_bq_client, get_bq_config

def load_to_fact_trips(file_path):
    """
    Materializes detailed trip data into the Fact_Trips table within the Data Warehouse.
    
    Args:
        file_path (str): Absolute path to the cleaned Parquet file.
    """
    client = get_bq_client()
    # Retrieve standardized table configuration
    table_id, job_config = get_bq_config("trips", is_raw=False)
    
    # Ensure the destination Production dataset exists
    dataset_ref = ".".join(table_id.split(".")[:2])
    client.create_dataset(dataset_ref, exists_ok=True)
    
    with open(file_path, "rb") as source_file:
        job = client.load_table_from_file(source_file, table_id, job_config=job_config)
        job.result() # Wait for job completion
    
    print(f"   [BQ] Production DW: Fact_Trips successfully updated from {os.path.basename(file_path)}")

def load_to_fact_demand_hourly(file_path):
    """
    Materializes aggregated hourly demand data into the Fact_Demand_Hourly table (Feature Store).
    
    Args:
        file_path (str): Absolute path to the aggregated Parquet file.
    """
    client = get_bq_client()
    # Route to the aggregated grain table
    table_id, job_config = get_bq_config("agg_demand", is_raw=False)
    
    with open(file_path, "rb") as source_file:
        job = client.load_table_from_file(source_file, table_id, job_config=job_config)
        job.result()
    
    print(f"   [BQ] Production DW: Fact_Demand_Hourly successfully updated from {os.path.basename(file_path)}")
