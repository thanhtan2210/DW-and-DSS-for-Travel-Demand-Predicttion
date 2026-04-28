# ETL Technical Specification: High-Performance Data Engineering

This document outlines the technical implementation details of the NYC Taxi ETL pipeline, with a focus on memory-efficient processing of multi-million row datasets.

## 1. Unified Schema Architecture
To enable seamless cross-category analysis (UNION operations) on BigQuery, the pipeline enforces a consistent framework across all data sources:
*   **Yellow/Green:** Legacy meter-based columns.
*   **FHV:** Traditional dispatch data (high nullity).
*   **FHVHV:** High-volume app data (complex timelines).

## 2. Advanced Transformation Logic

### 2.1. The "Safety First" Approach (LazyFrame)
We use Polars `LazyFrame` for all transformations. This ensures that column renaming, filtering, and feature engineering are only mapped out, not executed immediately.

### 2.2. Timeline Integrity (FHVHV Focus)
To handle the "Ma trận thời gian" (4+ timestamps), the pipeline explicitly prioritizes:
1.  `pickup_datetime` -> `pickup_time`
2.  `dropoff_datetime` -> `dropoff_time`
This ensures `duration_minutes` is calculated correctly based on actual passenger presence in the vehicle.

### 2.3. Smart Imputation (Maintaining Demand Signals)
*   **Location Mapping:** Missing IDs are filled with **264 (Unknown)** to keep the trip record for forecasting while maintaining join safety.
*   **Flag Normalization:** Null flags in Uber/Lyft data are converted to **'N'** to provide a clean categorical input for Machine Learning.

## 3. High-Performance Loading Strategy

### 3.1. Raw Ingestion (Direct Stream)
*   Raw files are pushed directly to BigQuery using the Python Client.
*   **Performance:** This is an I/O-bound task that does not stress the local machine's RAM.

### 3.2. Cleaned Ingestion (The Streaming Solution)
Cleaning FHVHV data (2M - 5M rows) traditionally causes system freezes due to RAM overflow. We solve this by:
*   **`sink_parquet()`:** Instead of materializing the entire cleaned dataset in memory (`collect()`), the data is streamed directly to the local disk in chunks.
*   **Memory Footprint:** RAM remains stable, allowing the ETL to process any file size regardless of local hardware specs.

### 3.3. Destination Management (Dual Ingestion)
*   **`BQ_DATASET_ID`**: Holds raw, unfiltered data for auditing.
*   **`BQ_CLEANED_DATASET_ID`**: Holds standardized, filtered, and aggregated data for production forecasting.

## 4. Monitoring & Error Handling
*   **`etl_report_summary.csv`**: A single source of truth for tracking row retention and ingestion status.
*   **Performance Toggles**: Command-line flags `--cat` and `--threads` allow users to downscale the process for lower-end hardware.
