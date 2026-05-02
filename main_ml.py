import sys
from src.models.train_model import run_automated_training

def main():
    print("============================================================")
    print("NYC TAXI - AUTOMATED ML PIPELINE (MLOps)")
    print("============================================================")
    print("Khởi động quá trình kéo dữ liệu, huấn luyện và lưu trữ model...\n")
    
    try:
        run_automated_training()
        print("\n[SUCCESS] Pipeline Machine Learning đã hoàn tất xuất sắc!")
    except Exception as e:
        print(f"\n[ERROR] Đã xảy ra lỗi trong quá trình huấn luyện: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
