-- SQL: Tạo bảng Fact_Trips nếu chưa tồn tại
CREATE
OR REPLACE TABLE `{{PROJECT_ID}}.{{DW_DATASET}}.Fact_Trips` (
    pickup_time_key INT64,
    dropoff_time_key INT64,
    pulocationid INT64,
    dolocationid INT64,
    service_type_key INT64,
    distance FLOAT64,
    fare FLOAT64,
    duration_minutes FLOAT64,
    passenger_count INT64
);

-- SQL: Tạo bảng Fact_Demand_Hourly nếu chưa tồn tại
CREATE
OR REPLACE TABLE `{{PROJECT_ID}}.{{DW_DATASET}}.Fact_Demand_Hourly` (
    pickup_time_key INT64,
    pulocationid INT64,
    service_type_key INT64,
    total_demand INT64,
    total_revenue_generated FLOAT64,
    average_trip_distance FLOAT64,
    average_duration FLOAT64
);