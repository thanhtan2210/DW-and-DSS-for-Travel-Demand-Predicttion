# Theoretical Background on Data Preprocessing & Statistics

**Domain-Specific Data Cleaning Techniques**
Raw urban mobility data is inherently noisy due to sensor errors, GPS signal loss, or human input anomalies. To ensure the integrity of the predictive model, the following preprocessing techniques are applied:
* **Rule-Based Outlier Removal:** Taxi data often contains physical impossibilities. Techniques involve defining strict threshold boundaries, such as removing trips with zero distance but non-zero fares, negative trip durations, or extreme passenger counts exceeding standard vehicle capacities.
* **Temporal and Spatial Filtering:** Meter malfunctions can introduce out-of-bound timestamps (e.g., trips recorded in the year 2088). Data is strictly truncated to the designated study period. Spatially, trips originating or terminating in 'Unknown' zones are filtered out using an inner join with the spatial lookup table.
* **Handling Missing Data:** Given the massive volume of the TLC dataset, imputation techniques (like mean/median substitution) for missing critical features (e.g., pickup location or time) introduce unnecessary bias. Therefore, Listwise Deletion (dropping rows with missing primary keys) is the preferred statistical approach.

**Time-Based Splitting vs. Stratified Sampling**
In traditional machine learning classification tasks, Stratified Sampling is utilized to ensure train and test sets have similar target distributions. However, for Travel Demand Prediction, treating observations as independent and identically distributed (i.i.d.) violates the fundamental nature of time-series data. 

Using Stratified or Random splitting would result in **Data Leakage**—where the model inadvertently learns from future events to predict past occurrences. Instead, this system mandates a **Time-Based Splitting (Chronological Split)** approach. 

In this method, the temporal order of observations is strictly preserved. The dataset is split using a chronological cut-off point. For instance, in a 6-month dataset spanning from June to November, the initial chronological window (e.g., June to October) is isolated strictly for the **Training Set**, while the final chronological window (e.g., November) is reserved for the **Testing Set**. This accurately simulates the real-world operational environment where only historical data is available to forecast unknown future demand.
