#!/usr/bin/env python3
"""Keedio Financial AI — End-to-End Forecasting Pipeline."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.transformation.pipeline import DataPipeline
from src.exploration.eda import EDA
from src.forecasting.prophet_model import FinancialForecaster
from src.anomaly_detection.detector import AnomalyDetector
from src.visualization.charts import ExecutiveCharts
from src.utils.helpers import (
    generate_executive_summary,
    export_for_powerbi,
)


def main(raw_path: str = "data/raw/KEEDIO_Cierre_Mensual.csv"):
    print("=" * 60)
    print("  KEEDIO Financial AI Forecasting Pipeline")
    print("=" * 60)

    # 1. LOAD & TRANSFORM
    print("\n[1/7] Loading and transforming data...")
    pipeline = DataPipeline(raw_path)
    df = pipeline.run()
    monthly = pipeline.get_monthly_aggregate()
    print(f"  → {len(df)} records loaded, {len(monthly)} months aggregated")

    # 2. EDA
    print("\n[2/7] Running exploratory analysis...")
    eda = EDA(df)
    summary = eda.summary()
    report_path = eda.report()
    eda.plot_distributions()
    eda.plot_monthly_trends()
    eda.plot_correlation_heatmap()
    print(f"  → EDA report saved: {report_path}")

    # 3. FORECASTING
    print("\n[3/7] Training Prophet forecasting model...")
    forecaster = FinancialForecaster(monthly, target="Ingresos")
    forecaster.train()
    forecaster.forecast_future(periods=90)
    forecast_img = forecaster.plot_forecast()
    components_img = forecaster.plot_components()
    insights = forecaster.get_insights()
    print(f"  → Model metrics: {forecaster.metrics}")
    for ins in insights:
        print(f"  → Insight: {ins}")

    # 4. ANOMALY DETECTION
    print("\n[4/7] Detecting anomalies...")
    detector = AnomalyDetector(df)
    anomaly_results = detector.detect_all(monthly_df=monthly)
    detector.plot_anomalies()
    anom_insights = detector.anomaly_insights()
    print(f"  → Anomalies detected: {len(detector.anomalies) if detector.anomalies is not None else 0}")

    # 5. EXECUTIVE CHARTS
    print("\n[5/7] Generating executive visualizations...")
    charts = ExecutiveCharts(df, monthly)
    chart_paths = charts.generate_all()
    print(f"  → {len(chart_paths)} charts generated")

    # 6. EXPORT
    print("\n[6/7] Exporting data...")
    pbi_path = export_for_powerbi(df)
    print(f"  → Power BI data: {pbi_path}")

    # 7. EXECUTIVE SUMMARY
    print("\n[7/7] Generating executive summary...")
    summary_text = generate_executive_summary(
        forecaster.metrics, insights, anom_insights
    )
    summary_path = "reports/executive_summary.md"
    Path(summary_path).write_text(summary_text, encoding="utf-8")
    print(f"  → Summary: {summary_path}")

    print("\n" + "=" * 60)
    print("  Pipeline completed successfully!")
    print("=" * 60)

    return {
        "df": df,
        "monthly": monthly,
        "forecaster": forecaster,
        "detector": detector,
        "chart_paths": chart_paths,
    }


if __name__ == "__main__":
    main()
