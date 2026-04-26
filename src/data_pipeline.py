import os
import argparse
import polars as pl
import pandas as pd
import gc # Giải phóng bộ nhớ thủ công
from datetime import datetime
from .extractors.extract import get_files, scan_data, read_data
from .transformers.transform import standardize_columns, apply_cleaning_logic, aggregate_trips
from .loaders.local import ensure_output_dir, save_data
from .loaders.bigquery import load_parquet_to_bq

def run_pipeline(load_raw=False, load_clean=False):
    """Quy trình ETL tối ưu RAM bằng Lazy API của Polars."""
    input_base = os.getenv("RAW_DATA_DIR", "dataset/Trip_Record")
    output_base = os.getenv("PROCESSED_DATA_DIR", "dataset/processed")
    categories = ["yellow", "green", "fhv", "fhvhv"]
    
    stats_report = []
    
    print("="*60)
    print("NYC TAXI DATA - MEMORY OPTIMIZED BQ PIPELINE")
    print("="*60)
    
    for cat in categories:
        files = get_files(input_base, cat)
        output_dir = ensure_output_dir(output_base, cat)
        agg_output_dir = ensure_output_dir(output_base, f"aggregated/{cat}")
        
        print(f"\n>>> Xử lý danh mục: {cat.upper()} ({len(files)} files)")
        
        for file_path in files:
            file_name = os.path.basename(file_path)
            current_stats = {"category": cat, "file_name": file_name, "raw_rows": 0, "cleaned_rows": 0, "status": "Success"}
            
            try:
                # 1. EXTRACT (Lazy Scan)
                lf_raw = scan_data(file_path)
                
                # 2. LOAD RAW (Gửi file trực tiếp lên BQ, không thông qua RAM của máy)
                if load_raw:
                    load_parquet_to_bq(file_path, cat, is_raw=True)
                
                # 3. TRANSFORM & AGGREGATE (Vẫn là LazyFrame)
                lf_std = standardize_columns(lf_raw)
                lf_cleaned = apply_cleaning_logic(lf_std, cat)
                lf_aggregated = aggregate_trips(lf_cleaned)
                
                # 4. THỰC THI & NẠP (Chỉ nạp vào RAM từng phần)
                df_cleaned = lf_cleaned.collect()
                current_stats["raw_rows"] = lf_raw.select(pl.len()).collect().item()
                current_stats["cleaned_rows"] = df_cleaned.height
                
                saved_path = save_data(df_cleaned, output_dir, file_name)
                if load_clean:
                    load_parquet_to_bq(saved_path, cat, is_raw=False)
                
                # Giải phóng RAM ngay lập tức
                del df_cleaned
                gc.collect()

                df_aggregated = lf_aggregated.collect()
                agg_saved_path = save_data(df_aggregated, agg_output_dir, f"agg_{file_name}")
                if load_clean:
                    load_parquet_to_bq(agg_saved_path, f"agg_{cat}", is_raw=False)
                
                print(f"   [OK] {file_name}: {current_stats['raw_rows']:,} -> {current_stats['cleaned_rows']:,} dòng.")
                
                # Giải phóng RAM file cũ trước khi sang file mới
                del df_aggregated
                gc.collect()
                    
            except Exception as e:
                print(f"   [ERROR] Lỗi tại file {file_name}: {e}")
                current_stats["status"] = f"Failed: {str(e)}"
            
            stats_report.append(current_stats)

    # Xuất báo cáo CSV
    report_file = f"etl_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    pd.DataFrame(stats_report).to_csv(report_file, index=False)
    print(f"\n[DONE] Báo cáo chi tiết đã tạo: {report_file}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    run_pipeline(load_raw=True, load_clean=True)
