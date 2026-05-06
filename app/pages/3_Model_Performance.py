import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Model Performance", page_icon="📈", layout="wide")

st.title("📈 Model Performance Metrics")

# Performance data
models = ['XGBoost', 'Random Forest', 'LSTM']
metrics = pd.DataFrame({
    'Model': models,
    'RMSE': [78.7, 90.9, 85.2],
    'MAE': [47.9, 57.1, 52.0],
    'R2 Score': [0.77, 0.69, 0.73]
})

# Performance Comparison (Radar Chart)
st.subheader("Performance Comparison (Lower is better for RMSE/MAE)")
fig_radar = go.Figure()
for model in models:
    row = metrics[metrics['Model'] == model]
    fig_radar.add_trace(go.Scatterpolar(
        r=[row['RMSE'].values[0], row['MAE'].values[0], row['R2 Score'].values[0]*100],
        theta=['RMSE', 'MAE', 'R2*100'],
        fill='toself',
        name=model
    ))
fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True)), showlegend=True, template="plotly_dark")
st.plotly_chart(fig_radar, use_container_width=True)

st.subheader("Metrics Table")
st.dataframe(metrics, use_container_width=True)

# Tree-based Importance
st.subheader("Tree-Based Feature Importance (XGBoost & RF)")
importance = pd.DataFrame({
    'Feature': ['Hour', 'Temperature', 'Lag_1h', 'DayOfWeek', 'Precipitation', 'Is_Weekend'],
    'XGBoost': [0.35, 0.20, 0.15, 0.12, 0.10, 0.08],
    'Random Forest': [0.30, 0.18, 0.16, 0.15, 0.11, 0.10]
})
importance_melted = importance.melt(id_vars='Feature', var_name='Model', value_name='Score')
st.plotly_chart(px.bar(importance_melted, x='Score', y='Feature', color='Model', barmode='group', template="plotly_dark"), use_container_width=True)

# LSTM Section
st.subheader("LSTM Model Analysis")
st.info("""
**LSTM (Long Short-Term Memory)**:
* **Architecture**: Sequence-to-sequence neural network.
* **Feature Sensitivity**: Captures temporal dependencies (lagged demand) more effectively than tree models.
* **Note**: Unlike tree-based models, LSTM does not provide native feature importance. We evaluate its contribution via time-series reconstruction error analysis.
""")
