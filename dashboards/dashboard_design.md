# Power BI Dashboard Design — Keedio Financial AI

## Layout

```
┌──────────────────────────────────────────────────────────────┐
│  🚀 KEEDIO FINANCIAL AI — Executive Dashboard               │
│  Period: [Date Range]        Last Updated: [Timestamp]       │
├──────────┬──────────┬──────────┬──────────┬──────────┬───────┤
│ Revenue  │ Gross    │ Cost     │ Avg      │ Billable │ Active│
│ €XXX,XXX │ Margin   │ Ratio    │ Satis-   │ Hours    │ Proj- │
│ (+X.X%)  │ XX.X%    │ XX.X%    │ faction  │ XXX hrs  │ ects  │
│          │          │          │ XX.X%    │          │ XX    │
├──────────┴──────────┴──────────┴──────────┴──────────┴───────┤
│                                                              │
│  [Line Chart] Revenue + Forecast (Historical + 90d Prophet)  │
│  - Actual line (blue)  │  Forecast line (red dashed)         │
│  - Confidence interval (red shaded 80%)                      │
│  - Anomaly markers (red X)                                   │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│  Revenue by Service   │  Margin % Trend     │  Anomalies     │
│  [Stacked Area Chart] │  [Combo Bar+Line]   │  [Scatter]     │
│  - Big Data  - Cloud  │  - Margin € (bar)   │  - Ingresos    │
│  - IA                │  - Margin % (line)  │  - Costes       │
│                      │                     │  - Margen       │
├──────────────────────┴─────────────────────┴────────────────┤
│                                                              │
│  Smart Narrative (AI-generated text):                        │
│  "La caja proyectada caería un 12% en 60 días debido a..."  │
│  "Se detectaron 3 anomalías en ingresos de Jul 2025."       │
│  "Los proyectos de IA muestran márgenes 5% superiores."     │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│  Risk Indicators                    │  Alerts                │
│  🟢 Low Risk   🟡 Medium 🟠 High    │  ⚠ Revenue drop 15%   │
│  🔴 Critical                        │  🚨 Cash risk < 45d   │
└──────────────────────────────────────────────────────────────┘
```

## Visualizations Required

| Visualization | Data | Type | Position |
|---|---|---|---|
| KPI Cards (6) | Revenue, Margin, Cost Ratio, Satisfaction, Hours, Projects | Card | Top row |
| Revenue Forecast | Monthly Revenue + Prophet prediction | Line chart with forecast | Row 2 |
| Revenue by Service | Ingresos grouped by Servicio | Stacked area chart | Row 3 left |
| Margin % Trend | MargenBruto + margen_pct | Combo (bar + line) | Row 3 center |
| Anomaly Scatter | Anomalies by metric | Scatter plot | Row 3 right |
| Smart Narrative | AI-generated insights | Text box (DAX) | Row 4 |
| Risk Matrix | Composite risk score | Shape indicators | Row 5 left |
| Alerts Feed | Triggered alerts | Table/List | Row 5 right |

## DAX Measures

```dax
-- KPIs
Total Revenue = SUM('Cierre_Mensual'[Ingresos])
Total Margin = SUM('Cierre_Mensual'[MargenBruto])
Margin % = DIVIDE([Total Margin], [Total Revenue], 0) * 100
Cost Ratio = DIVIDE(SUM('Cierre_Mensual'[CosteEquipo]), [Total Revenue], 0) * 100
Avg Satisfaction = AVERAGE('Cierre_Mensual'[Satisfaccion])

-- Time Intelligence
Revenue MoM % = 
VAR CurrentMonth = [Total Revenue]
VAR PreviousMonth = CALCULATE([Total Revenue], PREVIOUSMONTH('Calendario'[Date]))
RETURN DIVIDE(CurrentMonth - PreviousMonth, PreviousMonth, 0)

Revenue Forecast = 
// Import Prophet predictions from CSV
SUM('Forecast'[yhat])

-- Smart Narrative (basic)
Insight Narrative = 
VAR RevTrend = [Revenue MoM %]
RETURN 
IF(RevTrend < -0.10, 
    "⚠️ Revenue dropped " & FORMAT(RevTrend, "0.0%") & " — review pipeline",
    "✅ Revenue stable or growing"
)
```

## Color Palette

| Purpose | Hex | Usage |
|---|---|---|
| Primary | #2563EB | KPIs, Revenue line |
| Success | #10B981 | Margin, Positive trends |
| Danger | #EF4444 | Anomalies, Alerts |
| Warning | #F59E0B | Warnings, Medium risk |
| Purple | #8B5CF6 | IA service line |
| Background | #F8FAFC | Page background |
| Card bg | #FFFFFF | Cards |

## Design Principles

1. **CFO-ready**: Clean, no clutter, focus on cash & risk
2. **Left-to-right**: Most critical metrics top-left
3. **Color-coded severity**: Green → Yellow → Orange → Red
4. **Data-ink ratio**: Maximize information, minimize decoration
5. **Responsive**: Fit 1080p screens, readable at 100%
