# Diseño del Dashboard Power BI — Keedio Financial AI

## Layout

```
┌──────────────────────────────────────────────────────────────┐
│  🚀 KEEDIO FINANCIAL AI — Dashboard Ejecutivo               │
│  Período: [Rango de Fechas]        Última Actualización: [Timestamp]
├──────────┬──────────┬──────────┬──────────┬──────────┬───────┤
│ Ingresos │ Margen   │ Costo    │ Satisf.  │ Horas    │ Proy. │
│ €XXX,XXX │ Bruto    │ Ratio    │ Promedio │ Fact.    │ Activos│
│ (+X.X%)  │ XX.X%    │ XX.X%    │ XX.X%    │ XXX hrs  │ XX    │
├──────────┴──────────┴──────────┴──────────┴──────────┴───────┤
│                                                              │
│  [Gráfico Líneas] Ingresos + Pronóstico (Histórico + 90d Prophet)
│  - Linea real (azul)  │  Línea pronóstico (rojo punteado)   │
│  - Intervalo de confianza (sombreado rojo 80%)               │
│  - Marcadores de anomalías (X roja)                          │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│  Ingresos por Servicio │  Tendencia Margen │  Anomalías      │
│  [Área Apilada]        │  [Combo Barra+Línea] [Dispersión]  │
│  - Big Data  - Cloud   │  - Margen € (barra) │  - Ingresos   │
│  - IA                  │  - Margen % (línea) │  - Costos      │
│                        │                     │  - Margen      │
├──────────────────────┴─────────────────────┴────────────────┤
│                                                              │
│  Narrativa Inteligente (texto generado por IA):              │
│  "La caja proyectada caería un 12% en 60 días debido a..." │
│  "Se detectaron 3 anomalías en ingresos de Jul 2025."       │
│  "Los proyectos de IA muestran márgenes 5% superiores."     │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│  Indicadores de Riesgo          │  Alertas                   │
│  🟢 Bajo   🟡 Medio 🟠 Alto    │  ⚠ Caída ingresos 15%     │
│  🔴 Crítico                     │  🚨 Riesgo caja < 45d     │
└──────────────────────────────────────────────────────────────┘
```

## Visualizaciones Requeridas

| Visualización | Datos | Tipo | Posición |
|---|---|---|---|
| Tarjetas KPI (6) | Ingresos, Margen, Ratio Costo, Satisfacción, Horas, Proyectos | Tarjeta | Fila superior |
| Pronóstico Ingresos | Ingresos mensuales + predicción Prophet | Líneas con pronóstico | Fila 2 |
| Ingresos por Servicio | Ingresos agrupados por Servicio | Área apilada | Fila 3 izquierda |
| Tendencia Margen % | MargenBruto + margen_pct | Combo (barra + línea) | Fila 3 centro |
| Dispersión Anomalías | Anomalías por métrica | Dispersión | Fila 3 derecha |
| Narrativa Inteligente | Insights generados por IA | Cuadro de texto (DAX) | Fila 4 |
| Matriz de Riesgo | Puntaje de riesgo compuesto | Indicadores gráficos | Fila 5 izquierda |
| Feed de Alertas | Alertas disparadas | Tabla/Lista | Fila 5 derecha |

## Medidas DAX

```dax
-- KPIs
Total Revenue = SUM('Cierre_Mensual'[Ingresos])
Total Margin = SUM('Cierre_Mensual'[MargenBruto])
Margin % = DIVIDE([Total Margin], [Total Revenue], 0) * 100
Cost Ratio = DIVIDE(SUM('Cierre_Mensual'[CosteEquipo]), [Total Revenue], 0) * 100
Avg Satisfaction = AVERAGE('Cierre_Mensual'[Satisfaccion])

-- Inteligencia Temporal
Revenue MoM % = 
VAR CurrentMonth = [Total Revenue]
VAR PreviousMonth = CALCULATE([Total Revenue], PREVIOUSMONTH('Calendario'[Date]))
RETURN DIVIDE(CurrentMonth - PreviousMonth, PreviousMonth, 0)

Revenue Forecast = 
// Importar predicciones de Prophet desde CSV
SUM('Forecast'[yhat])

-- Narrativa Inteligente (básica)
Insight Narrative = 
VAR RevTrend = [Revenue MoM %]
RETURN 
IF(RevTrend < -0.10, 
    "⚠️ Los ingresos cayeron " & FORMAT(RevTrend, "0.0%") & " — revisar pipeline",
    "✅ Ingresos estables o en crecimiento"
)
```

## Paleta de Colores

| Propósito | Hex | Uso |
|---|---|---|
| Principal | #2563EB | KPIs, línea de ingresos |
| Éxito | #10B981 | Margen, tendencias positivas |
| Peligro | #EF4444 | Anomalías, Alertas |
| Advertencia | #F59E0B | Advertencias, riesgo medio |
| Púrpura | #8B5CF6 | Línea de servicio IA |
| Fondo | #F8FAFC | Fondo de página |
| Fondo tarjeta | #FFFFFF | Tarjetas |

## Principios de Diseño

1. **Listo para CFO**: Limpio, sin saturación, enfoque en caja y riesgo
2. **Izquierda a derecha**: Métricas más críticas en la esquina superior izquierda
3. **Severidad por color**: Verde → Amarillo → Naranja → Rojo
4. **Ratio dato-tinta**: Maximizar información, minimizar decoración
5. **Responsive**: Que entre en pantallas 1080p, legible al 100%
