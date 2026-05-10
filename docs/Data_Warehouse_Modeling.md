# Data Warehouse Modeling: Star Schema Design

To facilitate efficient analytical querying and robust feature engineering for Travel Demand Prediction, the data is structured into a **Star Schema**. This dimensional modeling approach separates quantitative measures (Facts) from descriptive attributes (Dimensions), optimizing the system for high-performance aggregations across spatio-temporal axes.

## 1. Fact Tables

### A. `Fact_Trips` (Atomic Level)
The central table containing grain-level trip observations. Each row represents a single completed trip.

| Column | Type | Description |
| :--- | :--- | :--- |
| `pickup_time_key` | Foreign Key | Reference to `Dim_Time` for the trip start (YYYYMMDDHH). |
| `dropoff_time_key` | Foreign Key | Reference to `Dim_Time` for the trip end. |
| `pulocationid` | Foreign Key | Reference to `Dim_Location` (Pickup Zone). |
| `dolocationid` | Foreign Key | Reference to `Dim_Location` (Drop-off Zone). |
| `service_type_key` | Foreign Key | Reference to `Dim_Service_Type` (Yellow, Green, etc.). |
| **Metrics** | | |
| `distance` | Float | The elapsed trip distance in miles. |
| `fare` | Float | The base fare amount. |
| `duration_minutes`| Float | Calculated trip duration. |
| `passenger_count` | Integer | Number of passengers. |

### B. `Fact_Demand_Hourly` (Aggregate Level)
This table serves as the primary **Feature Store** for Machine Learning models and high-level OLAP reporting.

| Column | Type | Description |
| :--- | :--- | :--- |
| `pickup_time_key` | Primary Key Component | Temporal bucket. |
| `pulocationid` | Primary Key Component | Spatial bucket. |
| `service_type_key` | Primary Key Component | Vehicle category. |
| **Aggregated Metrics** | | |
| `total_demand` | Integer | Total number of trips (Target variable for ML). |
| `total_revenue_generated` | Float | Sum of fares. |
| `average_trip_distance` | Float | Mean miles per trip. |

## 2. Dimension Tables

### `Dim_Time`
This dimension provides the temporal context required for time-series forecasting. It allows for multi-granular analysis of demand patterns (hourly, daily, seasonal).

*   **`Time_Key`**: Primary Key (format: `YYYYMMDDHH`).
*   **`Full_Date`**: Date of the observation.
*   **`Hour`**: Hour of the day (0-23).
*   **`Day`**: Day of the month.
*   **`Month`**: Month of the year.
*   **`Day_of_Week`**: Name or index of the weekday.
*   **`Is_Weekend`**: Boolean flag for Saturday and Sunday.
*   **`Is_Holiday`**: Boolean flag indicating US Federal/Public holidays.

### `Dim_Location`
Derived from the Taxi Zone Lookup table, this dimension maps numeric Location IDs to geographical and administrative boundaries.

*   **`Location_ID`**: Primary Key (matching TLC Taxi Zone IDs).
*   **`Borough`**: Administrative borough (e.g., Manhattan, Brooklyn).
*   **`Zone`**: Specific neighborhood or airport zone.
*   **`Service_Zone`**: Designation for specific taxi service areas.

### `Dim_Weather` (Optional)
Since urban mobility is highly sensitive to environmental conditions, this table provides exogenous variables to improve model accuracy.

*   **`Weather_Key`**: Linked to `Fact_Trips` via Date/Time.
*   **`Precipitation`**: Rainfall or snowfall amounts.
*   **`Temperature`**: Hourly temperature readings.
*   **`Condition`**: Categorical weather state (e.g., Clear, Rain, Snow).

## 3. Design Rationale
The choice of a Star Schema is driven by the need to aggregate millions of records across specific dimensions rapidly. By pre-calculating keys like `Pickup_Time_Key` (at the hourly level) during the ETL process, the system can instantly generate historical demand heatmaps and provide structured inputs for Machine Learning models without expensive runtime joins or complex timestamp manipulations.
