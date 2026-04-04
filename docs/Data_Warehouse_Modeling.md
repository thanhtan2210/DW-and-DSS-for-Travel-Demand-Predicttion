# Data Warehouse Modeling: Star Schema Design

To facilitate efficient analytical querying and robust feature engineering for Travel Demand Prediction, the data is structured into a **Star Schema**. This dimensional modeling approach separates quantitative measures (Facts) from descriptive attributes (Dimensions), optimizing the system for high-performance aggregations across spatio-temporal axes.

## 1. Fact Table: `Fact_Trips`
The `Fact_Trips` table is the central table in the schema, containing grain-level trip observations. Each row represents a single completed trip, integrated from both Yellow and Green taxi datasets.

| Column | Type | Description |
| :--- | :--- | :--- |
| `Trip_ID` | Surrogate Key | Unique identifier for each trip. |
| `Pickup_Time_Key` | Foreign Key | Reference to `Dim_Time` for the trip start. |
| `Dropoff_Time_Key` | Foreign Key | Reference to `Dim_Time` for the trip end. |
| `PULocation_Key` | Foreign Key | Reference to `Dim_Location` for the pickup zone. |
| `DOLocation_Key` | Foreign Key | Reference to `Dim_Location` for the drop-off zone. |
| **Metrics** | | |
| `Trip_Distance` | Float | The elapsed trip distance in miles. |
| `Fare_Amount` | Float | The time-and-distance fare calculated by the meter. |
| `Total_Revenue` | Float | Total amount charged to passengers. |
| `Passenger_Count` | Integer | Number of passengers in the vehicle. |
| `Duration_Minutes` | Float | Calculated trip duration (Dropoff - Pickup). |
| `Trip_Count` | Integer | Constant value (1) used for aggregating total demand. |

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
