import os
import polars as pl

def ensure_output_dir(base_path, category):
    """Tạo thư mục đầu ra nếu chưa tồn tại."""
    path = os.path.join(base_path, category)
    os.makedirs(path, exist_ok=True)
    return path

def save_data(df, output_path, file_name):
    """Ghi dữ liệu DataFrame đã nạp vào RAM (dùng cho bảng nhỏ/Aggregated)."""
    full_path = os.path.join(output_path, f"cleaned_{file_name}")
    df.write_parquet(full_path)
    return full_path

def sink_data(lf, output_path, file_name):
    """Ghi dữ liệu trực tiếp từ LazyFrame xuống đĩa (Streaming - Không tốn RAM)."""
    full_path = os.path.join(output_path, f"cleaned_{file_name}")
    # Cơ chế sink_parquet cực kỳ mạnh mẽ cho dữ liệu khổng lồ
    lf.sink_parquet(full_path)
    return full_path
