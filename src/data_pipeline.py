import os
import polars as pl
import pandas as pd
import gc
from .extractors.extract import get_files, scan_data
from .transformers import polars_engine, bq_engine
from .loaders.local import ensure_output_dir, save_data, sink_data
from .loaders.bigquery import load_parquet_to_bq
from .loaders.bigquery_dims import (
    load_dim_location_to_bq, load_dim_time_to_bq, 
    load_dim_service_type_to_bq, load_dim_weather_to_bq
)
from .loaders.bigquery_facts import load_to_fact_trips, load_to_fact_demand_hourly

def run_pipeline(engine="polars", load_raw=False, load_clean=False, load_dims=False, target_cat=None):
    """Orchestrator: Điều phối luồng chạy dựa trên Engine được chọn."""
    print("="*60)
    print(f"NYC TAXI - ETL PIPELINE (Engine: {engine.upper()})")
    print("="*60)

    # --- 1. NẠP DIMENSIONS (Dùng chung cho cả 2 engine) ---
    if load_dims:
        run_dimensions_load()

    # --- 2. XỬ LÝ DỮ LIỆU CHÍNH (FACTS) ---
    all_categories = ["yellow", "green", "fhv", "fhvhv"]
    categories = [target_cat] if target_cat else all_categories

    # Khởi tạo Schema trước khi xử lý Fact data (để tránh lỗi mismatch kiểu dữ liệu)
    if load_clean or engine == "bigquery":
        bq_engine.execute_sql_file("sql/ddl_create_tables.sql")

    if engine == "polars":
        for cat in categories:
            run_local_polars_etl(cat, load_raw, load_clean)
    elif engine == "bigquery":
        for cat in categories:
            run_cloud_bq_elt(cat, load_raw)
    else:
        print(f"[ERROR] Engine '{engine}' không được hỗ trợ.")

def run_dimensions_load():
    """Nạp các bảng Dimension lên BigQuery."""
    lookup_csv = os.getenv("TAXI_ZONE_LOOKUP", "dataset/taxi_zone_lookup.csv")
    print("\n>>> Đang nạp các bảng Dimension...")
    try:
        load_dim_location_to_bq(lookup_csv)
        load_dim_time_to_bq()
        load_dim_service_type_to_bq()
        load_dim_weather_to_bq()
    except Exception as e:
        print(f"   [ERROR] Không thể nạp bảng Dimension: {e}")

def run_local_polars_etl(cat, load_raw, load_clean):
    """PHIÊN BẢN 1: Local ETL sử dụng Polars."""
    input_base = os.getenv("RAW_DATA_DIR", "dataset/Trip_Record")
    output_base = os.getenv("PROCESSED_DATA_DIR", "dataset/processed")
    
    files = get_files(input_base, cat)
    output_dir = ensure_output_dir(output_base, cat)
    agg_output_dir = ensure_output_dir(output_base, f"aggregated/{cat}")
    
    print(f"\n>>> [Polars] Đang xử lý: {cat.upper()} ({len(files)} files)")
    
    for file_path in files:
        file_name = os.path.basename(file_path)
        try:
            # 1. Extract & Optional Raw Load
            lf_raw = scan_data(file_path)
            if load_raw:
                load_parquet_to_bq(file_path, cat, is_raw=True)
            
            # 2. Transform (Additive Logic)
            lf_std = polars_engine.standardize_columns(lf_raw)
            lf_cleaned = polars_engine.apply_cleaning_logic(lf_std, cat)
            
            # 3. Load (Streaming Sink)
            saved_path = sink_data(lf_cleaned, output_dir, file_name)
            
            if load_clean:
                # Load Transactional Fact
                load_to_fact_trips(saved_path)
                
                # 4. Aggregate Local (Two-Pass)
                lf_agg = polars_engine.aggregate_trips(pl.scan_parquet(saved_path))
                df_agg_final = lf_agg.collect()
                agg_saved_path = save_data(df_agg_final, agg_output_dir, f"agg_{file_name}")
                
                # Load Aggregated Fact
                load_to_fact_demand_hourly(agg_saved_path)
            
            gc.collect()
        except Exception as e:
            print(f"   [ERROR] {file_name}: {e}")

def run_cloud_bq_elt(cat, load_raw):
    """PHIÊN BẢN 2: Cloud ELT sử dụng BigQuery SQL."""
    input_base = os.getenv("RAW_DATA_DIR", "dataset/Trip_Record")
    files = get_files(input_base, cat)

    # Mapping tên cột thực tế cho từng category
    col_mapping = {
        "yellow": {
            "pickup": "tpep_pickup_datetime", "dropoff": "tpep_dropoff_datetime",
            "dist": "trip_distance", "fare": "fare_amount", "pass": "passenger_count"
        },
        "green": {
            "pickup": "lpep_pickup_datetime", "dropoff": "lpep_dropoff_datetime",
            "dist": "trip_distance", "fare": "fare_amount", "pass": "passenger_count"
        },
        "fhvhv": {
            "pickup": "pickup_datetime", "dropoff": "dropoff_datetime",
            "dist": "trip_miles", "fare": "base_passenger_fare", "pass": "CAST(NULL AS INT64)"
        },
        "fhv": {
            "pickup": "pickup_datetime", "dropoff": "dropoff_datetime",
            "dist": "CAST(NULL AS FLOAT64)", "fare": "CAST(NULL AS FLOAT64)", "pass": "CAST(NULL AS INT64)"
        }
    }

    mapping = col_mapping.get(cat.lower())
    service_map = {"yellow": 1, "green": 2, "fhv": 3, "fhvhv": 4}
    service_key = service_map.get(cat.lower(), 0)

    print(f"\n>>> [BigQuery] Category: {cat.upper()}")

    # 1. Load to Staging (Skip if already uploaded)
    if load_raw:
        print(f"    [STAGING] Đang đẩy {len(files)} file thô lên Cloud...")
        for file_path in files:
            load_parquet_to_bq(file_path, cat, is_raw=True)
    else:
        print(f"    [STAGING] Bỏ qua bước nạp Raw (Dữ liệu đã có sẵn).")

    # 2. Transform & Aggregate trên Cloud
    params = {
        "CATEGORY": cat, 
        "SERVICE_TYPE_KEY": service_key,
        "COL_PICKUP": mapping["pickup"],
        "COL_DROPOFF": mapping["dropoff"],
        "COL_DIST": mapping["dist"],
        "COL_FARE": mapping["fare"],
        "COL_PASS": mapping["pass"]
    }

    # Chạy SQL biến đổi (Staging -> Fact_Trips)
    bq_engine.execute_sql_file("sql/transform_generic.sql", params=params)

    # Chạy SQL tổng hợp (Fact_Trips -> Fact_Demand_Hourly)
    bq_engine.execute_sql_file("sql/aggregate_demand.sql", params=params)
