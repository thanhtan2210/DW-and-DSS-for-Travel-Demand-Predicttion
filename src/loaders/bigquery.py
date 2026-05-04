import os
from ..utils.database import get_bq_client, get_bq_config

def load_parquet_to_bq(file_path, category, is_raw=False):
    """
    Ingests a Parquet file into Google BigQuery using a tiered architecture (Staging vs Production).
    
    Args:
        file_path (str): Absolute path to the source Parquet file.
        category (str): Taxi vehicle category identifier.
        is_raw (bool): If True, targets the Staging area; otherwise targets the Production DW.
    """
    client = get_bq_client()
    table_id, job_config = get_bq_config(category, is_raw=is_raw)
    
    # Ensure the destination dataset exists before materialization
    dataset_ref = ".".join(table_id.split(".")[:2])
    client.create_dataset(dataset_ref, exists_ok=True)

    with open(file_path, "rb") as source_file:
        file_name = os.path.basename(file_path)
        tier = "STAGING" if is_raw else "PRODUCTION"
        print(f"   [{tier}] Ingesting {file_name} -> {table_id}...")
        
        # Dispatch the load job
        job = client.load_table_from_file(source_file, table_id, job_config=job_config)
        job.result()  # Blocking call to wait for ingestion completion
        
    print(f"   [{tier}] SUCCESS: Materialization complete for {file_name}")
