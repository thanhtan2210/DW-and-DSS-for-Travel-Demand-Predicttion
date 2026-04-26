import polars as pl
from datetime import datetime

def standardize_columns(lf):
    """Chuẩn hóa tên cột cho LazyFrame với hiệu năng tối ưu."""
    cols = lf.collect_schema().names()
    lf = lf.rename({col: col.lower() for col in cols})
    cols_lower = [col.lower() for col in cols]
    
    col_map = {}
    pickup_candidates = ["pickup_datetime", "tpep_pickup_datetime", "lpep_pickup_datetime"]
    for cand in pickup_candidates:
        if cand in cols_lower:
            col_map[cand] = "pickup_time"
            break
            
    dropoff_candidates = ["dropoff_datetime", "tpep_dropoff_datetime", "lpep_dropoff_datetime"]
    for cand in dropoff_candidates:
        if cand in cols_lower:
            col_map[cand] = "dropoff_time"
            break

    for col in cols_lower:
        if col not in col_map.keys() and col not in col_map.values():
            if col in ["trip_distance", "trip_miles"]: col_map[col] = "distance"
            if col in ["fare_amount", "base_passenger_fare"]: col_map[col] = "fare"
            if "pulocation" in col: col_map[col] = "pulocationid"
            if "dolocation" in col: col_map[col] = "dolocationid"
            if "passenger_count" in col: col_map[col] = "passenger_count"
    
    return lf.rename(col_map)

def apply_cleaning_logic(lf, category):
    """Hiện thực hóa kịch bản ETL trên LazyFrame."""
    start_date = datetime(2025, 6, 1)
    end_date = datetime(2025, 11, 30, 23, 59, 59)
    
    cols = lf.collect_schema().names()

    # 1. Ép khung Schema chuẩn
    essential_cols = {
        "pulocationid": pl.Int64,
        "dolocationid": pl.Int64,
        "passenger_count": pl.Float64,
        "distance": pl.Float64,
        "fare": pl.Float64
    }
    for col, dtype in essential_cols.items():
        if col not in cols:
            lf = lf.with_columns(pl.lit(None).cast(dtype).alias(col))

    # 2. Critical Filters
    lf = lf.filter(pl.col("pickup_time").is_not_null())
    lf = lf.filter(pl.col("pickup_time").is_between(start_date, end_date))
    
    # 3. Imputation (Mã 264 Unknown)
    lf = lf.with_columns([
        pl.col("pulocationid").fill_null(264).cast(pl.Int64),
        pl.col("dolocationid").fill_null(264).cast(pl.Int64)
    ])
    
    # 4. Taxi/App Outlier Filtering
    if category in ["yellow", "green"]:
        lf = lf.filter(
            (pl.col("distance").fill_null(0).is_between(0.1, 50)) & 
            (pl.col("fare").fill_null(0).is_between(2.5, 500))
        )
    elif category == "fhvhv":
        flag_cols = ["shared_request_flag", "shared_match_flag", "wav_request_flag", "wav_match_flag"]
        for col in flag_cols:
            if col in cols: 
                lf = lf.with_columns(pl.col(col).cast(pl.String).fill_null("N"))
        lf = lf.filter((pl.col("distance").fill_null(0) > 0.1) & (pl.col("distance") < 100))

    # 5. Feature Engineering
    if "dropoff_time" in cols:
        lf = lf.with_columns([
            ((pl.col("dropoff_time") - pl.col("pickup_time")).dt.total_seconds() / 60).alias("duration_minutes")
        ])
        lf = lf.filter(pl.col("duration_minutes").is_between(1, 180))

    # 6. Tạo khóa Star Schema
    lf = lf.with_columns([
        pl.col("pickup_time").dt.strftime("%Y%m%d%H").cast(pl.Int64).alias("time_key"),
        (pl.col("pickup_time").dt.weekday() >= 6).cast(pl.Int8).alias("is_weekend")
    ])

    return lf.unique()

def aggregate_trips(lf):
    """
    Aggregate dữ liệu theo Grain: 1 Giờ + 1 Khu vực đón (PULocationID).
    Measures: trips, revenue, distance.
    """
    # Loại bỏ Null khóa để bảo vệ tính toàn vẹn của Star Schema
    lf_safe = lf.filter(pl.col("pulocationid").is_not_null() & pl.col("time_key").is_not_null())
    
    return lf_safe.group_by(["pulocationid", "time_key"]).agg([
        pl.len().alias("trip_count"),                                     # Measure: trips
        pl.col("fare").fill_null(0).sum().cast(pl.Float64).alias("total_revenue"), # Measure: revenue
        pl.col("distance").fill_null(0).sum().cast(pl.Float64).alias("total_distance"), # Measure: distance
        pl.col("passenger_count").fill_null(1).mean().alias("avg_passengers")
    ]).sort(["time_key", "pulocationid"])
