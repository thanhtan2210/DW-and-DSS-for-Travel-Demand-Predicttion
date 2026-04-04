# Exploratory Data Analysis (EDA) Report

## 1. Executive Summary
This report summarizes the findings from the Exploratory Data Analysis conducted on the NYC TLC Trip Record dataset (June 2025 sample). The primary objective was to diagnose data quality issues, identify outliers, and validate temporal patterns to define the rules for the subsequent ETL pipeline and machine learning modeling.

## 2. Dataset Overview & Completeness
*   **Data Volume:** The June 2025 sample contains approximately **4.32 million records**.
*   **Missing Values Analysis:**
    *   Significant null counts (~28%) were observed in fields such as `passenger_count`, `RatecodeID`, and `congestion_surcharge`.
    *   **Strategic Decision:** Since the core objective is **Travel Demand Prediction**, records will only be dropped if primary keys or critical spatio-temporal fields (`pickup_datetime`, `PULocationID`) are null. Non-critical nulls in secondary fields will be retained to preserve the total demand count.

## 3. Outlier Detection & Logical Anomalies
The analysis revealed several physical and logical impossibilities caused by sensor malfunctions or human error:

### A. Temporal Anomalies
*   **Invalid Durations:** Observed negative durations (e.g., -51 mins) and extreme outliers (e.g., 8,500+ mins, roughly 6 days).
*   **Rule:** Implementation of a 1-minute minimum and 180-minute maximum threshold for valid trips.

### B. Financial Anomalies
*   **Fare Irregularities:** Detected negative fare amounts (-$99) and extreme values (+$325,000) likely due to system errors.
*   **Rule:** Trips will be filtered to keep `fare_amount` within the [$2.5, $500] range.

### C. Operational Anomalies
*   **Passenger Counts:** Identified over 22,000 trips with 0 passengers and several trips exceeding standard vehicle capacity (7+ passengers).
*   **Rule:** Keep only trips with 1 to 6 passengers.

## 4. Spatio-Temporal Demand Patterns
*   **Hourly Distribution:** Demand consistently hits its lowest point between **4:00 AM - 5:00 AM** and reaches peak volume during the evening rush hour (**5:00 PM - 7:00 PM**).
*   **Validation:** These patterns align with urban mobility logic, confirming that `pickup_hour` is a high-variance feature and will serve as a critical input for predictive models (XGBoost/LSTM).

## 5. Conclusion & Next Steps
The EDA confirms that while the dataset is noisy, the underlying demand signal is strong and predictable. The insights derived here will be used to build a **Rule-Based ETL Pipeline** that cleans the data while maximizing the retention of valid demand observations for the Data Warehouse.
