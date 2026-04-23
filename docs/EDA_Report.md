# Exploratory Data Analysis (EDA) Report - NYC TLC Data

## 1. Executive Summary
Báo cáo này tóm tắt các phát hiện từ quá trình EDA trên dữ liệu NYC TLC (tháng 06/2025). Mục tiêu chính là chẩn đoán các vấn đề về chất lượng dữ liệu và xác định các quy tắc làm sạch (Cleaning Rules) cho đường ống ETL.

## 2. Dataset Overview & Data Quality Issues

### A. Yellow Taxi (4.32 triệu bản ghi)
Đây là tập dữ liệu lớn nhất và chứa nhiều sai lệch vật lý nhất:
*   **Lỗi logic thời gian:** Xuất hiện các chuyến đi có thời gian âm (-51.68 phút) và cực đại vô lý (8,596 phút ~ 6 ngày).
*   **Sai lệch quãng đường:** Ghi nhận lên tới 261,262 dặm (Lỗi cảm biến).
*   **Cước phí "hoang tưởng":** Xuất hiện cước phí âm (-99.0 USD) và cực đại (325,478 USD).
*   **Lỗi hệ thống cụm:** Có đúng **121,294 dòng** bị rỗng đồng loạt các thông tin phụ trợ (số khách, phụ phí, mã giá cước). Đây là dấu hiệu của lỗi Vendor ghi nhận.

### B. Green Taxi (493,900 bản ghi)
*   **Cột dữ liệu "chết":** Cột `ehail_fee` rỗng 100% trên toàn bộ tập dữ liệu.
*   **Lỗi hệ thống cụm:** Khoảng **3,785 dòng** bị mất thông tin định danh thanh toán và loại giá cước.
*   **Quãng đường cực đại:** 77,463 dặm (Lỗi hệ thống).

### C. FHV (For-Hire Vehicle)
*   **Mất dữ liệu tài chính:** Hầu hết các cột liên quan đến cước phí bị trống hoàn toàn.
*   **Thiếu thông tin vị trí:** Một lượng lớn bản ghi không có `PULocationID` và `DOLocationID`.
*   **Tính toàn vẹn:** Nếu xóa bỏ các dòng thiếu vị trí sẽ làm mất đi tín hiệu về tổng nhu cầu (Demand Signal).

### D. FHVHV (High Volume - Uber/Lyft)
*   **Timeline Complexity:** Ma trận 4 mốc thời gian (Request, On-scene, Pickup, Dropoff).
*   **Business Nulls:** Các cột Flags (shared_request, wav_request) mang giá trị Null khi người dùng không sử dụng tính năng đó.

## 3. Quy tắc làm sạch (ETL Rules)
Dựa trên các phát hiện trên, quy trình ETL sẽ áp dụng các bộ lọc sau:
1.  **Thời gian:** Chỉ giữ lại các chuyến đi từ 1 đến 180 phút.
2.  **Quãng đường:** Giới hạn từ 0.1 đến 50 dặm (Taxi) hoặc 100 dặm (App).
3.  **Cước phí:** Tối thiểu 2.5$ cho Taxi; loại bỏ cước âm cho tất cả các loại xe.
4.  **Vị trí:** Sử dụng mã **264 (Unknown)** để bù đắp dữ liệu thiếu thay vì xóa bỏ (đặc biệt cho FHV).
5.  **Cột chết:** Tự động loại bỏ các cột rỗng 100% để tối ưu kho dữ liệu.
