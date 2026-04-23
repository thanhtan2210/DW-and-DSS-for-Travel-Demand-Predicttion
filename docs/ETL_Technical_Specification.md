# ETL Technical Specification & Data Quality Management

Tài liệu này chi tiết hóa cấu trúc và logic nghiệp vụ của hệ thống ETL tích hợp cho dự án Dự báo nhu cầu giao thông NYC.

## 1. Kiến trúc Pipeline (Unified ETL)
Hệ thống được thiết kế theo nguyên tắc **Modular Architecture**, chia tách hoàn toàn các giai đoạn:
*   **Extractors (`src/extractors/`):** Chịu trách nhiệm đọc dữ liệu từ tệp Parquet bằng Polars cho tốc độ tối ưu.
*   **Transformers (`src/transformers/`):** Chứa toàn bộ logic làm sạch và chuẩn hóa dữ liệu. Đây là phần lõi của hệ thống.
*   **Loaders (`src/loaders/`):** Phụ trách việc nạp dữ liệu vào nhiều đích (Local Parquet, SQL Server, Google BigQuery).
*   **Utils (`src/utils/`):** Quản lý kết nối Database tập trung.

## 2. Chiến lược xử lý chất lượng dữ liệu

### A. Chuẩn hóa Schema
Toàn bộ tên cột được chuẩn hóa về một bộ quy tắc chung để hỗ trợ việc gộp bảng (UNION) trong Data Warehouse:
*   `tpep_pickup_datetime` / `lpep_pickup_datetime` / `pickup_datetime` -> **`pickup_time`**
*   `trip_distance` / `trip_miles` -> **`distance`**
*   `fare_amount` / `base_passenger_fare` -> **`fare`**

### B. Logic làm sạch chuyên biệt (Transform Stage)

#### 1. Xử lý "Dữ liệu chết" (Dead Columns)
Hệ thống tự động quét và loại bỏ bất kỳ cột nào có tỷ lệ Null là 100% trong mỗi tập dữ liệu. Điều này đặc biệt hiệu quả cho xe Green (`ehail_fee`) và FHV (các cột cước phí trống).

#### 2. Xử lý Outliers & Lỗi vật lý
*   **Thời gian di chuyển:** `1 <= duration_minutes <= 180`. Loại bỏ các chuyến đi âm hoặc kéo dài quá 3 tiếng.
*   **Quãng đường:**
    *   Taxi (Yellow/Green): `0.1 <= distance <= 50` dặm.
    *   App-based (FHVHV): `0.1 <= distance <= 100` dặm.
*   **Cước phí:**
    *   Taxi: `fare >= 2.5$` (Giá mở cửa tối thiểu tại NYC). Loại bỏ các cuốc xe âm (Refund).

#### 3. Xử lý Missing Values (Imputation)
*   **Hành khách:** Mặc định điền **1** nếu số khách bị trống (`fill_null(1)`).
*   **Vị trí (LocationID):** Đối với FHV, các dòng bị mất LocationID sẽ được gán mã **264 (Unknown)** để duy trì toàn vẹn dữ liệu cho mô hình Forecasting mà không làm hỏng Star Schema.
*   **FHVHV Flags:** Điền **'N'** cho các cờ hiệu (shared, wav) nếu trống thay vì xóa bỏ.

## 3. Quản lý tải dữ liệu (Loading Strategy)
Hệ thống hỗ trợ 3 đích nạp thông qua các tham số điều khiển:
*   **Local (`--local`):** Lưu dữ liệu đã làm sạch dưới định dạng Parquet tại `dataset/processed/`.
*   **BigQuery (`--bq`):** Đẩy dữ liệu trực tiếp lên BigQuery với cấu trúc bảng được phân vùng (Partitioned) để tối ưu chi phí.
*   **SQL Server (`--sql`):** Nạp vào bảng `Fact_Trips` và tự động cập nhật các bảng `DimTime`, `DimLocation`.

## 4. Công nghệ sử dụng
*   **Polars:** Thư viện xử lý dữ liệu chính (Hiệu năng vượt trội hơn Pandas trên tập dữ liệu hàng triệu dòng).
*   **google-cloud-bigquery:** Thư viện chính thức từ Google cho tích hợp Cloud.
*   **pyodbc:** Kết nối SQL Server nội bộ.
*   **python-dotenv:** Quản lý cấu hình bảo mật thông qua biến môi trường.
