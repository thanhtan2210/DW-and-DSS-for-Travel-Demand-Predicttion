# Comprehensive Engineering Blueprint: NYC Taxi DSS in Power BI

This document provides a technical guide to implementing a professional-grade Decision Support System using the Star Schema from BigQuery.

---

## Phase 1: Data Infrastructure & Modeling

### 1.1. Ingestion Strategy
1.  **Home** > **Get Data** > **Google BigQuery**.
2.  **Navigator Window**: Select `Dim_Time`, `Dim_Location`, `Dim_Service_Type`, `Dim_Weather`, `Fact_Demand_Hourly` (Main), and `Fact_Trips` (Optional).
3.  **Storage Mode Selection**:
    - **Import**: `Dim_Time`, `Dim_Location`, `Dim_Service_Type`, `Dim_Weather`, `Fact_Demand_Hourly`.
        *Reason: Importing the aggregated fact table allows for lightning-fast interactivity and complex DAX measures.*
    - **DirectQuery**: `Fact_Trips`.
        *Reason: This table contains millions of rows. Use DirectQuery only for granular "Drill-through" pages to avoid bloating the .pbix file.*

### 1.2. Crucial Table Configurations (Power Query)
1.  **Dim_Time**: Ensure `Time_Key` is a **Whole Number** and `Full_Date` is a **Date**.
2.  **Fact_Demand_Hourly**: Ensure `pickup_time_key` and `pulocationid` match the types in the Dimension tables.

### 1.3. Relationship Integrity (Model View)
1.  **Mark as Date Table**: Right-click `Dim_Time` > **Mark as date table** > Select `Full_Date`.
2.  **The Star Schema Joins**:
    - `Dim_Time[Time_Key]` (1) to `Fact_Demand_Hourly[pickup_time_key]` (*)
    - `Dim_Location[Location_ID]` (1) to `Fact_Demand_Hourly[pulocationid]` (*)
    - `Dim_Service_Type[Service_Type_Key]` (1) to `Fact_Demand_Hourly[service_type_key]` (*)

---

## Phase 2: The DAX Analytical Engine

### 2.1. Basic Metrics
```dax
Total Trips = SUM('Fact_Demand_Hourly'[total_demand])

Total Revenue = SUM('Fact_Demand_Hourly'[total_revenue_generated])

Avg Trip Dist = AVERAGE('Fact_Demand_Hourly'[average_trip_distance])
```

### 2.2. Advanced Time Intelligence
```dax
Demand 7-Day Moving Avg = 
AVERAGEX(
    DATESINPERIOD('Dim_Time'[Full_Date], LASTDATE('Dim_Time'[Full_Date]), -7, DAY),
    [Total Trips]
)
```

---

## Phase 3: Visual Engineering (The 4-Tab Layout)

### 3.1. Temporal Dynamics
- **Line Chart**: X-Axis: `Full_Date`, Y-Axis: `Total Trips`.
- **Heatmap Matrix**: Rows: `Day_of_Week`, Columns: `Hour`, Values: `Total Trips`.

### 3.2. Spatial View
- **Map Visual**: Location: `Borough` or `Zone`, Size: `Total Trips`, Color: `Total Revenue`.

### 3.3. Financial Flows
- **Sunburst/Treemap**: Hierarchy: `Borough` > `Service_Name`, Values: `Total Revenue`.

### 3.4. Model Validation
- **Actual vs Forecast**: Line chart comparing historical `Total Trips` against predictions exported from the ML pipeline.
