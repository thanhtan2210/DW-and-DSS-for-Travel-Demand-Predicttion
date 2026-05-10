# ETL Process: Analysis, Design, and Implementation

This document provides a comprehensive technical overview of the Extract, Transform, and Load (ETL) pipeline designed for the NYC Taxi & FHV dataset. The pipeline is engineered to handle multi-million row datasets efficiently while ensuring high data quality for Travel Demand Prediction and Decision Support Systems (DSS).

## 1. Hybrid Pipeline Architecture
The system supports two distinct execution strategies to balance local resource constraints with cloud scalability:

*   **Local Strategy (Polars):** Built with **Python** and **Polars**. To handle large-scale data (especially FHVHV/Uber/Lyft) on consumer-grade hardware, we utilize the **Polars Lazy API** and **Streaming Sink**, which minimizes RAM usage by deferring execution and flushing results directly to disk.
*   **Cloud Strategy (BigQuery):** Utilizes **SQL-based ELT**. Raw data is ingested into a staging area and then transformed/aggregated using BigQuery's distributed compute engine.

---

## 2. Data Cleaning & Standardization Strategy

### 2.1. Unified Schema Architecture (The "Gold" Schema)
Each TLC dataset (Yellow, Green, FHV, FHVHV) has inconsistent naming conventions. Our pipeline enforces a unified schema across all inputs:
*   **`pickup_time` / `dropoff_time`**: Standardized timestamps.
*   **`distance`**: Normalized trip miles.
*   **`fare`**: Base passenger fare for financial analysis.
*   **`pulocationid` / `dolocationid`**: Standard Taxi Zone IDs.
*   **`service_type_key`**: 1 (Yellow), 2 (Green), 3 (FHV), 4 (FHVHV).

### 2.2. Robust Outlier Filtering
Based on Exploratory Data Analysis (EDA), we apply "hard" filters to eliminate physical impossibilities and sensor errors:
*   **Temporal Integrity:** Only trips between **1 and 180 minutes** are retained.
*   **Spatial Bounds:** Distance must be between **0.1 and 50 miles** (100 miles for App-based).
*   **Financial Validation:** Taxi fares are capped at a minimum of **$2.50** (NYC flag drop rate).

### 2.3. Missing Value Management (Smart Imputation)
*   **Unknown Zones:** Missing location IDs are mapped to **264 (Unknown)**.
*   **App-Based Flags:** Nulls in `shared_request_flag` are imputed with **'N'**.

---

## 3. Dimensional Modeling (Star Schema)

The ETL pipeline transforms raw "Trip Grain" data into two functional fact tables:

### 3.1. Atomic Fact Table: `Fact_Trips`
*   **Grain:** Single trip observation.
*   **Purpose:** Detailed auditing, ad-hoc granular queries, and deep-dive spatial analysis.

### 3.2. Aggregated Fact Table: `Fact_Demand_Hourly`
*   **Grain:** 1 Hour, 1 Zone, 1 Service Type.
*   **Purpose:** Core "Feature Store" for ML models and high-performance dashboard visualizations.
*   **Measures:** `total_demand`, `total_revenue_generated`, `average_trip_distance`.

---

## 4. Operational Excellence & Performance Optimization

### 4.1. The "Two-Pass" Execution Strategy
To handle FHVHV data (5M+ rows) without memory overflow on local hardware:
1.  **Pass 1 (Streaming Clean):** Data is read via `scan_parquet`, cleaned, and immediately "Sunk" to the disk using `sink_parquet`. This breaks the long calculation chain and flushes RAM.
2.  **Pass 2 (Atomic Aggregation):** The pipeline re-reads the cleaned file to perform hourly aggregations.

### 4.2. Monitoring & Logging
Every run generates an `etl_report_summary.csv` containing raw vs. cleaned row counts and ingestion status.
