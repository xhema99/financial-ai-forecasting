import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path


class EDA:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def summary(self) -> dict:
        return {
            "shape": self.df.shape,
            "columns": list(self.df.columns),
            "dtypes": self.df.dtypes.astype(str).to_dict(),
            "missing": self.df.isnull().sum().to_dict(),
            "missing_pct": (self.df.isnull().sum() / len(self.df) * 100).to_dict(),
            "duplicates": self.df.duplicated().sum(),
            "describe": self.df.describe(include="all").to_dict(),
        }

    def report(self, output_dir: str = "reports") -> str:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        lines = []
        lines.append("# Financial Data EDA Report\n")
        lines.append(f"**Dataset shape:** {self.df.shape}\n")
        lines.append(f"**Date range:** {self.df['ds'].min()} to {self.df['ds'].max()}\n")
        lines.append(f"**Projects:** {self.df['Proyecto'].nunique()}\n")
        lines.append(f"**Clients:** {self.df['Cliente'].nunique()}\n")
        lines.append("## Column Summary\n")
        for c in self.df.columns:
            dtype = str(self.df[c].dtype)
            nulls = self.df[c].isnull().sum()
            uniq = self.df[c].nunique()
            lines.append(f"- **{c}** ({dtype}): {uniq} unique, {nulls} nulls")

        lines.append("\n## Numerical Distributions\n")
        num_cols = self.df.select_dtypes(include=np.number).columns
        lines.append(self.df[num_cols].describe().to_string())

        lines.append("\n## Categorical Distributions\n")
        for c in ["Proyecto", "Cliente", "Servicio", "Seniority", "Estado"]:
            lines.append(f"\n### {c}\n")
            lines.append(self.df[c].value_counts().to_string())

        lines.append("\n## Correlation Matrix\n")
        corr = self.df[num_cols].corr()
        lines.append(corr.to_string())

        report_text = "\n".join(lines)
        report_path = out / "eda_report.md"
        report_path.write_text(report_text, encoding="utf-8")
        return str(report_path)

    def plot_distributions(self, output_dir: str = "images"):
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        num_cols = ["Ingresos", "HorasFacturadas", "CosteEquipo", "MargenBruto", "Satisfaccion"]

        fig, axes = plt.subplots(3, 2, figsize=(14, 12))
        axes = axes.flatten()
        for i, c in enumerate(num_cols):
            sns.histplot(self.df[c], bins=30, kde=True, ax=axes[i], color="#2563EB")
            axes[i].set_title(f"Distribution of {c}", fontsize=12, fontweight="bold")
            axes[i].axvline(self.df[c].mean(), color="red", linestyle="--", label="Mean")
            axes[i].axvline(self.df[c].median(), color="green", linestyle="--", label="Median")
            axes[i].legend()
        fig.delaxes(axes[-1])
        plt.tight_layout()
        path = out / "distributions.png"
        plt.savefig(path, dpi=150, bbox_inches="tight")
        plt.close()
        return str(path)

    def plot_monthly_trends(self, output_dir: str = "images"):
        out = Path(output_dir)
        monthly = self.df.groupby("ds")[["Ingresos", "CosteEquipo", "MargenBruto"]].sum().reset_index()

        fig, ax = plt.subplots(figsize=(16, 6))
        ax.plot(monthly["ds"], monthly["Ingresos"], marker="o", linewidth=2,
                color="#2563EB", label="Ingresos")
        ax.plot(monthly["ds"], monthly["CosteEquipo"], marker="s", linewidth=2,
                color="#EF4444", label="Coste Equipo")
        ax.plot(monthly["ds"], monthly["MargenBruto"], marker="^", linewidth=2,
                color="#10B981", label="Margen Bruto")
        ax.fill_between(monthly["ds"], monthly["CosteEquipo"], monthly["Ingresos"],
                        alpha=0.1, color="#2563EB")
        ax.set_title("Monthly Revenue, Cost & Margin Trend", fontsize=14, fontweight="bold")
        ax.set_xlabel("Month")
        ax.set_ylabel("EUR (€)")
        ax.legend()
        ax.grid(True, alpha=0.3)
        fig.autofmt_xdate()
        path = out / "monthly_trends.png"
        plt.savefig(path, dpi=150, bbox_inches="tight")
        plt.close()
        return str(path)

    def plot_correlation_heatmap(self, output_dir: str = "images"):
        out = Path(output_dir)
        num_cols = ["Ingresos", "HorasFacturadas", "TarifaHora", "CosteEquipo", "MargenBruto", "Satisfaccion"]
        corr = self.df[num_cols].corr()

        fig, ax = plt.subplots(figsize=(10, 8))
        mask = np.triu(np.ones_like(corr, dtype=bool))
        sns.heatmap(corr, mask=mask, annot=True, fmt=".2f", cmap="RdBu_r",
                    center=0, square=True, linewidths=0.5, ax=ax)
        ax.set_title("Feature Correlation Matrix", fontsize=14, fontweight="bold")
        path = out / "correlation_heatmap.png"
        plt.savefig(path, dpi=150, bbox_inches="tight")
        plt.close()
        return str(path)
