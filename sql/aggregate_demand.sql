-- SQL: Aggregate from Fact_Trips to Fact_Demand_Hourly using Unified ML Columns
DELETE FROM `{{PROJECT_ID}}.{{DW_DATASET}}.Fact_Demand_Hourly`
WHERE service_type_key = {{SERVICE_TYPE_KEY}};

INSERT INTO `{{PROJECT_ID}}.{{DW_DATASET}}.Fact_Demand_Hourly` (
    pickup_time_key, pulocationid, service_type_key, 
    total_demand, total_revenue_generated, average_trip_distance, average_duration
)
SELECT 
    pickup_time_key,
    pulocation_id,
    service_type_key,
    COUNT(*) as total_demand,
    SUM(ml_unified_fare) as total_revenue_generated,
    AVG(ml_unified_distance) as average_trip_distance,
    AVG(ml_unified_duration) as average_duration
FROM `{{PROJECT_ID}}.{{DW_DATASET}}.Fact_Trips`
WHERE service_type_key = {{SERVICE_TYPE_KEY}}
GROUP BY 1, 2, 3;
