import argparse
import os
from src.data_pipeline import run_pipeline
from dotenv import load_dotenv

def main():
    """Điểm khởi đầu chính của dự án ETL - Hỗ trợ BigQuery với tính năng chống overload."""
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="NYC Taxi ETL Master Script (BigQuery Focus)")
    parser.add_argument("--raw", action="store_true", help="Nạp dữ liệu THÔ (Raw) lên BigQuery")
    parser.add_argument("--clean", action="store_true", help="Nạp dữ liệu SẠCH (Cleaned/Aggregated) lên BigQuery")
    parser.add_argument("--all", action="store_true", help="Nạp TẤT CẢ lên BigQuery")
    parser.add_argument("--cat", type=str, choices=["yellow", "green", "fhv", "fhvhv"], help="Chỉ xử lý 1 danh mục cụ thể (Ví dụ: green)")
    parser.add_argument("--threads", type=int, default=2, help="Giới hạn số luồng CPU để tránh đơ máy (mặc định: 2)")
    
    args = parser.parse_args()
    
    # Cấu hình môi trường cho Polars
    os.environ["POLARS_MAX_THREADS"] = str(args.threads)
    
    load_raw = args.raw or args.all
    load_clean = args.clean or args.all
    
    if not (load_raw or load_clean):
        print("[!] Lưu ý: Bạn chưa chọn loại dữ liệu nạp. Hệ thống sẽ mặc định chạy Cleaned.")
        load_clean = True

    # Chạy quy trình ETL
    run_pipeline(load_raw=load_raw, load_clean=load_clean, target_cat=args.cat)

if __name__ == "__main__":
    main()
