-- SQL: Create Feature Engineering View/Table in BigQuery
-- This offloads lag/rolling calculations from local RAM to BigQuery
CREATE OR REPLACE TABLE `{{PROJECT_ID}}.{{DW_DATASET}}.Feature_Engineered_Demand` AS
WITH BaseData AS (
    SELECT 
        f.pickup_time_key,
        f.pulocationid,
        f.total_demand,
        t.hour,
        t.day_of_week_number,
        t.is_weekend
    FROM `{{PROJECT_ID}}.{{DW_DATASET}}.Fact_Demand_Hourly` f
    JOIN `{{PROJECT_ID}}.{{DW_DATASET}}.Dim_Time` t ON f.pickup_time_key = t.Time_Key
),
LaggedData AS (
    SELECT *,
        LAG(total_demand, 1) OVER (PARTITION BY pulocationid ORDER BY pickup_time_key) as lag_demand_1h,
        LAG(total_demand, 2) OVER (PARTITION BY pulocationid ORDER BY pickup_time_key) as lag_demand_2h,
        LAG(total_demand, 24) OVER (PARTITION BY pulocationid ORDER BY pickup_time_key) as lag_demand_24h,
        LAG(total_demand, 168) OVER (PARTITION BY pulocationid ORDER BY pickup_time_key) as lag_demand_168h,
        AVG(total_demand) OVER (PARTITION BY pulocationid ORDER BY pickup_time_key ROWS BETWEEN 5 PRECEDING AND CURRENT ROW) as rolling_mean_6h
    FROM BaseData
)
SELECT *,
    -- Cyclical Features
    SIN(hour * (2.0 * 3.14159 / 24.0)) as hour_sin,
    COS(hour * (2.0 * 3.14159 / 24.0)) as hour_cos,
    SIN(day_of_week_number * (2.0 * 3.14159 / 7.0)) as day_sin,
    COS(day_of_week_number * (2.0 * 3.14159 / 7.0)) as day_cos
FROM LaggedData
WHERE lag_demand_168h IS NOT NULL;
