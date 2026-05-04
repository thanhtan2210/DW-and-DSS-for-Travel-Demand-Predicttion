import os
import polars as pl
import glob

def get_files(base_dir, category):
    """
    Retrieves a sorted list of Parquet file paths for a given vehicle category.
    
    Args:
        base_dir (str): Root directory for trip record data.
        category (str): Taxi category identifier (e.g., 'yellow', 'green', 'fhv').
        
    Returns:
        list: Alphabetically sorted list of file paths.
    """
    search_pattern = os.path.join(base_dir, category, "*.parquet")
    return sorted(glob.glob(search_pattern))

def scan_data(file_path):
    """
    Initializes a lazy scan of the Parquet source to minimize peak RAM usage.
    
    Args:
        file_path (str): Absolute or relative path to the Parquet file.
        
    Returns:
        pl.LazyFrame: Polars computation graph for deferred execution.
    """
    return pl.scan_parquet(file_path)

def read_data(file_path):
    """
    Reads a Parquet file into an eager Polars DataFrame for immediate manipulation.
    
    Args:
        file_path (str): Path to the target file.
        
    Returns:
        pl.DataFrame: Materialized Polars DataFrame.
    """
    return pl.read_parquet(file_path)
