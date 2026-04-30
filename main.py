import argparse
import os
from src.data_pipeline import run_pipeline
from dotenv import load_dotenv

def main():
    """Điểm khởi đầu của hệ thống ETL tích hợp (Polars & BigQuery Engines)."""
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="NYC Taxi ETL & Star Schema Master Script")
    parser.add_argument("--engine", type=str, choices=["polars", "bigquery"], default="polars", 
                        help="Chọn engine xử lý: 'polars' (Local) hoặc 'bigquery' (Cloud ELT)")
    parser.add_argument("--raw", action="store_true", help="Nạp dữ liệu THÔ (Staging) lên BigQuery")
    parser.add_argument("--clean", action="store_true", help="Xử lý và nạp dữ liệu SẠCH (DW) lên BigQuery")
    parser.add_argument("--dims", action="store_true", help="Nạp các bảng Dimension (Time, Location, etc.) lên BigQuery")
    parser.add_argument("--all", action="store_true", help="Thực hiện TẤT CẢ các bước (Dims + Raw + Clean)")
    parser.add_argument("--cat", type=str, choices=["yellow", "green", "fhv", "fhvhv"], help="Chỉ xử lý 1 danh mục cụ thể")
    parser.add_argument("--threads", type=int, default=4, help="Giới hạn số luồng CPU cho Polars (mặc định: 4)")
    
    args = parser.parse_args()
    
    # Cấu hình môi trường cho Polars
    os.environ["POLARS_MAX_THREADS"] = str(args.threads)
    
    load_raw = args.raw or args.all
    load_clean = args.clean or args.all
    load_dims = args.dims or args.all
    
    print(f"[*] Cấu hình: Engine={args.engine}, Category={args.cat or 'ALL'}")
    print(f"[*] Hành động: Raw={load_raw}, Clean={load_clean}, Dims={load_dims}")

    # Chạy quy trình ETL/ELT tích hợp
    run_pipeline(
        engine=args.engine,
        load_raw=load_raw, 
        load_clean=load_clean, 
        load_dims=load_dims, 
        target_cat=args.cat
    )

if __name__ == "__main__":
    main()
