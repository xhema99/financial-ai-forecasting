#!/usr/bin/env python3
"""Keedio Financial AI — Streamlit Executive Dashboard."""

import sys
from pathlib import Path
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))

from src.transformation.pipeline import DataPipeline
from src.forecasting.prophet_model import FinancialForecaster
from src.forecasting.mlp_model import MLPFinancialForecaster
from src.forecasting.comparison import ModelComparison
from src.anomaly_detection.detector import AnomalyDetector
from src.visualization.charts import ExecutiveCharts


st.set_page_config(
    page_title="Keedio Financial AI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data
def load_data():
    pipeline = DataPipeline("data/raw/KEEDIO_Cierre_Mensual.csv")
    df = pipeline.run()
    monthly = pipeline.get_monthly_aggregate()
    return df, monthly


@st.cache_data
def train_forecaster(monthly):
    forecaster = FinancialForecaster(monthly, target="Ingresos")
    forecaster.train()
    forecaster.forecast_future(periods=90)
    return forecaster


@st.cache_data
def train_mlp(monthly):
    mlp = MLPFinancialForecaster(monthly, target="Ingresos", lookback=3)
    mlp.train()
    mlp.forecast_future(periods=90)
    return mlp


@st.cache_data
def detect_anomalies(df, monthly):
    detector = AnomalyDetector(df)
    detector.detect_all(monthly_df=monthly)
    return detector


@st.cache_data
def generate_charts(df, monthly):
    charts = ExecutiveCharts(df, monthly)
    return charts.generate_all()


df, monthly = load_data()
forecaster = train_forecaster(monthly)
detector = detect_anomalies(df, monthly)
chart_paths = generate_charts(df, monthly)


PAGES = [
    "Executive KPI Dashboard",
    "Forecasting",
    "Model Comparison",
    "Anomaly Detection",
    "Data Explorer",
]

st.sidebar.markdown("## 🚀 Keedio Financial AI")
st.sidebar.markdown("---")
page = st.sidebar.radio("Navigate", PAGES, label_visibility="collapsed")
st.sidebar.markdown("---")
st.sidebar.markdown(
    f"**Data:** {len(df)} records, {len(monthly)} months"
)

if page == "Executive KPI Dashboard":
    st.title("📊 Executive KPI Dashboard")
    st.markdown("### Panorama Ejecutivo")

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    latest = monthly.iloc[-1]
    prev = monthly.iloc[-2]

    with col1:
        delta = f"{((latest['Ingresos'] - prev['Ingresos']) / prev['Ingresos'] * 100):+.1f}%"
        st.metric("Revenue (latest)", f"€{latest['Ingresos']:,.0f}", delta)
    with col2:
        st.metric("Gross Margin", f"€{latest['MargenBruto']:,.0f}",
                  f"{latest['margen_pct']:.1f}% margin")
    with col3:
        cost_pct = latest['CosteEquipo'] / latest['Ingresos'] * 100
        st.metric("Total Costs", f"€{latest['CosteEquipo']:,.0f}",
                  f"{cost_pct:.1f}% of revenue")
    with col4:
        sat = df['Satisfaccion'].mean()
        st.metric("Avg Satisfaction", f"{sat:.1f}/100",
                  f"Min: {df['Satisfaccion'].min()}, Max: {df['Satisfaccion'].max()}")
    with col5:
        hours = int(monthly['HorasFacturadas'].sum())
        avg_hours = int(monthly['HorasFacturadas'].mean())
        st.metric("Total Billed Hours", f"{hours:,}",
                  f"{avg_hours:,} avg/month")
    with col6:
        active = df[df['Estado'] == 'Activo']['Proyecto'].nunique()
        total = df['Proyecto'].nunique()
        st.metric("Active Projects", active, f"Total: {total}")

    st.markdown("---")

    img_col1, img_col2 = st.columns(2)
    with img_col1:
        kpi_path = chart_paths.get("kpi", "")
        if kpi_path:
            st.image(kpi_path, use_container_width=True)

    with img_col2:
        rev_path = chart_paths.get("revenue_by_service", "")
        if rev_path:
            st.image(rev_path, use_container_width=True)

    img_col3, img_col4 = st.columns(2)
    with img_col3:
        margin_path = chart_paths.get("margin", "")
        if margin_path:
            st.image(margin_path, use_container_width=True)
    with img_col4:
        sat_path = chart_paths.get("satisfaction", "")
        if sat_path:
            st.image(sat_path, use_container_width=True)

elif page == "Forecasting":
    st.title("🔮 Prophet Forecasting")
    st.markdown("### Forecast de Ingresos a 30/60/90 días")

    col1, col2 = st.columns([1, 3])
    with col1:
        periods = st.slider("Forecast horizon (days)", 30, 180, 90, 30)
        show_uncertainty = st.checkbox("Show uncertainty", True)
        target = st.selectbox("Target metric",
                              ["Ingresos", "MargenBruto", "CosteEquipo"])

    if target != forecaster.target:
        forecaster_custom = FinancialForecaster(monthly, target=target)
        forecaster_custom.train()
        forecaster_custom.forecast_future(periods=periods)
        f = forecaster_custom
    else:
        forecaster.forecast_future(periods=periods)
        f = forecaster

    train_df = f.prepare()
    future = f.forecast[f.forecast["ds"] > monthly["ds"].max()]

    with col2:
        fig, ax = __import__("matplotlib.pyplot").subplots(figsize=(14, 5))
        ax.plot(train_df["ds"], train_df["y"], marker="o",
                linewidth=2, color="#2563EB", label=f"Historical {target}")
        ax.plot(future["ds"], future["yhat"], linestyle="--",
                linewidth=2, color="#EF4444", label=f"Forecast {target}")
        if show_uncertainty:
            ax.fill_between(future["ds"], future["yhat_lower"],
                            future["yhat_upper"],
                            alpha=0.2, color="#EF4444", label="Uncertainty")
        ax.axvline(x=monthly["ds"].max(), color="gray", linestyle=":",
                   alpha=0.7, label="Forecast Start")
        ax.set_title(f"{target} — Prophet Forecast ({periods} days)")
        ax.set_ylabel("EUR (€)")
        ax.legend()
        ax.grid(True, alpha=0.3)
        fig.autofmt_xdate()
        st.pyplot(fig)

    st.markdown("### Model Metrics")
    m = f.metrics
    mc1, mc2, mc3 = st.columns(3)
    mc1.metric("MAE", f"€{m['MAE']:,.2f}")
    mc2.metric("RMSE", f"€{m['RMSE']:,.2f}")
    mc3.metric("MAPE", f"{m['MAPE']:.2f}%")

    st.markdown("### Insights")
    for ins in f.get_insights():
        st.info(ins)

    st.markdown("### Scenario Analysis")
    scenarios = [
        {"name": "Base", "adjustments": {}},
        {"name": "Growth +10%", "adjustments": {"growth": 10}},
        {"name": "Decline -15%", "adjustments": {"decline": 15}},
        {"name": "Costs +8%", "adjustments": {"costs": 8}},
    ]
    sc_df = f.scenario_analysis(scenarios)
    st.dataframe(sc_df, use_container_width=True)

elif page == "Model Comparison":
    st.title("⚖️ Model Comparison: Prophet vs MLP")
    st.markdown("### Prophet (Facebook) vs MLP Neural Network (scikit-learn)")

    with st.spinner("Training MLP model..."):
        mlp = train_mlp(monthly)
        comparison = ModelComparison(forecaster, mlp)

    st.markdown("#### Metrics Comparison")
    metrics_df = comparison.compare_metrics()
    st.dataframe(metrics_df, use_container_width=True)

    st.markdown("#### Forecast Comparison")
    forecast_compare = comparison.compare_forecasts()
    if not forecast_compare.empty:
        st.dataframe(forecast_compare.style
                     .format("{:,.2f}", subset=["yhat_prophet", "yhat_mlp", "difference"])
                     .format("{:.2f}%", subset=["diff_pct"]),
                     use_container_width=True)

    comp_img = "images/model_comparison.png"
    if Path(comp_img).exists():
        st.image(comp_img, use_container_width=True)

    mlp_img = "images/mlp_forecast_ingresos.png"
    if Path(mlp_img).exists():
        st.image(mlp_img, use_container_width=True)

    st.markdown("#### MLP Model Details")
    m = mlp.metrics
    mc1, mc2, mc3 = st.columns(3)
    mc1.metric("Train MAE", f"€{m['MAE']:,.2f}" if m.get('MAE') else "N/A")
    mc2.metric("Train RMSE", f"€{m['RMSE']:,.2f}" if m.get('RMSE') else "N/A")
    mc3.metric("Train MAPE", f"{m['MAPE']:.2f}%" if m.get('MAPE') else "N/A")

    if m.get("MAE_test"):
        tc1, tc2, tc3 = st.columns(3)
        tc1.metric("Test MAE", f"€{m['MAE_test']:,.2f}")
        tc2.metric("Test RMSE", f"€{m['RMSE_test']:,.2f}")
        tc3.metric("Test MAPE", f"{m['MAPE_test']:.2f}%")

elif page == "Anomaly Detection":
    st.title("🔍 Anomaly Detection")
    st.markdown("### Isolation Forest · Z-Score · Prophet Residuals")

    anomalies = detector.anomalies
    if anomalies is not None:
        st.metric("Anomalies Detected", len(anomalies))
        st.dataframe(
            anomalies[["ds", "Proyecto", "Ingresos", "Servicio",
                       "anomaly_score", "anomaly_type"]]
            if "anomaly_type" in anomalies.columns
            else anomalies,
            use_container_width=True,
        )
    else:
        st.info("No anomalies detected.")

    anom_img = "images/anomalies_detected.png"
    if Path(anom_img).exists():
        st.image(anom_img, use_container_width=True)

    st.markdown("### Anomaly Insights")
    insights = detector.anomaly_insights()
    if insights:
        for ins in insights:
            st.warning(ins)
    else:
        st.info("No anomaly insights available.")

elif page == "Data Explorer":
    st.title("🗃️ Data Explorer")

    tab1, tab2 = st.tabs(["Raw Records", "Monthly Aggregates"])

    with tab1:
        st.markdown(f"**{len(df)} individual records**")
        cols = st.multiselect(
            "Columns", df.columns.tolist(),
            default=["Mes", "Proyecto", "Cliente", "Servicio",
                     "Ingresos", "MargenBruto", "Seniority", "Satisfaccion"]
        )
        if cols:
            st.dataframe(df[cols], use_container_width=True)

        st.download_button(
            "Download as CSV",
            df.to_csv(index=False).encode("utf-8-sig"),
            "keedio_data.csv",
            "text/csv",
        )

    with tab2:
        st.markdown(f"**{len(monthly)} monthly aggregates**")
        st.dataframe(monthly, use_container_width=True)
        st.line_chart(monthly.set_index("ds")[["Ingresos", "CosteEquipo", "MargenBruto"]])

    st.markdown("### Summary Statistics")
    st.dataframe(df.describe(), use_container_width=True)

    st.markdown("### Categorical Distributions")
    cat_col = st.selectbox("Categorical column",
                           ["Servicio", "Cliente", "Proyecto", "Seniority", "Estado"])
    dist = df[cat_col].value_counts()
    st.bar_chart(dist)
