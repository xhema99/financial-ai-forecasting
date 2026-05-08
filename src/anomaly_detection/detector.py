import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.ensemble import IsolationForest
from pathlib import Path


class AnomalyDetector:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.iso_forest: IsolationForest | None = None
        self.anomalies: pd.DataFrame | None = None

    def zscore_anomalies(self, col: str = "Ingresos",
                         threshold: float = 2.0) -> pd.DataFrame:
        z = np.abs(
            (self.df[col] - self.df[col].mean()) / self.df[col].std()
        )
        result = self.df[z > threshold].copy()
        result["anomaly_type"] = f"zscore_{col}"
        result["anomaly_score"] = z[z > threshold]
        return result

    def isolation_forest_anomalies(self,
                                   features: list[str] | None = None,
                                   contamination: float = 0.05) -> pd.DataFrame:
        if features is None:
            features = ["Ingresos", "HorasFacturadas", "CosteEquipo", "MargenBruto"]
        X = self.df[features].values
        self.iso_forest = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=200,
        )
        preds = self.iso_forest.fit_predict(X)
        scores = self.iso_forest.score_samples(X)
        result = self.df.copy()
        result["anomaly_if"] = preds
        result["anomaly_score_if"] = scores
        anom = result[result["anomaly_if"] == -1].copy()
        anom["anomaly_type"] = "isolation_forest"
        return anom

    def prophet_residuals(self, monthly_df: pd.DataFrame,
                          target: str = "Ingresos") -> pd.DataFrame:
        from prophet import Prophet
        pdf = monthly_df[["ds", target]].rename(columns={target: "y"}).copy()
        m = Prophet(yearly_seasonality=True)
        m.fit(pdf)
        forecast = m.predict(pdf[["ds"]])
        pdf["residual"] = pdf["y"] - forecast["yhat"]
        pdf["residual_pct"] = pdf["residual"] / pdf["y"] * 100
        threshold = pdf["residual"].std() * 2
        anom = pdf[np.abs(pdf["residual"]) > threshold].copy()
        anom["anomaly_type"] = "prophet_residual"
        return anom

    def detect_all(self, monthly_df: pd.DataFrame | None = None,
                   output_dir: str = "reports") -> dict:
        results = {}

        zscore_ing = self.zscore_anomalies("Ingresos")
        zscore_cost = self.zscore_anomalies("CosteEquipo")
        zscore_margin = self.zscore_anomalies("MargenBruto")
        zscore_hours = self.zscore_anomalies("HorasFacturadas")

        results["zscore"] = pd.concat(
            [zscore_ing, zscore_cost, zscore_margin, zscore_hours],
            ignore_index=True
        )

        results["isolation_forest"] = self.isolation_forest_anomalies()

        if monthly_df is not None:
            results["prophet_residuals"] = self.prophet_residuals(monthly_df)

        self.anomalies = pd.concat(
            [v for v in results.values() if isinstance(v, pd.DataFrame) and not v.empty],
            ignore_index=True
        ) if results else pd.DataFrame()

        return results

    def plot_anomalies(self, output_dir: str = "images"):
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        fig, axes = plt.subplots(2, 2, figsize=(16, 10))
        targets = ["Ingresos", "CosteEquipo", "MargenBruto", "HorasFacturadas"]

        for ax, col in zip(axes.flatten(), targets):
            ax.scatter(self.df["ds"], self.df[col], alpha=0.6,
                       color="#2563EB", label="Normal")

            if self.anomalies is not None and not self.anomalies.empty:
                anom_in_col = self.anomalies[
                    self.anomalies.apply(
                        lambda r: r.get(col, np.nan) == r.get(col, np.nan),
                        axis=1
                    )
                ]
                common = self.df[
                    self.df["ds"].isin(self.anomalies["ds"])
                ]
                anom_plot = common[
                    common["ds"].isin(self.anomalies["ds"])
                ]
                ax.scatter(anom_plot["ds"], anom_plot[col],
                           color="#EF4444", s=100, marker="x",
                           label="Anomaly")

            ax.set_title(f"Anomalies — {col}", fontsize=12, fontweight="bold")
            ax.legend()
            ax.grid(True, alpha=0.3)

        fig.autofmt_xdate()
        plt.tight_layout()
        path = out / "anomalies_detected.png"
        plt.savefig(path, dpi=150, bbox_inches="tight")
        plt.close()
        return str(path)

    def anomaly_insights(self) -> list:
        if self.anomalies is None or self.anomalies.empty:
            return ["No anomalies detected."]

        insights = []
        anom_count = len(self.anomalies)

        if "Ingresos" in self.anomalies.columns:
            avg_anom = self.anomalies["Ingresos"].mean()
            avg_normal = self.df[
                ~self.df.index.isin(self.anomalies.index)
            ]["Ingresos"].mean() if not self.anomalies.empty else self.df["Ingresos"].mean()
            insights.append(
                f"Anomalous revenue events avg €{avg_anom:,.0f} "
                f"(normal avg: €{avg_normal:,.0f}) — {anom_count} anomalies detected"
            )

        monthly_anom = self.df[
            self.df["ds"].isin(self.anomalies["ds"])
        ] if "ds" in self.anomalies.columns else pd.DataFrame()

        return insights
