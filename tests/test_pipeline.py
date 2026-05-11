import sys
import pytest
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.transformation.pipeline import DataPipeline
from src.forecasting.prophet_model import FinancialForecaster


@pytest.fixture(scope="module")
def pipeline():
    p = DataPipeline("data/raw/KEEDIO_Cierre_Mensual.csv")
    df = p.run()
    monthly = p.get_monthly_aggregate()
    return p, df, monthly


class TestDataPipeline:
    def test_loads_correct_number_of_records(self, pipeline):
        _, df, _ = pipeline
        assert len(df) == 128

    def test_has_required_columns(self, pipeline):
        _, df, _ = pipeline
        required = ["ds", "Ingresos", "Proyecto", "Cliente", "Servicio"]
        for col in required:
            assert col in df.columns, f"Missing column: {col}"

    def test_no_null_in_critical_columns(self, pipeline):
        _, df, _ = pipeline
        critical = ["Ingresos", "HorasFacturadas", "CosteEquipo", "MargenBruto"]
        assert df[critical].isnull().sum().sum() == 0

    def test_monthly_aggregate_has_correct_months(self, pipeline):
        _, _, monthly = pipeline
        assert len(monthly) == 16
        assert list(monthly.columns) == [
            "ds", "Ingresos", "CosteEquipo", "MargenBruto", "HorasFacturadas", "margen_pct"
        ]

    def test_engineered_features_exist(self, pipeline):
        _, df, _ = pipeline
        assert "margen_pct" in df.columns
        assert "coste_por_hora_real" in df.columns
        assert "ingreso_por_hora" in df.columns

    def test_categorical_encoding(self, pipeline):
        _, df, _ = pipeline
        assert "Proyecto_encoded" in df.columns
        n_projects = df["Proyecto"].nunique()
        assert df["Proyecto_encoded"].min() == 0
        assert df["Proyecto_encoded"].max() == n_projects - 1


class TestFinancialForecaster:
    def test_train_and_forecast(self, pipeline):
        _, _, monthly = pipeline
        forecaster = FinancialForecaster(monthly, target="Ingresos")
        forecaster.train()
        forecaster.forecast_future(periods=90)
        assert forecaster.model is not None
        assert forecaster.forecast is not None
        assert "MAE" in forecaster.metrics
        assert "MAPE" in forecaster.metrics

    def test_forecast_returns_future_dates(self, pipeline):
        _, _, monthly = pipeline
        forecaster = FinancialForecaster(monthly, target="Ingresos")
        forecaster.train()
        forecaster.forecast_future(periods=90)
        future = forecaster.forecast[forecaster.forecast["ds"] > monthly["ds"].max()]
        assert len(future) > 0

    def test_insights_are_generated(self, pipeline):
        _, _, monthly = pipeline
        forecaster = FinancialForecaster(monthly, target="Ingresos")
        forecaster.train()
        forecaster.forecast_future(periods=90)
        insights = forecaster.get_insights()
        assert len(insights) >= 1

    def test_scenario_analysis(self, pipeline):
        _, _, monthly = pipeline
        forecaster = FinancialForecaster(monthly, target="Ingresos")
        forecaster.train()
        scenarios = [
            {"name": "Base", "adjustments": {}},
            {"name": "Growth +10%", "adjustments": {"growth": 10}},
        ]
        sc_df = forecaster.scenario_analysis(scenarios)
        assert len(sc_df) == 2
        assert "scenario" in sc_df.columns
