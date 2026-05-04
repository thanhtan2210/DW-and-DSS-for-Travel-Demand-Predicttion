import os
import polars as pl

def ensure_output_dir(base_dir, category):
    """
    Creates the processing output directory if it does not exist.
    
    Args:
        base_dir (str): Root directory for processed data.
        category (str): Sub-directory name for the taxi category.
        
    Returns:
        str: Absolute path to the validated directory.
    """
    path = os.path.join(base_dir, category)
    os.makedirs(path, exist_ok=True)
    return path

def save_data(df, output_dir, file_name):
    """
    Materializes and saves a Polars DataFrame to a Parquet file.
    
    Args:
        df (pl.DataFrame): The DataFrame to persist.
        output_dir (str): Target directory.
        file_name (str): Original filename for reference.
        
    Returns:
        str: Path to the saved Parquet file.
    """
    out_path = os.path.join(output_dir, file_name)
    df.write_parquet(out_path)
    return out_path

def sink_data(lf, output_dir, file_name):
    """
    Streams a Polars LazyFrame directly to disk (Memory-Safe sink).
    
    Args:
        lf (pl.LazyFrame): The computation graph to execute and stream.
        output_dir (str): Target directory.
        file_name (str): Output filename.
        
    Returns:
        str: Path to the materialized file.
    """
    out_path = os.path.join(output_dir, file_name)
    # Perform a streaming sink to bypass RAM limitations
    lf.sink_parquet(out_path)
    return out_path
