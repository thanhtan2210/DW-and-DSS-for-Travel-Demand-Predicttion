# Theoretical Background on Forecasting Models

To accurately predict travel demand across New York City's taxi zones, this project employs a multi-model approach ranging from ensemble machine learning to deep learning architectures. This allows for a comprehensive evaluation of different modeling strengths in capturing the complex spatio-temporal dynamics of urban mobility.

## 1. Forecasting Algorithms

### A. Random Forest Regressor (Ensemble Learning)
*   **Concept:** An ensemble learning method that constructs a multitude of decision trees during training and outputs the mean prediction of the individual trees.
*   **Rationale:** 
    *   **Robustness:** Effectively handles outliers and noisy data inherent in taxi trip records.
    *   **Non-linearity:** Captures non-linear relationships between features (e.g., time of day, location) and demand without requiring complex feature scaling.
    *   **Interpretability:** Provides feature importance scores to identify the primary drivers of taxi demand.

### B. XGBoost Regressor (Gradient Boosting)
*   **Concept:** A highly efficient implementation of gradient boosted decision trees designed for speed and performance. It builds trees sequentially, where each new tree minimizes the errors of previous ones.
*   **Rationale:**
    *   **Regularization:** Includes built-in L1 and L2 regularization to prevent overfitting on complex urban datasets.
    *   **Performance:** Generally offers superior accuracy for structured/tabular data compared to standard random forests.
    *   **Optimization:** Optimized for large-scale datasets, making it suitable for processing millions of TLC trip records.

### C. Long Short-Term Memory - LSTM (Deep Learning)
*   **Concept:** A specialized type of Recurrent Neural Network (RNN) capable of learning long-term dependencies. LSTMs are designed to avoid the vanishing gradient problem in standard RNNs.
*   **Rationale:**
    *   **Sequential Dependencies:** Ideal for time-series forecasting where past demand significantly influences future patterns.
    *   **Memory Gates:** The forget, input, and output gates allow the model to retain historical patterns across long periods, such as daily and weekly seasonality in traffic.

## 2. Evaluation Metrics

To rigorously assess model performance and ensure the reliability of the Decision Support System (DSS), the following regression metrics are utilized:

| Metric | Formula / Intuition | Application in Demand Prediction |
| :--- | :--- | :--- |
| **Mean Absolute Error (MAE)** | Average of absolute errors | Measures the average magnitude of errors in the same units as the target (number of trips). |
| **Root Mean Squared Error (RMSE)** | Square root of average squared errors | Penalizes larger errors more heavily, highlighting instances where the model makes significant prediction mistakes. |
| **R-squared ($R^2$)** | Coefficient of determination | Indicates the proportion of variance in travel demand explained by the model's features. |

## 3. Implementation Strategy
The forecasting workflow involves establishing a performance baseline using Random Forest, followed by iterative optimization using XGBoost for higher precision. Finally, LSTM is implemented to leverage the sequential nature of the data, with all models being cross-validated using the time-based splitting strategy defined in the preprocessing stage.
