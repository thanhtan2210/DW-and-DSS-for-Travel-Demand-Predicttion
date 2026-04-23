import argparse
from src.data_pipeline import run_pipeline
from dotenv import load_dotenv

def main():
    """Điểm khởi đầu chính của dự án ETL - Hỗ trợ nạp song song Raw và Cleaned."""
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="NYC Taxi ETL Master Script (Google BigQuery Focus)")
    parser.add_argument("--raw", action="store_true", help="Nạp dữ liệu THÔ (Raw) lên BigQuery")
    parser.add_argument("--clean", action="store_true", help="Nạp dữ liệu SẠCH (Cleaned/Aggregated) lên BigQuery")
    parser.add_argument("--all", action="store_true", help="Nạp TẤT CẢ (Cả Raw và Clean) lên BigQuery")
    
    args = parser.parse_args()
    
    # Xác định trạng thái nạp dựa trên flag
    load_raw = args.raw or args.all
    load_clean = args.clean or args.all
    
    if not (load_raw or load_clean):
        print("[!] Cảnh báo: Bạn chưa chọn flag nào (--raw, --clean, hoặc --all). Hệ thống sẽ chỉ làm sạch dữ liệu tại máy.")

    # Chạy quy trình ETL tích hợp
    run_pipeline(load_raw=load_raw, load_clean=load_clean)

if __name__ == "__main__":
    main()
