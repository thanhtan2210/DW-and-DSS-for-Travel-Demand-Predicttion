-- SQL: Incremental Transformation (Additive Approach)
-- This query clears existing data for the current category and inserts standardized records

DELETE FROM `{{PROJECT_ID}}.{{DW_DATASET}}.Fact_Trips`
WHERE service_type_key = {{SERVICE_TYPE_KEY}};

INSERT INTO `{{PROJECT_ID}}.{{DW_DATASET}}.Fact_Trips` (
    pickup_time_key, dropoff_time_key, pulocationid, dolocationid, service_type_key, 
    distance, fare, duration_minutes, passenger_count
)
SELECT 
    CAST(FORMAT_TIMESTAMP('%Y%m%d%H', {{COL_PICKUP}}) AS INT64) as pickup_time_key,
    CAST(FORMAT_TIMESTAMP('%Y%m%d%H', {{COL_DROPOFF}}) AS INT64) as dropoff_time_key,
    COALESCE(PULocationID, 264) as pulocationid,
    COALESCE(DOLocationID, 264) as dolocationid,
    {{SERVICE_TYPE_KEY}} as service_type_key,
    CAST({{COL_DIST}} AS FLOAT64) as distance,
    CAST({{COL_FARE}} AS FLOAT64) as fare,
    TIMESTAMP_DIFF({{COL_DROPOFF}}, {{COL_PICKUP}}, MINUTE) as duration_minutes,
    CAST({{COL_PASS}} AS INT64) as passenger_count
FROM `{{PROJECT_ID}}.{{STAGING_DATASET}}.raw_{{CATEGORY}}`
WHERE {{COL_PICKUP}} BETWEEN '2025-06-01' AND '2025-11-30 23:59:59';
