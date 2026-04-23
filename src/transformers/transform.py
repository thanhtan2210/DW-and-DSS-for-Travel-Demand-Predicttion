import polars as pl
from datetime import datetime

def standardize_columns(df):
    """Normalize column names across different taxi/fhv datasets."""
    # Lowercase all columns
    df = df.rename({col: col.lower() for col in df.columns})
    
    col_map = {}
    for col in df.columns:
        if "pickup_datetime" in col: col_map[col] = "pickup_time"
        if "dropoff_datetime" in col: col_map[col] = "dropoff_time"
        if col in ["trip_distance", "trip_miles"]: col_map[col] = "distance"
        if col in ["fare_amount", "base_passenger_fare"]: col_map[col] = "fare"
        if "pulocation" in col: col_map[col] = "pulocationid"
        if "dolocation" in col: col_map[col] = "dolocationid"
        if "passenger_count" in col: col_map[col] = "passenger_count"
    
    # Rename only columns that need mapping
    actual_map = {old: new for old, new in col_map.items() if old != new and old in df.columns}
    return df.rename(actual_map)

def apply_cleaning_logic(df, category):
    """Apply business logic and cleaning rules derived from EDA findings."""
    start_date = datetime(2025, 6, 1)
    end_date = datetime(2025, 11, 30, 23, 59, 59)
    
    # Danh sách ngày lễ Mỹ 2025 (Jun - Nov)
    holidays = [
        datetime(2025, 6, 19).date(),  # Juneteenth
        datetime(2025, 7, 4).date(),   # Independence Day
        datetime(2025, 9, 1).date(),   # Labor Day
        datetime(2025, 10, 13).date(), # Columbus Day
        datetime(2025, 11, 11).date(), # Veterans Day
        datetime(2025, 11, 27).date(), # Thanksgiving
    ]
    
    # 1. Xử lý cột rỗng 100%
    null_counts = df.null_count()
    cols_to_drop = [col for col in df.columns if null_counts[col][0] == df.height and df.height > 0]
    if cols_to_drop:
        df = df.drop(cols_to_drop)

    # 2. Critical Filters & Imputation
    df = df.filter(pl.col("pickup_time").is_not_null())
    df = df.filter(pl.col("pickup_time").is_between(start_date, end_date))
    
    df = df.with_columns([
        pl.col("pulocationid").fill_null(264).cast(pl.Int64),
        pl.col("dolocationid").fill_null(264).cast(pl.Int64)
    ])
    
    # 3. Taxi Specific Outlier Filtering (Yellow & Green)
    if category in ["yellow", "green"]:
        if category == "green" and "ehail_fee" in df.columns:
            df = df.drop("ehail_fee")
            
        df = df.filter(
            pl.col("passenger_count").is_not_null() | pl.col("fare").is_not_null()
        )

        df = df.filter(
            (pl.col("passenger_count").fill_null(1).is_between(1, 6)) &
            (pl.col("distance").fill_null(0).is_between(0.1, 50)) & 
            (pl.col("fare").fill_null(0).is_between(2.5, 500))
        )
        
        if "trip_type" in df.columns:
            df = df.with_columns(pl.col("trip_type").fill_null(1).cast(pl.Int64))
            
    # 4. App-based Specific Logic (FHVHV)
    if category == "fhvhv":
        fee_cols = ["airport_fee", "tolls", "bcf", "sales_tax", "congestion_surcharge", "tips"]
        flag_cols = ["shared_request_flag", "shared_match_flag", "wav_request_flag", "wav_match_flag"]
        for col in fee_cols:
            if col in df.columns: df = df.with_columns(pl.col(col).fill_null(0.0))
        for col in flag_cols:
            if col in df.columns: df = df.with_columns(pl.col(col).fill_null("N"))
        
        df = df.filter((pl.col("distance").fill_null(0) > 0.1) & (pl.col("distance") < 100))
    
    # 5. Feature Engineering & Business Logic
    if "dropoff_time" in df.columns:
        df = df.with_columns([
            ((pl.col("dropoff_time") - pl.col("pickup_time")).dt.total_seconds() / 60).alias("duration_minutes")
        ])
        df = df.filter(pl.col("duration_minutes").is_between(1, 180))
        
    # Create Time Key và các cờ nghiệp vụ
    df = df.with_columns([
        pl.col("pickup_time").dt.strftime("%Y%m%d%H").cast(pl.Int64).alias("time_key"),
        pl.col("pickup_time").dt.date().is_in(holidays).cast(pl.Int8).alias("is_holiday"),
        (pl.col("pickup_time").dt.weekday() >= 6).cast(pl.Int8).alias("is_weekend")
    ])

    # 6. Loại bỏ trùng lặp (Duplicates)
    df = df.unique()

    return df


def aggregate_trips(df):
    """Aggregate dữ liệu theo PULocationID + Hour (Demand Prediction Grain)."""
    # Group by Location và Time Key (YYYYMMDDHH)
    agg_df = df.group_by(["pulocationid", "time_key"]).agg([
        pl.len().alias("trip_count"),
        pl.col("passenger_count").mean().alias("avg_passengers") if "passenger_count" in df.columns else pl.lit(None),
        pl.col("distance").mean().alias("avg_distance") if "distance" in df.columns else pl.lit(None),
        pl.col("is_holiday").first().alias("is_holiday"),
        pl.col("is_weekend").first().alias("is_weekend")
    ]).sort(["time_key", "pulocationid"])
    
    return agg_df
