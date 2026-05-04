import polars as pl
from datetime import datetime

def standardize_columns(lf):
    """Wide Table Strategy: Normalizes CORE KEYS while preserving original attributes."""
    cols = lf.collect_schema().names()
    lf = lf.rename({col: col.lower() for col in cols})
    cols_lower = [col.lower() for col in cols]
    
    col_map = {}
    
    # 1. Temporal Key Unification
    if "tpep_pickup_datetime" in cols_lower: col_map["tpep_pickup_datetime"] = "pickup_time"
    elif "lpep_pickup_datetime" in cols_lower: col_map["lpep_pickup_datetime"] = "pickup_time"
    elif "pickup_datetime" in cols_lower: col_map["pickup_datetime"] = "pickup_time"

    if "tpep_dropoff_datetime" in cols_lower: col_map["tpep_dropoff_datetime"] = "dropoff_time"
    elif "lpep_dropoff_datetime" in cols_lower: col_map["lpep_dropoff_datetime"] = "dropoff_time"
    elif "dropoff_datetime" in cols_lower: col_map["dropoff_datetime"] = "dropoff_time"

    # 2. Spatial Key Unification (Standardizing pulocationid/dolocationid)
    for col in cols_lower:
        if "pulocationid" in col: col_map[col] = "pulocationid"
        if "dolocationid" in col: col_map[col] = "dolocationid"
        if "passenger_count" in col: col_map[col] = "passenger_count"

    return lf.rename(col_map)

def apply_cleaning_logic(lf, category):
    """Additive Transformation: Creates Unified ML features without data loss."""
    start_date = datetime(2025, 6, 1)
    end_date = datetime(2025, 11, 30, 23, 59, 59)
    
    service_map = {"yellow": 1, "green": 2, "fhv": 3, "fhvhv": 4}
    service_key = service_map.get(category.lower(), 0)
    cols = lf.collect_schema().names()

    # 1. Feature Unification for Aggregation/ML
    if category in ["yellow", "green"]:
        lf = lf.with_columns([
            pl.col("fare_amount").alias("ml_unified_fare"),
            pl.col("trip_distance").alias("ml_unified_distance")
        ])
    elif category == "fhvhv":
        lf = lf.with_columns([
            pl.col("base_passenger_fare").alias("ml_unified_fare"),
            pl.col("trip_miles").alias("ml_unified_distance")
        ])
    else: # FHV base case
        lf = lf.with_columns([
            pl.lit(0.0).alias("ml_unified_fare"),
            pl.lit(0.0).alias("ml_unified_distance")
        ])

    # 2. Enrichment & Reference Integrity
    lf = lf.with_columns([
        pl.col("pulocationid").fill_null(264).cast(pl.Int64),
        pl.col("dolocationid").fill_null(264).cast(pl.Int64),
        pl.lit(service_key).cast(pl.Int64).alias("service_type_key")
    ])

    # 3. Trip Duration Calculation
    if "pickup_time" in cols and "dropoff_time" in cols:
        lf = lf.with_columns([
            ((pl.col("dropoff_time") - pl.col("pickup_time")).dt.total_seconds() / 60).alias("ml_unified_duration")
        ])
    else:
        lf = lf.with_columns(pl.lit(0.0).alias("ml_unified_duration"))

    # 4. Quality Filtering (Additive Principle: filter on unified columns)
    lf = lf.filter(
        (pl.col("pickup_time").is_between(start_date, end_date)) &
        (pl.col("ml_unified_distance") >= 0)
    )

    # 5. Star Schema Key Generation
    lf = lf.with_columns([
        pl.col("pickup_time").dt.strftime("%Y%m%d%H").cast(pl.Int64).alias("pickup_time_key"),
        pl.col("dropoff_time").dt.strftime("%Y%m%d%H").cast(pl.Int64).alias("dropoff_time_key") if "dropoff_time" in cols else pl.lit(None).cast(pl.Int64).alias("dropoff_time_key")
    ])

    return lf

def aggregate_trips(lf):
    """Summarizes trip data into Hourly/Zone grain for ML Feature Store."""
    lf_safe = lf.filter(pl.col("pulocationid").is_not_null() & pl.col("pickup_time_key").is_not_null())
    
    return lf_safe.group_by(["pickup_time_key", "pulocationid", "service_type_key"]).agg([
        pl.len().alias("total_demand"),
        pl.col("ml_unified_fare").sum().alias("total_revenue_generated"),
        pl.col("ml_unified_distance").mean().alias("average_trip_distance"),
        pl.col("ml_unified_duration").mean().alias("average_duration")
    ]).sort(["pickup_time_key", "pulocationid"])
