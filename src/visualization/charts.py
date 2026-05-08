import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from pathlib import Path

matplotlib.rcParams["font.family"] = "sans-serif"
matplotlib.rcParams["font.size"] = 11
COLORS = {
    "primary": "#2563EB",
    "danger": "#EF4444",
    "success": "#10B981",
    "warning": "#F59E0B",
    "purple": "#8B5CF6",
    "gray": "#6B7280",
}


class ExecutiveCharts:
    def __init__(self, df: pd.DataFrame, monthly_df: pd.DataFrame):
        self.df = df
        self.monthly = monthly_df

    def revenue_by_service(self, output_dir: str = "images"):
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        fig, ax = plt.subplots(figsize=(12, 6))
        pivot = self.df.pivot_table(
            index="ds", columns="Servicio", values="Ingresos", aggfunc="sum"
        )
        pivot.plot(kind="area", ax=ax, alpha=0.7,
                   color=[COLORS["primary"], COLORS["success"], COLORS["purple"]])
        ax.set_title("Revenue by Service Line", fontsize=14, fontweight="bold")
        ax.set_ylabel("EUR (€)")
        ax.legend(title="Service")
        ax.grid(True, alpha=0.3)
        fig.autofmt_xdate()
        path = out / "revenue_by_service.png"
        plt.savefig(path, dpi=150, bbox_inches="tight")
        plt.close()
        return str(path)

    def margin_analysis(self, output_dir: str = "images"):
        out = Path(output_dir)
        fig, ax1 = plt.subplots(figsize=(14, 6))
        ax1.bar(self.monthly["ds"], self.monthly["MargenBruto"],
                color=COLORS["success"], alpha=0.7, label="Gross Margin")
        ax1.set_ylabel("Margin (€)", color=COLORS["success"])
        ax1.tick_params(axis="y", labelcolor=COLORS["success"])

        ax2 = ax1.twinx()
        ax2.plot(self.monthly["ds"], self.monthly["margen_pct"],
                 marker="D", color=COLORS["primary"], linewidth=2,
                 label="Margin %")
        ax2.set_ylabel("Margin (%)", color=COLORS["primary"])
        ax2.tick_params(axis="y", labelcolor=COLORS["primary"])

        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")
        ax1.set_title("Gross Margin — Absolute & Relative", fontsize=14, fontweight="bold")
        fig.autofmt_xdate()
        ax1.grid(True, alpha=0.3)
        path = out / "margin_analysis.png"
        plt.savefig(path, dpi=150, bbox_inches="tight")
        plt.close()
        return str(path)

    def seniority_performance(self, output_dir: str = "images"):
        out = Path(output_dir)
        fig, axes = plt.subplots(1, 3, figsize=(16, 5))
        seniority_order = ["Junior", "SemiSenior", "Senior"]

        for ax, metric in zip(axes, ["Ingresos", "MargenBruto", "Satisfaccion"]):
            data = self.df.groupby("Seniority")[metric].mean().reindex(seniority_order)
            colors_ = [COLORS["purple"], COLORS["primary"], COLORS["success"]]
            bars = ax.bar(data.index, data.values, color=colors_, alpha=0.8)
            ax.set_title(f"Avg {metric} by Seniority", fontsize=12, fontweight="bold")
            ax.set_ylabel(metric)
            for bar, val in zip(bars, data.values):
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                        f"{val:,.0f}" if metric != "Satisfaccion" else f"{val:.1f}",
                        ha="center", va="bottom", fontsize=9)
        plt.tight_layout()
        path = out / "seniority_performance.png"
        plt.savefig(path, dpi=150, bbox_inches="tight")
        plt.close()
        return str(path)

    def satisfaction_trend(self, output_dir: str = "images"):
        out = Path(output_dir)
        monthly_sat = self.df.groupby("ds")["Satisfaccion"].mean().reset_index()
        fig, ax = plt.subplots(figsize=(14, 5))
        ax.plot(monthly_sat["ds"], monthly_sat["Satisfaccion"],
                marker="o", linewidth=2, color=COLORS["purple"])
        ax.axhline(y=80, color=COLORS["success"], linestyle="--", alpha=0.7,
                   label="Target (80)")
        ax.axhline(y=70, color=COLORS["warning"], linestyle="--", alpha=0.5,
                   label="Minimum (70)")
        ax.fill_between(monthly_sat["ds"], monthly_sat["Satisfaccion"], 80,
                        where=monthly_sat["Satisfaccion"] < 80,
                        color=COLORS["danger"], alpha=0.1)
        ax.set_title("Client Satisfaction Trend", fontsize=14, fontweight="bold")
        ax.set_ylabel("Satisfaction Score")
        ax.legend()
        ax.grid(True, alpha=0.3)
        fig.autofmt_xdate()
        path = out / "satisfaction_trend.png"
        plt.savefig(path, dpi=150, bbox_inches="tight")
        plt.close()
        return str(path)

    def kpi_dashboard(self, output_dir: str = "images"):
        out = Path(output_dir)
        fig, axes = plt.subplots(2, 3, figsize=(18, 8))
        axes = axes.flatten()
        monthly = self.monthly
        latest = monthly.iloc[-1]
        prev = monthly.iloc[-2]

        kpis = [
            ("Total Revenue (Latest Month)",
             f"€{latest['Ingresos']:,.0f}",
             f"{((latest['Ingresos'] - prev['Ingresos']) / prev['Ingresos'] * 100):+.1f}% MoM"),
            ("Gross Margin",
             f"€{latest['MargenBruto']:,.0f}",
             f"{latest['margen_pct']:.1f}% margin"),
            ("Total Costs",
             f"€{latest['CosteEquipo']:,.0f}",
             f"{latest['CosteEquipo'] / latest['Ingresos'] * 100:.1f}% of revenue"),
            ("Avg Satisfaction",
             f"{self.df['Satisfaccion'].mean():.1f}/100",
             f"Min: {self.df['Satisfaccion'].min()}, Max: {self.df['Satisfaccion'].max()}"),
            ("Total Billed Hours",
             f"{int(monthly['HorasFacturadas'].sum()):,}",
             f"{int(monthly['HorasFacturadas'].mean()):,} avg/month"),
            ("Active Projects",
             f"{self.df[self.df['Estado'] == 'Activo']['Proyecto'].nunique()}",
             f"Total unique: {self.df['Proyecto'].nunique()}"),
        ]

        for ax, (title, value, sub) in zip(axes, kpis):
            ax.text(0.5, 0.65, value, fontsize=28, fontweight="bold",
                    ha="center", va="center", color=COLORS["primary"])
            ax.text(0.5, 0.3, sub, fontsize=11, ha="center", va="center",
                    color=COLORS["gray"])
            ax.set_title(title, fontsize=12, fontweight="bold", pad=15)
            ax.set_frame_on(False)
            ax.tick_params(left=False, labelleft=False, bottom=False, labelbottom=False)

        path = out / "kpi_dashboard.png"
        plt.savefig(path, dpi=150, bbox_inches="tight")
        plt.close()
        return str(path)

    def generate_all(self, output_dir: str = "images"):
        paths = {}
        paths["kpi"] = self.kpi_dashboard(output_dir)
        paths["revenue_by_service"] = self.revenue_by_service(output_dir)
        paths["margin"] = self.margin_analysis(output_dir)
        paths["seniority"] = self.seniority_performance(output_dir)
        paths["satisfaction"] = self.satisfaction_trend(output_dir)
        return paths
