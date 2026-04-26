import os

def ensure_output_dir(base_path, category):
    """Tạo thư mục đầu ra nếu chưa tồn tại."""
    path = os.path.join(base_path, category)
    os.makedirs(path, exist_ok=True)
    return path

def save_data(df, output_path, file_name):
    """Ghi dữ liệu đã làm sạch ra file Parquet và trả về đường dẫn."""
    full_path = os.path.join(output_path, f"cleaned_{file_name}")
    df.write_parquet(full_path)
    return full_path
