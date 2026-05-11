import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from prophet import Prophet
from prophet.diagnostics import cross_validation, performance_metrics
from sklearn.metrics import mean_absolute_error, mean_squared_error
from pathlib import Path


class FinancialForecaster:
    def __init__(self, df: pd.DataFrame, target: str = "Ingresos"):
        self.df = df.copy()
        self.target = target
        self.model: Prophet | None = None
        self.forecast: pd.DataFrame | None = None
        self.metrics: dict = {}

    def prepare(self):
        prophet_df = self.df[["ds", self.target]].rename(
            columns={self.target: "y"}
        ).copy()
        prophet_df["y"] = pd.to_numeric(prophet_df["y"], errors="coerce")
        prophet_df = prophet_df.dropna()
        return prophet_df

    def train(self, yearly_seasonality: bool = True,
              weekly_seasonality: bool = False,
              daily_seasonality: bool = False,
              changepoint_prior_scale: float = 0.05,
              seasonality_prior_scale: float = 10.0):
        train_df = self.prepare()
        self.model = Prophet(
            yearly_seasonality=yearly_seasonality,
            weekly_seasonality=weekly_seasonality,
            daily_seasonality=daily_seasonality,
            changepoint_prior_scale=changepoint_prior_scale,
            seasonality_prior_scale=seasonality_prior_scale,
            seasonality_mode="multiplicative",
        )
        self.model.add_seasonality(name="quarterly", period=91.25, fourier_order=5)
        self.model.fit(train_df)

        train_pred = self.model.predict(train_df[["ds"]])
        y_true = train_df["y"].values
        y_pred = train_pred["yhat"].values

        self.metrics = {
            "MAE": round(mean_absolute_error(y_true, y_pred), 2),
            "RMSE": round(np.sqrt(mean_squared_error(y_true, y_pred)), 2),
            "MAPE": round(np.mean(np.abs((y_true - y_pred) / y_true)) * 100, 2),
        }
        return self.model

    def forecast_future(self, periods: int = 90):
        months = max(1, periods // 30)
        future = self.model.make_future_dataframe(periods=months, freq="MS")
        self.forecast = self.model.predict(future)
        return self.forecast

    def plot_forecast(self, output_dir: str = "images"):
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        fig, ax = plt.subplots(figsize=(16, 7))
        train_df = self.prepare()

        ax.plot(train_df["ds"], train_df["y"], marker="o", linewidth=2,
                color="#2563EB", label=f"Historical {self.target}")
        ax.plot(self.forecast["ds"], self.forecast["yhat"], linestyle="--",
                linewidth=2, color="#EF4444", label=f"Forecast {self.target}")
        ax.fill_between(self.forecast["ds"],
                        self.forecast["yhat_lower"],
                        self.forecast["yhat_upper"],
                        alpha=0.2, color="#EF4444", label="Uncertainty (80%)")

        split_idx = len(train_df)
        ax.axvline(x=train_df["ds"].iloc[-1], color="gray", linestyle=":",
                   alpha=0.7, label="Forecast Start")

        ax.set_title(f"{self.target} — Prophet Forecast (30/60/90 days)",
                     fontsize=14, fontweight="bold")
        ax.set_xlabel("Date")
        ax.set_ylabel("EUR (€)")
        ax.legend()
        ax.grid(True, alpha=0.3)
        fig.autofmt_xdate()

        path = out / f"forecast_{self.target.lower()}.png"
        plt.savefig(path, dpi=150, bbox_inches="tight")
        plt.close()
        return str(path)

    def plot_components(self, output_dir: str = "images"):
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        fig = self.model.plot_components(self.forecast)
        path = out / f"components_{self.target.lower()}.png"
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close()
        return str(path)

    def get_insights(self) -> list:
        if self.forecast is None:
            return []

        future = self.forecast[self.forecast["ds"] > self.df["ds"].max()]
        insights = []
        last_hist = self.df[self.target].sum()
        avg_future = future["yhat"].mean()
        change_pct = round((avg_future - last_hist) / last_hist * 100, 1)

        insights.append(
            f"Forecasted average {self.target}: €{avg_future:,.0f} "
            f"({change_pct:+.1f}% vs last historical period)"
        )

        min_30 = future.head(1)["yhat"].values[0]
        min_90 = future.tail(1)["yhat"].values[0]
        trajectory = "upward" if min_90 > min_30 else "downward"
        insights.append(
            f"30→90 day {self.target} trajectory: {trajectory} "
            f"(€{min_30:,.0f} → €{min_90:,.0f})"
        )

        risk = future["yhat_lower"].min()
        threshold = self.df[self.target].mean() * 0.7
        if risk < threshold:
            insights.append(
                f"RISK: {self.target} could drop to €{risk:,.0f} "
                f"(below 70% threshold of €{threshold:,.0f})"
            )

        return insights

    def cross_validate(self, initial: str = "365 days",
                       period: str = "90 days",
                       horizon: str = "60 days"):
        train_df = self.prepare()
        cv_results = cross_validation(
            self.model, initial=initial, period=period, horizon=horizon
        )
        perf = performance_metrics(cv_results)
        return perf[["horizon", "mae", "rmse", "mape"]].head(10)

    def scenario_analysis(self, scenarios: list[dict]) -> pd.DataFrame:
        results = []
        base_forecast = self.forecast_future(periods=90)
        base_total = base_forecast.tail(3)["yhat"].sum()

        for sc in scenarios:
            adjusted = base_forecast.copy()
            for _, row in adjusted.iterrows():
                for factor, pct in sc.get("adjustments", {}).items():
                    if factor in ["growth", "decline"]:
                        sign = 1 if factor == "growth" else -1
                        multiplier = 1 + sign * pct / 100
                        adjusted.loc[_, "yhat"] *= multiplier
            sc_total = adjusted.tail(3)["yhat"].sum()
            results.append({
                "scenario": sc["name"],
                "projected_quarter_total": round(sc_total, 2),
                "delta_vs_base": round(sc_total - base_total, 2),
                "delta_pct": round((sc_total - base_total) / base_total * 100, 2),
            })

        return pd.DataFrame(results)
