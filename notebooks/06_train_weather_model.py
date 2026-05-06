import pandas as pd
import numpy as np
import os
import joblib
from datetime import datetime, timedelta
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
import sys

# Add project root to path to import fetcher
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.extractors.fetch_weather import fetch_weather_data

# 0. Fetch Data
print(">>> Fetching latest weather data...")
yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
df = fetch_weather_data("2025-01-01", yesterday)

if df is None:
    print("Error: Could not fetch weather data. Aborting training.")
    sys.exit(1)

# 1. Prepare Data
df['time'] = pd.to_datetime(df['time'])
data = df[['temperature_2m', 'precipitation']].values

# 2. Scale Data
scaler = MinMaxScaler()
scaled_data = scaler.fit_transform(data)

# 3. Create Sequences
def create_sequences(data, seq_length=24):
    X, y = [], []
    for i in range(len(data) - seq_length):
        X.append(data[i:i+seq_length])
        y.append(data[i+seq_length])
    return np.array(X), np.array(y)

X, y = create_sequences(scaled_data)

# 4. Train Simple LSTM Model
model = Sequential([
    LSTM(50, activation='relu', input_shape=(24, 2)),
    Dense(2)
])
model.compile(optimizer='adam', loss='mse')
model.fit(X, y, epochs=10, batch_size=32, verbose=1)

# 5. Save Artifacts
os.makedirs('saved_models/weather', exist_ok=True)
model.save('saved_models/weather/weather_forecast_model.keras')
joblib.dump(scaler, 'saved_models/weather/weather_scaler.pkl')

print("Weather forecast model trained and saved using latest data.")
