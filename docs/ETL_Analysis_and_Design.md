# ETL Process: Analysis, Design, and Implementation

This document provides a comprehensive technical overview of the Extract, Transform, and Load (ETL) pipeline designed for the NYC Taxi & FHV dataset. The pipeline is engineered to handle multi-million row datasets efficiently while ensuring high data quality for Travel Demand Prediction and Decision Support Systems (DSS).

## 1. Pipeline Architecture
The system follows a **Modular ETL Architecture** built with **Python** and **Polars**. To handle large-scale data (especially FHVHV/Uber/Lyft) on consumer-grade hardware, we utilize the **Polars Lazy API**, which minimizes RAM usage by deferring execution until the final ingestion step.

*   **Extraction:** Scans raw Parquet files without full memory loading.
*   **Transformation:** Applies domain-specific cleaning rules and standardizes schemas.
*   **Aggregation:** Summarizes trip-level data into hourly demand slots.
*   **Loading:** Performs dual-stage ingestion into Google BigQuery (Raw and Cleaned datasets).

---

## 2. Data Cleaning & Standardisation Strategy

### 2.1. Schema Unification (The "Gold" Schema)
Each TLC dataset (Yellow, Green, FHV, FHVHV) has inconsistent naming conventions (e.g., `tpep_pickup_datetime` vs `pickup_datetime`). Our pipeline enforces a unified schema:
*   **`pickup_time` / `dropoff_time`**: Standardized timestamps.
*   **`distance`**: Normalized trip miles.
*   **`fare`**: Base passenger fare for financial analysis.
*   **`pulocationid` / `dolocationid`**: Standard Taxi Zone IDs.

### 2.2. Robust Outlier Filtering
Based on Exploratory Data Analysis (EDA), we apply "hard" filters to eliminate physical impossibilities and sensor errors:
*   **Temporal Integrity:** Only trips between **1 and 180 minutes** are retained. Negative durations and multi-day "ghost" trips are dropped.
*   **Spatial Bounds:** Distance must be between **0.1 and 50 miles** (100 miles for App-based).
*   **Financial Validation:** Taxi fares are capped at a minimum of **$2.50** (NYC flag drop rate) to remove refunds and errors.

### 2.3. Missing Value Management (Smart Imputation)
To preserve total demand counts for forecasting, we avoid simply dropping rows with nulls:
*   **Unknown Zones:** Missing `PULocationID` or `DOLocationID` are mapped to **264 (Unknown)**. This maintains referential integrity with the `DimLocation` table.
*   **App-Based Flags:** Nulls in `shared_request_flag` or `wav_request_flag` are imputed with **'N'** (No), as a null usually indicates the feature was not used.
*   **Dead Columns:** Entirely null columns (like `ehail_fee` in Green Taxi) are automatically identified and dropped to optimize BigQuery storage costs.

---

## 3. Dimensional Modeling (Star Schema)

The ETL pipeline transforms raw "Trip Grain" data into an "Hourly-Zone Grain" suitable for **Star Schema** analysis:

### 3.1. Fact Table: `Fact_Trips`
Aggregated by **(1 Hour, 1 Zone)**.
*   **Keys:** `time_key` (YYYYMMDDHH), `pulocationid`.
*   **Measures:** 
    *   `trip_count`: The core target for Travel Demand Prediction.
    *   `total_revenue`: Sum of fares for economic impact analysis.
    *   **`total_distance`**: Sum of miles for traffic density modeling.

### 3.2. Dimension Tables
*   **`DimTime`**: Derived from the project date range (Jun - Nov 2025), including `is_holiday` and `is_weekend` flags.
*   **`DimLocation`**: Mapped from the official NYC Taxi Zone lookup.

---

## 4. Operational Excellence & Performance Optimization

### 4.1. The FHVHV Performance Challenge
During implementation, we identified a critical bottleneck: **System Freezes** when cleaning FHVHV (Uber/Lyft) data. 
*   **The Symptom:** While uploading raw data to BigQuery works seamlessly (Direct Stream), the cleaning process causes the system to hang.
*   **The Reason:** The `collect()` operation in Polars attempts to materialize millions of rows (2M - 5M+ per file) into RAM simultaneously. This creates a "Memory Spike" that exceeds consumer-grade hardware limits, forcing the OS to use slow swap space or freeze entirely.
*   **The Solution (Ultra Memory Saver):** We migrated from Eager materialization to **Streaming Sinking**.

### 4.2. Two-Pass Execution Strategy (The "Safe-Break" Logic)
To handle FHVHV data (5M+ rows) without memory overflow, the pipeline was upgraded to a two-pass architecture:
1.  **Pass 1 (Streaming Clean):** Data is read via `scan_parquet`, cleaned, and immediately "Sunk" to the disk using `sink_parquet`. This breaks the long calculation chain and flushes the RAM.
2.  **Pass 2 (Atomic Aggregation):** The pipeline re-reads the *already cleaned* file to perform hourly aggregations. This ensures that the complex Group-by operations only happen on clean, manageable data structures.

### 4.3. Deduplication Trade-off
The global `.unique()` (Deduplication) step was removed for the following technical reasons:
*   **Memory Overhead:** Deduplication requires maintaining a massive Hash Table in RAM, which is the primary cause of system freezes on FHVHV.
*   **Data Characteristics:** NYC TLC data has extremely low redundancy at the grain level. The performance gain of system stability far outweighs the negligible risk of duplicate records.

### 4.2. Monitoring & Logging
Every run generates an `etl_report_summary.csv` containing:
*   **Raw vs. Cleaned Row Counts**: Monitors data loss during cleaning.
*   **Retention Rate**: Tracks the percentage of valid data preserved.
*   **Status Logs**: Immediate feedback on BigQuery ingestion success or failure.

---

## 5. Conclusion
This ETL pipeline transforms noisy, fragmented urban mobility data into a high-quality, structured data warehouse. By combining **Polars' speed** with **BigQuery's scalability**, the system provides a solid foundation for both real-time decision support and advanced machine learning forecasting.
