from __future__ import annotations
import threading
import pandas as pd
from pathlib import Path
from datetime import datetime

from src.streaming.event_bus import EventBus
from src.transformation.pipeline import DataPipeline
from src.forecasting.prophet_model import FinancialForecaster
from src.anomaly_detection.detector import AnomalyDetector
from src.utils.helpers import generate_executive_summary
import src.streaming.config as cfg


class FinancialDataConsumer:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self._records: list[dict] = []
        self._lock = threading.Lock()
        self._monthly_cache: pd.DataFrame | None = None
        self._record_count = 0

    def start(self):
        self.event_bus.subscribe(cfg.KAFKA_TOPIC_RAW, self._on_record)
        print(f"Consumer subscribed to '{cfg.KAFKA_TOPIC_RAW}'")

    def _on_record(self, key: str, value: dict):
        with self._lock:
            self._records.append(value)
            self._record_count += 1

        # Publish aggregated monthly alert when month changes
        self._publish_alert_if_needed(value)

    def _publish_alert_if_needed(self, record: dict):
        pass

    def process_batch(self) -> dict:
        with self._lock:
            if not self._records:
                return {"status": "no_data"}
            df = pd.DataFrame(self._records)
            self._records = []

        try:
            pipeline = DataPipeline.__new__(DataPipeline)
            pipeline.df = df

            month_map = {
                "Ene": "Jan", "Feb": "Feb", "Mar": "Mar",
                "Abr": "Apr", "May": "May", "Jun": "Jun",
                "Jul": "Jul", "Ago": "Aug", "Sep": "Sep",
                "Oct": "Oct", "Nov": "Nov", "Dic": "Dec",
            }
            parts = pipeline.df["Mes"].str.split(" ", expand=True)
            eng_months = parts[0].map(month_map)
            pipeline.df["ds"] = pd.to_datetime(
                eng_months + " " + parts[1], format="%b %Y"
            )

            num_cols = ["Ingresos", "HorasFacturadas", "CosteEquipo",
                        "MargenBruto"]
            for c in num_cols:
                pipeline.df[c] = pd.to_numeric(pipeline.df[c], errors="coerce")
            pipeline.df = pipeline.df.dropna(subset=num_cols)

            monthly = (
                pipeline.df.groupby("ds")
                .agg({"Ingresos": "sum", "CosteEquipo": "sum",
                       "MargenBruto": "sum", "HorasFacturadas": "sum"})
                .reset_index()
                .sort_values("ds")
            )
            monthly.columns = [
                "ds", "Ingresos", "CosteEquipo",
                "MargenBruto", "HorasFacturadas"
            ]

            forecaster = FinancialForecaster(monthly, target="Ingresos")
            forecaster.train()
            forecaster.forecast_future(periods=90)
            insights = forecaster.get_insights()

            detector = AnomalyDetector(pipeline.df)
            anomaly_results = detector.detect_all(monthly_df=monthly)
            anom_insights = detector.anomaly_insights()

            summary = generate_executive_summary(
                forecaster.metrics,
                insights,
                anom_insights or [],
            )

            report = {
                "status": "success",
                "records": len(pipeline.df),
                "metrics": forecaster.metrics,
                "insights": insights,
                "anomalies": len(detector.anomalies)
                if detector.anomalies is not None else 0,
            }

            report_path = (
                Path("reports")
                / f"streaming_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            )
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(summary, encoding="utf-8")

            return report

        except Exception as e:
            return {"status": "error", "error": str(e)}

    @property
    def record_count(self) -> int:
        with self._lock:
            return self._record_count
