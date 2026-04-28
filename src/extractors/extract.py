import polars as pl
import glob
import os

def get_files(base_path, category):
    """Tìm tất cả các file parquet trong thư mục danh mục."""
    input_path = os.path.join(base_path, category)
    return glob.glob(os.path.join(input_path, "*.parquet"))

def scan_data(file_path):
    """Sử dụng Lazy API để quét file mà không nạp vào RAM ngay lập tức."""
    return pl.scan_parquet(file_path)

def read_data(file_path):
    """Vẫn giữ hàm này cho các trường hợp cần nạp ngay, nhưng sẽ ít dùng hơn."""
    return pl.read_parquet(file_path)
