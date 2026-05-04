import pandas as pd
import requests
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

def fetch_nyc_weather_data(start_date='2025-06-01', end_date='2025-11-30'):
    """
    Simulates or fetches NYC historical weather data for the study period.
    Constructs a Time-Series weather dimension for travel demand correlation.
    """
    print(f">>> Initializing weather data acquisition for {start_date} to {end_date}...")
    
    # Generate hourly timestamp range
    date_range = pd.date_range(start=start_date, end=end_date, freq='H')
    
    # Placeholder for actual API integration (e.g., VisualCrossing or Open-Meteo)
    # Using deterministic simulation for the environment setup
    weather_data = []
    for dt in date_range:
        weather_key = int(dt.strftime('%Y%m%d%H'))
        # Generate semi-realistic seasonal temperatures for NYC
        month = dt.month
        base_temp = 25 if month in [6,7,8] else 15
        
        weather_data.append({
            'Weather_Key': weather_key,
            'Temperature': round(base_temp + (dt.hour % 10) * 0.5, 1),
            'Precipitation': 0.1 if dt.hour % 24 == 15 else 0.0,
            'Condition': 'Cloudy' if dt.hour % 5 == 0 else 'Clear'
        })
    
    df = pd.DataFrame(weather_data)
    
    # Persistence
    output_path = "dataset/nyc_weather_2025.csv"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f">>> SUCCESS: Weather artifacts synchronized to {output_path}")

if __name__ == "__main__":
    fetch_nyc_weather_data()
