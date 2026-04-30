import polars as pl
from datetime import datetime

def standardize_columns(lf):
    """Chiến lược Wide Table: Chỉ chuẩn hóa tên các cột CORE KEYS, giữ nguyên các cột khác."""
    cols = lf.collect_schema().names()
    # Chuyển tất cả về chữ thường
    lf = lf.rename({col: col.lower() for col in cols})
    cols_lower = [col.lower() for col in cols]
    
    col_map = {}
    
    # 1. Thống nhất các cột Thời gian (Core)
    if "tpep_pickup_datetime" in cols_lower: col_map["tpep_pickup_datetime"] = "pickup_time"
    elif "lpep_pickup_datetime" in cols_lower: col_map["lpep_pickup_datetime"] = "pickup_time"
    elif "pickup_datetime" in cols_lower: col_map["pickup_datetime"] = "pickup_time"

    if "tpep_dropoff_datetime" in cols_lower: col_map["tpep_dropoff_datetime"] = "dropoff_time"
    elif "lpep_dropoff_datetime" in cols_lower: col_map["lpep_dropoff_datetime"] = "dropoff_time"
    elif "dropoff_datetime" in cols_lower: col_map["dropoff_datetime"] = "dropoff_time"

    # 2. Thống nhất các cột Không gian (Core)
    for col in cols_lower:
        if "pulocationid" in col: col_map[col] = "pulocationid"
        if "dolocationid" in col: col_map[col] = "dolocationid"
        if "passenger_count" in col: col_map[col] = "passenger_count"

    return lf.rename(col_map)

def apply_cleaning_logic(lf, category):
    """Additive Transformation: Tạo cột ML_Unified mà không làm mất cột gốc."""
    start_date = datetime(2025, 6, 1)
    end_date = datetime(2025, 11, 30, 23, 59, 59)
    
    service_map = {"yellow": 1, "green": 2, "fhv": 3, "fhvhv": 4}
    service_key = service_map.get(category.lower(), 0)
    cols = lf.collect_schema().names()

    # 1. Tạo các cột ML Unified (Dành riêng cho Aggregation/AI)
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
    else: # FHV
        lf = lf.with_columns([
            pl.lit(0.0).alias("ml_unified_fare"),
            pl.lit(0.0).alias("ml_unified_distance")
        ])

    # 2. Logic làm giàu dữ liệu chung
    lf = lf.with_columns([
        pl.col("pulocationid").fill_null(264).cast(pl.Int64),
        pl.col("dolocationid").fill_null(264).cast(pl.Int64),
        pl.lit(service_key).cast(pl.Int64).alias("service_type_key")
    ])

    # 3. Tính toán thời lượng (Nếu có đủ cột thời gian)
    if "pickup_time" in cols and "dropoff_time" in cols:
        lf = lf.with_columns([
            ((pl.col("dropoff_time") - pl.col("pickup_time")).dt.total_seconds() / 60).alias("ml_unified_duration")
        ])
    else:
        lf = lf.with_columns(pl.lit(0.0).alias("ml_unified_duration"))

    # 4. Filter dựa trên cột Unified (Không làm mất cột gốc)
    lf = lf.filter(
        (pl.col("pickup_time").is_between(start_date, end_date)) &
        (pl.col("ml_unified_distance") >= 0)
    )

    # 5. Tạo khóa thời gian
    lf = lf.with_columns([
        pl.col("pickup_time").dt.strftime("%Y%m%d%H").cast(pl.Int64).alias("pickup_time_key"),
        pl.col("dropoff_time").dt.strftime("%Y%m%d%H").cast(pl.Int64).alias("dropoff_time_key") if "dropoff_time" in cols else pl.lit(None).cast(pl.Int64).alias("dropoff_time_key")
    ])

    return lf

def aggregate_trips(lf):
    """Aggregate dựa trên các cột ML Unified - Đảm bảo sạch cho AI."""
    lf_safe = lf.filter(pl.col("pulocation_id").is_not_null() & pl.col("pickup_time_key").is_not_null())
    
    return lf_safe.group_by(["pickup_time_key", "pulocation_id", "service_type_key"]).agg([
        pl.len().alias("total_demand"),
        pl.col("ml_unified_fare").sum().alias("total_revenue_generated"),
        pl.col("ml_unified_distance").mean().alias("average_trip_distance"),
        pl.col("ml_unified_duration").mean().alias("average_duration")
    ]).sort(["pickup_time_key", "pulocation_id"])
