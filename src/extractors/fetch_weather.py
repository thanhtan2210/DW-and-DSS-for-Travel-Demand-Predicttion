import requests
import pandas as pd
import os
from datetime import datetime, timedelta

def fetch_weather_data(start_date, end_date):
    # Using Open-Meteo Archive API
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": 40.7128,
        "longitude": -74.0060,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": "temperature_2m,precipitation"
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if 'hourly' in data:
            df = pd.DataFrame(data['hourly'])
            filename = f"dataset/weather_forecast/weather_data_{datetime.now().strftime('%Y%m%d')}.csv"
            df.to_csv(filename, index=False)
            print(f"Weather data saved to {filename}")
            return df
        else:
            print(f"Error: {data.get('reason', 'Unknown API error')}")
            return None
    except Exception as e:
        print(f"Connection failed: {e}")
        return None

if __name__ == "__main__":
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    fetch_weather_data("2025-01-01", yesterday)
