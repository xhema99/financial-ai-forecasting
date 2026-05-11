import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path


class ModelComparison:
    def __init__(self, prophet_model, mlp_model):
        self.prophet = prophet_model
        self.mlp = mlp_model
        self.results = {}

    def compare_metrics(self) -> pd.DataFrame:
        rows = []
        for name, model in [("Prophet", self.prophet), ("MLP", self.mlp)]:
            m = model.metrics
            rows.append({
                "Model": name,
                "MAE": m.get("MAE"),
                "RMSE": m.get("RMSE"),
                "MAPE (%)": m.get("MAPE"),
            })
        return pd.DataFrame(rows).set_index("Model")

    def compare_forecasts(self) -> pd.DataFrame:
        p_forecast = self.prophet.forecast
        m_forecast = self.mlp.forecast
        if p_forecast is None or m_forecast is None:
            return pd.DataFrame()

        p_future = p_forecast[p_forecast["ds"] > self.prophet.df["ds"].max()][["ds", "yhat"]].copy()
        m_future = m_forecast[m_forecast["ds"] > self.prophet.df["ds"].max()][["ds", "yhat"]].copy()

        combined = pd.merge(p_future, m_future, on="ds", how="outer",
                            suffixes=("_prophet", "_mlp"))
        combined = combined.sort_values("ds").reset_index(drop=True)
        combined["difference"] = combined["yhat_prophet"] - combined["yhat_mlp"]
        combined["diff_pct"] = (
            combined["difference"] / combined["yhat_prophet"] * 100
        ).round(2)
        return combined

    def plot_comparison(self, output_dir: str = "images"):
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        fig, ax = plt.subplots(figsize=(16, 7))

        ax.plot(self.prophet.df["ds"], self.prophet.df[self.prophet.target],
                marker="o", linewidth=2, color="#2563EB", label="Historical")

        p_forecast = self.prophet.forecast
        p_future = p_forecast[p_forecast["ds"] > self.prophet.df["ds"].max()]
        ax.plot(p_future["ds"], p_future["yhat"], linestyle="--",
                linewidth=2, color="#EF4444", label="Prophet Forecast")
        ax.fill_between(p_future["ds"], p_future["yhat_lower"],
                        p_future["yhat_upper"],
                        alpha=0.15, color="#EF4444")

        m_forecast = self.mlp.forecast
        ax.plot(m_forecast["ds"], m_forecast["yhat"], linestyle="--",
                linewidth=2, color="#8B5CF6", label="MLP Forecast")
        ax.fill_between(m_forecast["ds"], m_forecast["yhat_lower"],
                        m_forecast["yhat_upper"],
                        alpha=0.15, color="#8B5CF6")

        ax.axvline(x=self.prophet.df["ds"].iloc[-1], color="gray",
                   linestyle=":", alpha=0.7, label="Forecast Start")

        ax.set_title("Model Comparison: Prophet vs MLP Neural Network",
                     fontsize=14, fontweight="bold")
        ax.set_xlabel("Date")
        ax.set_ylabel(f"{self.prophet.target} (EUR €)")
        ax.legend()
        ax.grid(True, alpha=0.3)
        fig.autofmt_xdate()

        path = out / "model_comparison.png"
        plt.savefig(path, dpi=150, bbox_inches="tight")
        plt.close()
        return str(path)

    def report(self, output_dir: str = "reports"):
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        metrics_df = self.compare_metrics()
        forecast_compare = self.compare_forecasts()

        lines = [
            "# Model Comparison Report: Prophet vs MLP\n",
            f"**Generated:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}\n",
            f"**Target:** {self.prophet.target}\n",
            "## Metrics Comparison\n",
            metrics_df.to_string(),
            "\n",
        ]

        if not forecast_compare.empty:
            lines.append("## Forecast Comparison (Future Periods)\n")
            lines.append(forecast_compare.to_string())
            lines.append("\n")

            avg_diff = forecast_compare["diff_pct"].mean()
            lines.append(f"\n**Average difference:** {avg_diff:+.2f}%\n")
            if abs(avg_diff) < 10:
                lines.append(
                    "Both models show similar forecast trajectories.\n"
                )
            else:
                winner = "Prophet" if avg_diff > 0 else "MLP"
                lines.append(
                    f"{winner} forecasts consistently higher.\n"
                )

        lines.append("\n## Verdict\n")
        p_mape = self.prophet.metrics.get("MAPE", 0)
        m_mape = self.mlp.metrics.get("MAPE", 0)
        if p_mape < m_mape:
            lines.append(
                f"**Prophet** performs better on training data "
                f"(MAPE: {p_mape}% vs {m_mape}%).\n"
            )
        elif m_mape < p_mape:
            lines.append(
                f"**MLP** performs better on training data "
                f"(MAPE: {m_mape}% vs {p_mape}%).\n"
            )
        else:
            lines.append("Both models perform similarly.\n")

        lines.append(
            "\n---\n*Generated by Keedio Financial AI Forecasting System*"
        )

        text = "\n".join(lines)
        path = out / "model_comparison_report.md"
        Path(path).write_text(text, encoding="utf-8")
        return str(path)
