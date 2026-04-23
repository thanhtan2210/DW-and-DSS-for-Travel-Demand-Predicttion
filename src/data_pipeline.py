import os
import argparse
import polars as pl
from .extractors.extract import get_files, read_data
from .transformers.transform import standardize_columns, apply_cleaning_logic, aggregate_trips
from .loaders.local import ensure_output_dir, save_data
from .loaders.bigquery import load_parquet_to_bq

def run_pipeline(load_raw=False, load_clean=False):
    """Quy trình ETL hợp nhất: Raw -> BQ_RAW | Cleaned -> BQ_CLEANED."""
    input_base = os.getenv("RAW_DATA_DIR", "dataset/Trip_Record")
    output_base = os.getenv("PROCESSED_DATA_DIR", "dataset/processed")
    categories = ["yellow", "green", "fhv", "fhvhv"]
    
    print("="*60)
    print("NYC TAXI DATA - DUAL INGESTION BQ PIPELINE")
    print("="*60)
    
    for cat in categories:
        files = get_files(input_base, cat)
        output_dir = ensure_output_dir(output_base, cat)
        agg_output_dir = ensure_output_dir(output_base, f"aggregated/{cat}")
        
        print(f"\n>>> Xử lý danh mục: {cat.upper()} ({len(files)} files)")
        
        for file_path in files:
            file_name = os.path.basename(file_path)
            try:
                # 1. EXTRACT
                df_raw = read_data(file_path)
                row_count_raw = df_raw.height
                
                # 2. LOAD RAW TO BIGQUERY
                if load_raw:
                    load_parquet_to_bq(file_path, cat, is_raw=True)
                
                # 3. TRANSFORM
                df_std = standardize_columns(df_raw)
                df_cleaned = apply_cleaning_logic(df_std, cat)
                row_count_cleaned = df_cleaned.height
                
                # 4. AGGREGATE
                df_aggregated = aggregate_trips(df_cleaned)
                
                # 5. LOAD LOCAL
                saved_path = save_data(df_cleaned, output_dir, file_name)
                agg_saved_path = save_data(df_aggregated, agg_output_dir, f"agg_{file_name}")
                
                # 6. LOGGING
                print(f"   [LOG] {file_name}: Trước: {row_count_raw:,} | Sau: {row_count_cleaned:,} dòng.")
                
                # 7. LOAD CLEANED TO BIGQUERY
                if load_clean:
                    load_parquet_to_bq(saved_path, cat, is_raw=False)
                    load_parquet_to_bq(agg_saved_path, f"agg_{cat}", is_raw=False)
                    
            except Exception as e:
                print(f"   [ERROR] Lỗi khi xử lý {file_name}: {e}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    run_pipeline(load_bq=True)
