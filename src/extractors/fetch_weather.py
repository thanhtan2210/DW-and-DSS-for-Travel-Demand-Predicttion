import requests
import pandas as pd
import os

def fetch_historical_weather():
    print(">>> Bắt đầu tải dữ liệu thời tiết lịch sử NYC từ Open-Meteo...")
    
    # 1. Cấu hình thông số API
    lat, lon = 40.7128, -74.0060 # Tọa độ trung tâm New York
    start_date = "2025-06-01"
    end_date = "2025-11-30"
    
    # Gọi API Archive của Open-Meteo (Miễn phí, không cần API Key)
    # Lấy nhiệt độ (temperature_2m), lượng mưa (precipitation) và mã thời tiết (weather_code) theo giờ
    url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date={start_date}&end_date={end_date}&hourly=temperature_2m,precipitation,weather_code&timezone=America%2FNew_York"
    
    try:
        response = requests.get(url)
        response.raise_for_status() # Kiểm tra lỗi HTTP
        data = response.json()
        hourly = data['hourly']
        
        # 2. Đưa dữ liệu json vào DataFrame
        df = pd.DataFrame({
            "time": hourly["time"],
            "temperature_2m": hourly["temperature_2m"],
            "precipitation": hourly["precipitation"],
            "weather_code": hourly["weather_code"]
        })
        
        # 3. Biến đổi dữ liệu (Transform) cho phù hợp với Data Warehouse
        
        # Hàm chuyển đổi mã WMO (weather_code) sang chuỗi mô tả dễ hiểu (Condition)
        def map_weather_condition(code):
            if pd.isna(code): return "Unknown"
            if code == 0: return "Clear"
            elif 1 <= code <= 3: return "Cloudy"
            elif 45 <= code <= 67 or 80 <= code <= 82: return "Rain"
            elif 71 <= code <= 77 or 85 <= code <= 86: return "Snow"
            elif code >= 95: return "Thunderstorm"
            else: return "Other"
            
        df['Condition'] = df['weather_code'].apply(map_weather_condition)
        
        # Quan Trọng: Tạo Weather_Key (YYYYMMDDHH) để làm Khóa Chính nối với Fact_Trips
        df['time'] = pd.to_datetime(df['time'])
        df['Weather_Key'] = df['time'].dt.strftime('%Y%m%d%H').astype(int)
        
        # Chuẩn hóa tên cột cho đẹp
        df = df.rename(columns={
            "temperature_2m": "Temperature",
            "precipitation": "Precipitation"
        })
        
        # Chỉ giữ lại các cột cần thiết cho bảng Dim_Weather
        dim_weather = df[['Weather_Key', 'Temperature', 'Precipitation', 'Condition']]
        
        # 4. Lưu dữ liệu xuống ổ cứng
        output_dir = "dataset"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "nyc_weather_2025.csv")
        
        dim_weather.to_csv(output_path, index=False)
        print(f">>> THÀNH CÔNG! Đã lưu dữ liệu thời tiết tại: {output_path}")
        print(f">>> Tổng số giờ quan trắc: {len(dim_weather)} dòng.")
        
    except Exception as e:
        print(f">>> [LỖI] Không thể lấy dữ liệu: {e}")

if __name__ == "__main__":
    fetch_historical_weather()
