import polars as pl
import glob
import os

def get_files(base_path, category):
    """Find all parquet files in the specified category directory."""
    input_path = os.path.join(base_path, category)
    return glob.glob(os.path.join(input_path, "*.parquet"))

def read_data(file_path):
    """Read data from a Parquet file."""
    return pl.read_parquet(file_path)
