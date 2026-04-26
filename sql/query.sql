CREATE DATABASE NYC_TaxiDW;

GO
    USE NYC_TaxiDW;

GO
    CREATE TABLE stg_yellow (
        vendorid INT,
        pickup_time DATETIME2,
        dropoff_time DATETIME2,
        passenger_count INT,
        distance FLOAT,
        pulocationid INT,
        dolocationid INT,
        fare FLOAT,
        tip_amount FLOAT,
        total_amount FLOAT,
        payment_type INT,
        congestion_surcharge FLOAT,
        duration_minutes FLOAT,
        time_key BIGINT,
        taxi_type NVARCHAR(10) DEFAULT 'yellow'
    );

CREATE TABLE stg_green (
    vendorid INT,
    pickup_time DATETIME2,
    dropoff_time DATETIME2,
    passenger_count INT,
    distance FLOAT,
    pulocationid INT,
    dolocationid INT,
    fare FLOAT,
    tip_amount FLOAT,
    total_amount FLOAT,
    payment_type INT,
    trip_type FLOAT,
    duration_minutes FLOAT,
    time_key BIGINT,
    taxi_type NVARCHAR(10) DEFAULT 'green'
);

CREATE TABLE DimTime (
    time_key BIGINT PRIMARY KEY,
    -- format: YYYYMMDDHH
    pickup_hour INT,
    pickup_date DATE,
    day_of_week INT,
    -- 1=Mon, 7=Sun
    day_name NVARCHAR(20),
    week_of_year INT,
    month_num INT,
    month_name NVARCHAR(20),
    quarter_num INT,
    year_num INT,
    is_weekend BIT,
    is_holiday BIT DEFAULT 0
);

CREATE TABLE DimLocation (
    location_key INT IDENTITY(1, 1) PRIMARY KEY,
    locationid INT UNIQUE,
    borough NVARCHAR(50),
    zone NVARCHAR(100),
    service_zone NVARCHAR(50)
);

CREATE TABLE DimTaxiType (
    taxi_type_key INT IDENTITY(1, 1) PRIMARY KEY,
    taxi_type NVARCHAR(10) UNIQUE,
    -- 'yellow' / 'green'
    description NVARCHAR(100)
);

CREATE TABLE Fact_Trips (
    trip_id BIGINT IDENTITY(1, 1) PRIMARY KEY,
    time_key BIGINT REFERENCES DimTime(time_key),
    pu_location_key INT REFERENCES DimLocation(location_key),
    do_location_key INT REFERENCES DimLocation(location_key),
    taxi_type_key INT REFERENCES DimTaxiType(taxi_type_key),
    passenger_count INT,
    trip_distance FLOAT,
    fare_amount FLOAT,
    tip_amount FLOAT,
    total_amount FLOAT,
    duration_minutes FLOAT,
    payment_type INT
);

INSERT INTO
    DimTaxiType (taxi_type, description)
VALUES
    ('yellow', 'NYC Yellow Medallion Taxi'),
    ('green', 'NYC Green Boro Taxi');

CREATE INDEX idx_fact_time ON Fact_Trips(time_key);

CREATE INDEX idx_fact_puloc ON Fact_Trips(pu_location_key);

CREATE INDEX idx_fact_taxitype ON Fact_Trips(taxi_type_key);

SELECT
    t.month_num,
    t.month_name,
    COUNT(*) AS trip_count
FROM
    Fact_Trips f
    JOIN DimTime t ON f.time_key = t.time_key
GROUP BY
    t.month_num,
    t.month_name
ORDER BY
    t.month_num;