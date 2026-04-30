-- SQL: Wide Table Transformation (Additive Approach)
-- This query keeps ALL raw columns while adding ML-unified columns for aggregation

CREATE OR REPLACE TABLE `{{PROJECT_ID}}.{{DW_DATASET}}.Fact_Trips`
AS
SELECT 
    -- 1. Unified ML Columns (Normalized for Aggregation)
    CAST(FORMAT_TIMESTAMP('%Y%m%d%H', {{COL_PICKUP}}) AS INT64) as pickup_time_key,
    CAST(FORMAT_TIMESTAMP('%Y%m%d%H', {{COL_DROPOFF}}) AS INT64) as dropoff_time_key,
    COALESCE(pulocationid, 264) as pulocation_id,
    COALESCE(dolocationid, 264) as dolocation_id,
    {{SERVICE_TYPE_KEY}} as service_type_key,
    CAST({{COL_DIST}} AS FLOAT64) as ml_unified_distance,
    CAST({{COL_FARE}} AS FLOAT64) as ml_unified_fare,
    TIMESTAMP_DIFF({{COL_DROPOFF}}, {{COL_PICKUP}}, MINUTE) as ml_unified_duration,
    
    -- 2. Keep ALL original columns for Data Analysts (Wide Table)
    * 
FROM `{{PROJECT_ID}}.{{STAGING_DATASET}}.raw_{{CATEGORY}}`
WHERE {{COL_PICKUP}} BETWEEN '2025-06-01' AND '2025-11-30 23:59:59';
