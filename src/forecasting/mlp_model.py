import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
from pathlib import Path


class MLPFinancialForecaster:
    def __init__(self, df: pd.DataFrame, target: str = "Ingresos",
                 lookback: int = 3):
        self.df = df.copy().reset_index(drop=True)
        self.target = target
        self.lookback = lookback
        self.model: MLPRegressor | None = None
        self.scaler = StandardScaler()
        self.forecast: pd.DataFrame | None = None
        self.metrics: dict = {}

    def _create_sequences(self, series: np.ndarray):
        X, y = [], []
        for i in range(self.lookback, len(series)):
            X.append(series[i - self.lookback : i])
            y.append(series[i])
        return np.array(X), np.array(y)

    def _recursive_predict(self, history: np.ndarray,
                            steps: int) -> np.ndarray:
        predictions = []
        window = history[-self.lookback:].copy()
        for _ in range(steps):
            scaled = self.scaler.transform(window.reshape(1, -1))
            pred = self.model.predict(scaled)[0]
            predictions.append(pred)
            window = np.append(window[1:], pred)
        return np.array(predictions)

    def train(self, test_size: float = 0.2, **mlp_kwargs):
        series = pd.to_numeric(self.df[self.target], errors="coerce").values
        series = series[~np.isnan(series)]

        split = int(len(series) * (1 - test_size))
        train_series = series[:split]
        test_series = series[split:]

        X_train, y_train = self._create_sequences(train_series)
        X_train_scaled = self.scaler.fit_transform(X_train)

        params = {
            "hidden_layer_sizes": (50, 25),
            "activation": "relu",
            "solver": "adam",
            "max_iter": 5000,
            "random_state": 42,
            "early_stopping": False,
        }
        params.update(mlp_kwargs)
        self.model = MLPRegressor(**params)
        self.model.fit(X_train_scaled, y_train)

        train_pred = self.model.predict(X_train_scaled)
        train_mae = mean_absolute_error(y_train, train_pred)
        train_rmse = np.sqrt(mean_squared_error(y_train, train_pred))
        train_mape = np.mean(np.abs((y_train - train_pred) / y_train)) * 100

        if len(test_series) > self.lookback:
            test_pred = self._recursive_predict(train_series, len(test_series))
            y_test = test_series[self.lookback:]
            test_pred = test_pred[:len(y_test)]
            test_mae = mean_absolute_error(y_test, test_pred)
            test_rmse = np.sqrt(mean_squared_error(y_test, test_pred))
            test_mape = np.mean(np.abs((y_test - test_pred) / y_test)) * 100
        else:
            test_mae = test_rmse = test_mape = None

        self.metrics = {
            "MAE": round(train_mae, 2),
            "RMSE": round(train_rmse, 2),
            "MAPE": round(train_mape, 2),
            "MAE_test": round(test_mae, 2) if test_mae else None,
            "RMSE_test": round(test_rmse, 2) if test_rmse else None,
            "MAPE_test": round(test_mape, 2) if test_mape else None,
        }

        return self.model

    def forecast_future(self, periods: int = 90):
        series = pd.to_numeric(self.df[self.target], errors="coerce").values
        series = series[~np.isnan(series)]

        months_ahead = max(1, periods // 30)
        future_preds = self._recursive_predict(series, months_ahead)

        last_date = self.df["ds"].max()
        future_dates = pd.date_range(
            start=last_date + pd.DateOffset(months=1),
            periods=months_ahead, freq="MS"
        )

        self.forecast = pd.DataFrame({
            "ds": future_dates,
            "yhat": future_preds,
            "yhat_lower": future_preds * 0.85,
            "yhat_upper": future_preds * 1.15,
        })
        return self.forecast

    def plot_forecast(self, output_dir: str = "images"):
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        fig, ax = plt.subplots(figsize=(16, 7))
        series = pd.to_numeric(self.df[self.target], errors="coerce").values
        series = series[~np.isnan(series)]

        ax.plot(self.df["ds"], series, marker="o", linewidth=2,
                color="#2563EB", label=f"Historical {self.target}")

        if self.forecast is not None:
            ax.plot(self.forecast["ds"], self.forecast["yhat"],
                    linestyle="--", linewidth=2, color="#8B5CF6",
                    label=f"MLP Forecast {self.target}")
            ax.fill_between(self.forecast["ds"],
                            self.forecast["yhat_lower"],
                            self.forecast["yhat_upper"],
                            alpha=0.2, color="#8B5CF6", label="Uncertainty")

        ax.axvline(x=self.df["ds"].iloc[-1], color="gray",
                   linestyle=":", alpha=0.7, label="Forecast Start")

        ax.set_title(f"{self.target} — MLP Neural Network Forecast",
                     fontsize=14, fontweight="bold")
        ax.set_xlabel("Date")
        ax.set_ylabel("EUR (€)")
        ax.legend()
        ax.grid(True, alpha=0.3)
        fig.autofmt_xdate()

        path = out / f"mlp_forecast_{self.target.lower()}.png"
        plt.savefig(path, dpi=150, bbox_inches="tight")
        plt.close()
        return str(path)

    def get_insights(self) -> list:
        if self.forecast is None:
            return []
        insights = []
        last_hist = self.df[self.target].sum()
        avg_future = self.forecast["yhat"].mean()
        change_pct = round((avg_future - last_hist) / last_hist * 100, 1)
        insights.append(
            f"MLP forecasted average {self.target}: "
            f"€{avg_future:,.0f} ({change_pct:+.1f}% vs last historical period)"
        )
        first = self.forecast["yhat"].iloc[0]
        last = self.forecast["yhat"].iloc[-1]
        trajectory = "upward" if last > first else "downward"
        insights.append(
            f"MLP 30→90 day {self.target} trajectory: {trajectory} "
            f"(€{first:,.0f} → €{last:,.0f})"
        )
        return insights
