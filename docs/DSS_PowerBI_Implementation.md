# Comprehensive Engineering Blueprint: NYC Taxi DSS in Power BI

This document provides a click-by-click technical guide to implementing a professional-grade Decision Support System.

---

## Phase 1: Data Infrastructure & Modeling (Deep Dive)

### 1.1. Ingestion Strategy
1.  **Home** > **Get Data** > **Google BigQuery**.
2.  **Navigator Window**: Select `Dim_Time`, `Dim_Location`, `Dim_Service_Type`, `Dim_Weather`, and `Fact_Trips`.
3.  **Storage Mode Selection**:
    - **Import**: `Dim_Time`, `Dim_Location`, `Dim_Service_Type`, `Dim_Weather`. 
        *Reason: These are small lookup tables. Importing them allows for faster filtering and advanced DAX time intelligence.*
    - **DirectQuery**: `Fact_Trips`.
        *Reason: This table contains millions of rows. DirectQuery pushes the heavy "SUM" and "COUNT" operations to BigQuery’s cloud CPUs, keeping the Power BI file lightweight.*

### 1.2. Crucial Table Configurations (Power Query)
*Before clicking Load, click **Transform Data**:*
1.  **Dim_Time**: 
    - Ensure `Full_Date` is a **Date** type.
    - Ensure `Time_Key` is a **Whole Number**.
2.  **Fact_Trips**:
    - Ensure `pickup_time_key` is a **Whole Number**.
3.  **Dim_Location**:
    - Select `Borough` column > **Data Category** (in ribbon) > **State or Province**.
    - Select `Zone` column > **Data Category** > **City**.

### 1.3. Relationship Integrity (Model View)
1.  **Mark as Date Table**: Right-click `Dim_Time` > **Mark as date table** > Select `Full_Date`. 
    *This is the "Golden Rule" for time-series analysis in Power BI.*
2.  **The Star Schema Joins**:
    - `Dim_Time[Time_Key]` (1) to `Fact_Trips[pickup_time_key]` (*) | Single Direction.
    - `Dim_Location[Location_ID]` (1) to `Fact_Trips[pulocation_id]` (*) | Single Direction.
    - `Dim_Service_Type[Service_Type_Key]` (1) to `Fact_Trips[service_type_key]` (*) | Single Direction.
3.  **Fixing the Sort Order**:
    - Select `Dim_Time` table. Select `Month_Name` column.
    - Ribbon > **Sort by Column** > Select `Month_Number`.
    - Select `Day_of_Week_Name` column.
    - Ribbon > **Sort by Column** > Select `Day_of_Week_Number`.
    *Result: Your charts will show "January, February..." instead of "April, August..."*

---

## Phase 2: The DAX Analytical Engine

### 2.1. Basic Metrics (Standard Measures)
```dax
Total Trips = COUNTROWS('Fact_Trips')

Total Revenue = SUM('Fact_Trips'[ml_unified_fare])

Avg Distance = AVERAGE('Fact_Trips'[ml_unified_distance])
```

### 2.2. Advanced Time Intelligence
*These require the "Mark as Date Table" step from Phase 1.*
```dax
Demand Growth YoY % = 
VAR CurrentTrips = [Total Trips]
VAR LastYearTrips = CALCULATE([Total Trips], SAMEPERIODLASTYEAR('Dim_Time'[Full_Date]))
RETURN DIVIDE(CurrentTrips - LastYearTrips, LastYearTrips, 0)

Demand 7-Day Moving Avg = 
AVERAGEX(
    DATESINPERIOD('Dim_Time'[Full_Date], LASTDATE('Dim_Time'[Full_Date]), -7, DAY),
    [Total Trips]
)
```

---

## Phase 3: Visual Engineering (The Z-Pattern Layout)

### 3.1. Top Section (KPIs & Slicers)
- **Visuals**: 3 Cards + 2 Slicers.
- **KPI Formatting**: Visualizations pane > Format visual > Callout value > Font: **Segoe UI Bold**, Size: **25**.
- **Slicers**: Use **Dropdown** style for `Borough` and `Service_Name`.

### 3.2. Left Section (Macro Analysis)
- **Map Visual**: 
    - Bubble size: `Total Trips`.
    - Colors: Format > Bubbles > Colors > Conditional Formatting (fx) > Based on `Total Revenue`.
- **Monthly Column Chart**: 
    - X-Axis: `Month_Name`. 
    - Y-Axis: `Total Trips`.

### 3.3. Right Section (Micro Analysis - The Heatmap Matrix)
1.  **Rows**: `Dim_Time[Day_of_Week_Name]`.
2.  **Columns**: `Dim_Time[Hour]`.
3.  **Values**: `Total Trips`.
4.  **Heatmap Steps**: 
    - Format visual > **Cell elements**.
    - Toggle **Background color** ON.
    - Click **fx** > Format style: **Gradient**.
    - Minimum: #F0F0F0 (Light Gray).
    - Maximum: #D64550 (Red).

---

## Phase 4: Pro-Level UX Enhancements

### 4.1. Visual-in-Visual Tooltips
1.  **The Tooltip Page**: 
    - New Page > Page Information > **Allow use as tooltip** = ON.
    - Canvas Settings > Type = **Tooltip**.
    - Create a small **Line Chart**: X: `Hour`, Y: `Total Trips`.
2.  **The Connection**: 
    - Select the **Map** on the main page > Format > General > Tooltips > Page: Select your Tooltip page.

### 4.2. Dynamic Titles
```dax
Auto_Header = "Analysis for " & SELECTEDVALUE('Dim_Service_Type'[Service_Name], "All Taxis")
```
- Go to Chart Title > Click **fx** > Field value: `Auto_Header`.

### 4.3. Navigation Bookmarks
1.  **Selection Pane**: View > **Selection**.
2.  **Setup**: Filter the page to "Yellow Taxi".
3.  **Add Bookmark**: View > **Bookmarks** > Add "Yellow_View".
4.  **Repeat**: Filter to "Uber/Lyft" > Add "App_View".
5.  **Buttons**: Insert > Buttons > Blank. Action: **Bookmark** > Link to "Yellow_View".

---

## Phase 5: AI Forecasting Validation

1.  **Actual vs Predicted Chart**: 
    - Create a Line Chart. 
    - Values: `Total Trips` (Actual) and `Predicted_Demand` (from ML table).
2.  **Variance Analysis**:
```dax
Forecast Accuracy % = 
1 - DIVIDE(
    SUMX('Fact_Trips', ABS([Total Trips] - [Predicted_Demand])),
    [Total Trips]
)
```

---

## Final Checklist for Deployment
1.  [ ] Are Relationships (1:*) single-direction?
2.  [ ] Is `Dim_Time` sorted by `Month_Number`?
3.  [ ] Is `Fact_Trips` in DirectQuery mode?
4.  [ ] Have you published to Power BI Service?
