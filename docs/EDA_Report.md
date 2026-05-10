# Exploratory Data Analysis (EDA) Report - NYC TLC Data

## 1. Executive Summary
This report summarizes the findings from the Exploratory Data Analysis (EDA) process conducted on the NYC TLC dataset (June 2025). The primary objective was to diagnose data quality issues and establish the "Cleaning Rules" required for theoduction ETL pipeline.

## 2. Dataset Overview & Data Quality Issues

### A. Yellow Taxi (4.32 Million Records)
As the largest dataset, it exhibits the highest frequency of physical and sensor-related anomalies:
*   **Temporal Logic Errors:** Presence of trips with negative durations (e.g., -51.68 minutes) and irrational maximums (e.g., 8,596 minutes, approximately 6 days).
*   **Trip Distance Anomalies:** Records showing distances up to 261,262 miles, likely due to sensor malfunctions.
*   **Irrational Fare Amounts:** Detection of negative fares (-99.0 USD) and extreme outliers reaching 325,478 USD.
*   **Systematic Null Clusters:** Exactly **121,294 rows** contain simultaneous null values across auxiliary columns (passenger count, surcharges, rate code). This indicates a specific Vendor-side logging failure.

### B. Green Taxi (493,900 Records)
*   **"Dead" Data Columns:** The `ehail_fee` column is 100% null across the entire dataset and serves no analytical purpose.
*   **Systematic Missing Info:** Approximately **3,785 rows** lack payment identifiers and rate types.
*   **Distance Outliers:** Maximum recorded distance of 77,463 miles, attributed to system errors.

### C. FHV (For-Hire Vehicle)
*   **Financial Data Loss:** Most fare-related columns are entirely empty, rendering financial analysis impossible for this segment.
*   **Missing Location Identifiers:** A significant volume of records lacks `PULocationID` and `DOLocationID`.
*   **Data Integrity:** Dropping records with missing locations would severely compromise the "Demand Signal"; therefore, imputation is required.

### D. FHVHV (High Volume - Uber/Lyft)
*   **Timeline Complexity:** Features a complex matrix of four distinct timestamps (Request, On-scene, Pickup, Dropoff).
*   **Business-Logic Nulls:** Flag columns such as `shared_request` and `wav_request` contain Null values when the feature was not utilized by the user, rather than indicating missing data.

## 3. ETL Cleaning Rules
Based on the EDA findings, the ETL pipeline will enforce the following filtration and transformation rules:

1.  **Duration:** Retain only trips between **1 and 180 minutes**.
2.  **Distance:** Limit range from **0.1 to 50 miles** for Taxis, and up to **100 miles** for FHVHV.
3.  **Fares:** Enforce a minimum of **$2.50** for Taxis; remove all negative fare records across all vehicle types.
4.  **Location Imputation:** Replace missing location IDs with code **264 (Unknown)** to preserve the total demand signal (especially for FHV).
5.  **Schema Optimization:** Automatically drop "Dead Columns" (100% null) to optimize Data Warehouse storage and performance.
