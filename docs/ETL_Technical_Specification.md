# ETL Technical Specification: High-Performance Data Engineering

This document outlines the technical implementation details of the NYC Taxi ETL pipeline, with a focus on hybrid processing (Local vs Cloud).

## 1. Unified Schema Architecture
To enable seamless cross-category analysis, the pipeline enforces a consistent "Gold Schema" framework across all data sources:
*   **Temporal**: `pickup_time`, `dropoff_time` (standardized timestamps).
*   **Geospatial**: `pulocationid`, `dolocationid` (NYC Taxi Zone IDs).
*   **Quantitative**: `distance` (miles), `fare` (base fare), `passenger_count`.
*   **Categorical**: `service_type_key` (1-Yellow, 2-Green, 3-FHV, 4-FHVHV).

## 2. Advanced Transformation Logic

### 2.1. Local Engine: Polars Streaming API
We use Polars `LazyFrame` for all local transformations to minimize the memory footprint:
- **`sink_parquet()`**: Instead of materializing results in RAM, data is streamed directly to the local disk.
- **Two-Pass Execution**: The system cleans data in Pass 1 and performs aggregations in Pass 2 to maintain peak performance on FHVHV datasets (5M+ rows).

### 2.2. Cloud Engine: BigQuery SQL ELT
For massive datasets or cloud-native workflows, the pipeline utilizes SQL templates:
- **Generic Transform**: Applies the Gold Schema and cleaning rules via BigQuery SQL.
- **Aggregation**: Leverages BigQuery's distributed compute to generate `Fact_Demand_Hourly`.

## 3. Destination Management (Dual Ingestion)
The pipeline populates two distinct zones in the Data Warehouse:
*   **Staging Area**: Holds raw, unfiltered Parquet data for auditing and history.
*   **Production DW**: Holds the Star Schema tables (`Fact_Trips`, `Fact_Demand_Hourly`) ready for DSS and ML.

## 4. Monitoring & Error Handling
*   **`etl_report_summary.csv`**: Tracks row retention (Raw vs Cleaned) and ingestion success.
*   **Garbage Collection**: Explicit `gc.collect()` calls in the Polars loop prevent memory leakage across multiple file iterations.
