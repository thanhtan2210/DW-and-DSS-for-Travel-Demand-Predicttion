import os
import argparse
import polars as pl
import pandas as pd
import gc
from datetime import datetime
from .extractors.extract import get_files, scan_data, read_data
from .transformers.transform import standardize_columns, apply_cleaning_logic, aggregate_trips
from .loaders.local import ensure_output_dir, save_data, sink_data
from .loaders.bigquery import load_parquet_to_bq

def run_pipeline(load_raw=False, load_clean=False, target_cat=None):
    """Quy trình ETL 2 giai đoạn: Chống đơ máy bằng cách ngắt chuỗi Lazy."""
    input_base = os.getenv("RAW_DATA_DIR", "dataset/Trip_Record")
    output_base = os.getenv("PROCESSED_DATA_DIR", "dataset/processed")
    
    all_categories = ["yellow", "green", "fhv", "fhvhv"]
    categories = [target_cat] if target_cat else all_categories
    
    stats_report = []
    
    print("="*60)
    print(f"NYC TAXI - TWO-PASS PIPELINE (Memory Safe: {target_cat or 'ALL'})")
    print("="*60)
    
    for cat in categories:
        if cat not in all_categories: continue
        
        files = get_files(input_base, cat)
        output_dir = ensure_output_dir(output_base, cat)
        agg_output_dir = ensure_output_dir(output_base, f"aggregated/{cat}")
        
        print(f"\n>>> Giai đoạn 1: Làm sạch & Streaming {cat.upper()}...")
        
        for file_path in files:
            file_name = os.path.basename(file_path)
            current_stats = {"category": cat, "file_name": file_name, "raw_rows": 0, "cleaned_rows": 0, "status": "Success"}
            
            try:
                # --- PHẦN 1: LÀM SẠCH VÀ GHI ĐĨA (TIẾT KIỆM RAM) ---
                lf_raw = scan_data(file_path)
                
                if load_raw:
                    load_parquet_to_bq(file_path, cat, is_raw=True)
                
                lf_std = standardize_columns(lf_raw)
                lf_cleaned = apply_cleaning_logic(lf_std, cat)
                
                # Ghi file sạch xuống đĩa bằng cơ chế Streaming
                saved_path = sink_data(lf_cleaned, output_dir, file_name)
                
                # Giải phóng bộ nhớ chuỗi Lazy vừa rồi
                del lf_raw, lf_std, lf_cleaned
                gc.collect()

                # --- PHẦN 2: ĐỌC LẠI FILE SẠCH ĐỂ GỘP (BREAK THE CHAIN) ---
                if load_clean:
                    # Nạp bản sạch lên BQ ngay
                    load_parquet_to_bq(saved_path, cat, is_raw=False)
                    
                    # Quét lại file sạch để Aggregate (Chuỗi Lazy mới cực ngắn)
                    lf_from_disk = pl.scan_parquet(saved_path)
                    lf_agg = aggregate_trips(lf_from_disk)
                    
                    df_agg_final = lf_agg.collect()
                    agg_saved_path = save_data(df_agg_final, agg_output_dir, f"agg_{file_name}")
                    
                    # Nạp bản gộp lên BQ
                    load_parquet_to_bq(agg_saved_path, f"agg_{cat}", is_raw=False)
                    
                    current_stats["cleaned_rows"] = df_agg_final.select(pl.col("trip_count").sum()).item()
                    
                    del df_agg_final, lf_from_disk, lf_agg
                    gc.collect()
                    
                    print(f"   [DONE] {file_name}")
                
            except Exception as e:
                print(f"   [ERROR] Lỗi tại file {file_name}: {e}")
                current_stats["status"] = f"Failed: {str(e)}"
            
            stats_report.append(current_stats)

    # Xuất báo cáo CSV
    pd.DataFrame(stats_report).to_csv("etl_report_summary.csv", index=False)

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    run_pipeline(load_raw=True, load_clean=True)
