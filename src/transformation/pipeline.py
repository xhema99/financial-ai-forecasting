import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.preprocessing import LabelEncoder


class DataPipeline:
    def __init__(self, raw_path: str):
        self.raw_path = Path(raw_path)
        self.df: pd.DataFrame | None = None
        self.label_encoders = {}

    def load(self) -> pd.DataFrame:
        self.df = pd.read_csv(self.raw_path, encoding="utf-8-sig")
        return self.df

    def parse_dates(self, col: str = "Mes") -> pd.DataFrame:
        month_map = {
            "Ene": "Jan", "Feb": "Feb", "Mar": "Mar", "Abr": "Apr",
            "May": "May", "Jun": "Jun", "Jul": "Jul", "Ago": "Aug",
            "Sep": "Sep", "Oct": "Oct", "Nov": "Nov", "Dic": "Dec",
        }
        parts = self.df[col].str.split(" ", expand=True)
        eng_months = parts[0].map(month_map)
        self.df["ds"] = pd.to_datetime(
            eng_months + " " + parts[1], format="%b %Y"
        )
        self.df["year"] = self.df["ds"].dt.year
        self.df["month"] = self.df["ds"].dt.month
        self.df["quarter"] = self.df["ds"].dt.quarter
        return self.df

    def encode_categoricals(self) -> pd.DataFrame:
        cat_cols = ["Proyecto", "Cliente", "Servicio", "Estado", "Equipo", "Seniority"]
        for c in cat_cols:
            le = LabelEncoder()
            self.df[f"{c}_encoded"] = le.fit_transform(self.df[c].astype(str))
            self.label_encoders[c] = le
        return self.df

    def engineer_features(self) -> pd.DataFrame:
        self.df["margen_pct"] = (
            self.df["MargenBruto"] / self.df["Ingresos"] * 100
        )
        self.df["coste_por_hora_real"] = (
            self.df["CosteEquipo"] / self.df["HorasFacturadas"]
        )
        self.df["ingreso_por_hora"] = (
            self.df["Ingresos"] / self.df["HorasFacturadas"]
        )
        return self.df

    def clean(self) -> pd.DataFrame:
        num_cols = ["Ingresos", "HorasFacturadas", "CosteEquipo", "MargenBruto"]
        for c in num_cols:
            self.df[c] = pd.to_numeric(self.df[c], errors="coerce")
        self.df = self.df.dropna(subset=num_cols)
        self.df = self.df.sort_values("ds").reset_index(drop=True)
        return self.df

    def run(self) -> pd.DataFrame:
        self.load()
        self.parse_dates()
        self.clean()
        self.encode_categoricals()
        self.engineer_features()
        return self.df

    def get_monthly_aggregate(self) -> pd.DataFrame:
        monthly = (
            self.df.groupby("ds")
            .agg(
                {
                    "Ingresos": "sum",
                    "CosteEquipo": "sum",
                    "MargenBruto": "sum",
                    "HorasFacturadas": "sum",
                }
            )
            .reset_index()
            .sort_values("ds")
        )
        monthly.columns = ["ds", "Ingresos", "CosteEquipo", "MargenBruto", "HorasFacturadas"]
        monthly["margen_pct"] = monthly["MargenBruto"] / monthly["Ingresos"] * 100
        return monthly
