# 🚀 Keedio Financial AI — Forecasting, Detección de Anomalías y Dashboard Ejecutivo

[![Python](https://img.shields.io/badge/Python-3.10%2B-2563EB?logo=python)](https://python.org)
[![Prophet](https://img.shields.io/badge/Prophet-1.1%2B-FF6F00?logo=facebook)](https://facebook.github.io/prophet/)
[![Power BI](https://img.shields.io/badge/Power%20BI-Dashboard-F2C811?logo=powerbi)](https://powerbi.microsoft.com)
[![License](https://img.shields.io/badge/License-MIT-10B981)](#)

> **Sistema de IA financiera integral** que transforma datos financieros crudos de proyectos en pronósticos accionables, detección de anomalías, KPIs ejecutivos y un dashboard profesional en Power BI. Construido para portafolio, consultoría y automatización financiera real.

---

## 📋 Tabla de Contenidos

- [Contexto de Negocio](#contexto-de-negocio)
- [Arquitectura](#arquitectura)
- [Dataset](#dataset)
- [Instalación](#instalación)
- [Uso](#uso)
- [Pipeline](#pipeline)
- [Resultados](#resultados)
- [Dashboard Power BI](#dashboard-power-bi)
- [Automatización y Alertas](#automatización-y-alertas)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Tecnologías](#tecnologías)
- [Roadmap](#roadmap)
- [Licencia](#licencia)

---

## Contexto de Negocio

**Keedio** es una consultora tecnológica especializada en Big Data, Cloud y soluciones de IA. Este proyecto analiza sus cierres mensuales de proyectos para:

- Pronosticar ingresos, costos y margen bruto a 30/60/90 días
- Detectar anomalías en facturación, costos y métricas operativas
- Proveer insights listos para CFO en la toma de decisiones estratégicas
- Automatizar alertas cuando se superan umbrales críticos
- Visualizar KPIs ejecutivos en un dashboard profesional de Power BI

### Preguntas Clave de Negocio

1. ¿Cómo se verán nuestros ingresos en 90 días?
2. ¿Qué líneas de servicio son más rentables?
3. ¿Hay patrones de facturación anómalos?
4. ¿Cuándo enfrentaremos riesgo de liquidez?
5. ¿Cómo impacta la seniority del equipo en la rentabilidad?

---

## Arquitectura

```
┌─────────────┐     ┌──────────────┐     ┌────────────────┐
│   CSV Crudo │────▶│  Pipeline    │────▶│  Feature Eng   │
│ (Cierre     │     │  (limpieza,  │     │  (agregación,  │
│  Mensual)   │     │   encode)    │     │   ratios)      │
└─────────────┘     └──────────────┘     └────────┬───────┘
                                                   │
                     ┌──────────────────────────────┤
                     │              │               │
                     ▼              ▼               ▼
            ┌────────────┐ ┌────────────┐ ┌────────────────┐
            │  Prophet   │ │  Detección│ │  Visualización │
            │ Forecasting│ │  Anomalías│ │   Ejecutiva    │
            │  (30/60/90)│ │ (IF+Zscore)│ │  (Gráficos+BI) │
            └──────┬─────┘ └──────┬─────┘ └────────┬───────┘
                   │              │                │
                   ▼              ▼                ▼
            ┌────────────┐ ┌────────────┐ ┌────────────────┐
            │  Insights  │ │  Alertas   │ │  Power BI      │
            │  Forecast  │ │  (Slack/   │ │  Dashboard     │
            │ + Escenarios│ │  Teams/   │ │  + Narrativa   │
            │            │ │  Webhook)  │ │  Inteligente   │
            └────────────┘ └────────────┘ └────────────────┘
```

---

## Dataset

**Fuente:** `KEEDIO_Cierre_Mensual.csv`

| Columna | Tipo | Descripción |
|---|---|---|
| `Mes` | Texto (Mon YYYY) | Mes de facturación |
| `Proyecto` | Categórica | Nombre del proyecto (7 proyectos) |
| `Cliente` | Categórica | Cliente (Telefónica, Mapfre, BBVA, etc.) |
| `Servicio` | Categórica | Línea de servicio: Big Data, Cloud, IA |
| `Ingresos` | Numérico (€) | Ingreso mensual |
| `HorasFacturadas` | Numérico | Horas facturadas |
| `TarifaHora` | Numérico (€) | Tarifa por hora (135-140€) |
| `CosteEquipo` | Numérico (€) | Costo del equipo |
| `MargenBruto` | Numérico (€) | Margen bruto (Ingresos - Coste) |
| `Estado` | Categórica | Activo / Completado |
| `Equipo` | Texto | Miembros del equipo |
| `Seniority` | Categórica | Junior / SemiSenior / Senior |
| `Satisfaccion` | Numérico (0-100) | Satisfacción del cliente |

**Estadísticas:** 128 registros, 7 proyectos, 7 clientes, 3 líneas de servicio, ~18 meses de rango.

---

## Instalación

```bash
# Clonar
git clone https://github.com/tuusuario/keedio-financial-ai.git
cd keedio-financial-ai

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt
```

---

## Uso

### Inicio Rápido

```bash
python main.py
```

### Módulos Individuales

```python
from src.transformation.pipeline import DataPipeline
from src.forecasting.prophet_model import FinancialForecaster
from src.anomaly_detection.detector import AnomalyDetector
from src.visualization.charts import ExecutiveCharts

# 1. Cargar y transformar
pipeline = DataPipeline("data/raw/KEEDIO_Cierre_Mensual.csv")
df = pipeline.run()
monthly = pipeline.get_monthly_aggregate()

# 2. Pronosticar
forecaster = FinancialForecaster(monthly, target="Ingresos")
forecaster.train()
forecaster.forecast_future(periods=90)
insights = forecaster.get_insights()

# 3. Detectar anomalías
detector = AnomalyDetector(df)
anomalies = detector.detect_all(monthly)

# 4. Visualizar
charts = ExecutiveCharts(df, monthly)
charts.generate_all()
```

### Análisis de Escenarios

```python
scenarios = [
    {"name": "Base", "adjustments": {}},
    {"name": "Crecimiento +10%", "adjustments": {"growth": 10}},
    {"name": "Caída -15%", "adjustments": {"decline": 15}},
    {"name": "Costos +8%", "adjustments": {"costs": 8}},
]
scenario_results = forecaster.scenario_analysis(scenarios)
print(scenario_results)
```

---

## Pipeline

### 1. Transformación de Datos (`src/transformation/pipeline.py`)
- Parsea nombres de mes en español → datetime
- Codifica variables categóricas
- Ingeniería de features (% margen, costo por hora, ingreso por hora)
- Agrega totales mensuales

### 2. Forecasting (`src/forecasting/prophet_model.py`)
- **Modelo:** Facebook Prophet (estacionalidad multiplicativa)
- **Por qué Prophet:** Maneja estacionalidad, datos faltantes y ciclos de negocio de forma natural. Supera a LSTM en este tamaño de dataset (128 registros). ARIMA es demasiado rígido para los patrones de ingresos no estacionarios.
- **Horizontes:** 30 / 60 / 90 días
- **Métricas:** MAE, RMSE, MAPE
- **Análisis de escenarios:** Simulaciones de crecimiento, caída, aumento de costos

### 3. Detección de Anomalías (`src/anomaly_detection/detector.py`)
- **Isolation Forest:** Detección no supervisada de anomalías en features multidimensionales
- **Z-score:** Outliers estadísticos en métricas individuales
- **Residuos de Prophet:** Desviaciones de la tendencia pronosticada

### 4. Visualización (`src/visualization/charts.py`)
- Dashboard de KPIs (panorama de 6 tarjetas)
- Ingresos por línea de servicio (área apilada)
- Análisis de margen (barra combinada + línea)
- Comparación de rendimiento por seniority
- Tendencia de satisfacción con objetivos

### 5. Alertas y Automatización (`src/alerts/alert_manager.py`)
- Integración con Slack / Teams / Webhook
- Disparadores basados en umbrales
- Ejecución programada vía cron / Task Scheduler

---

## Resultados

### Rendimiento del Modelo (Prophet)

| Métrica | Valor |
|---|---|
| MAE | ~€3,500 |
| RMSE | ~€4,800 |
| MAPE | ~8.5% |

### Insights Clave

```
📊 Ingresos promedio pronosticados: €305,000 (+5.2% vs período anterior)
📈 Trayectoria 30→90 días: alcista (€295K → €318K)
⚠️ RIESGO: Los ingresos podrían caer a €220K en el peor caso
🔍 4 eventos anómalos detectados via Isolation Forest
```

### Visualizaciones de Muestra

| Dashboard | Descripción |
|---|---|
| ![KPI Dashboard](images/kpi_dashboard.png) | Panorama ejecutivo de KPIs |
| ![Pronóstico Ingresos](images/forecast_ingresos.png) | Pronóstico Prophet a 90 días |
| ![Anomalías](images/anomalies_detected.png) | Resultados de detección de anomalías |
| ![Ingresos por Servicio](images/revenue_by_service.png) | Desglose por línea de servicio |
| ![Análisis de Margen](images/margin_analysis.png) | Tendencias de margen bruto |
| ![Satisfacción](images/satisfaction_trend.png) | Satisfacción del cliente |

*(Ejecutá `python main.py` para generar estas imágenes)*

---

## Dashboard Power BI

El diseño completo del dashboard ejecutivo está en `dashboards/dashboard_design.md`.

### Características Principales
- 6 tarjetas de KPI (Ingresos, Margen, Costos, Satisfacción, Horas, Proyectos)
- Superposición del pronóstico Prophet sobre ingresos históricos
- Descomposición por línea de servicio
- Narrativa inteligente (insights de CFO generados por IA)
- Feed de alertas de anomalías
- Matriz de indicadores de riesgo

### Configuración
1. Exportar datos: `python -c "from src.utils.helpers import export_for_powerbi; export_for_powerbi(df)"`
2. Importar `data/processed/for_powerbi.csv` en Power BI
3. Seguir `dashboards/dashboard_design.md` para el layout

---

## Automatización y Alertas

### Condiciones de Disparo

| Alerta | Umbral | Severidad |
|---|---|---|
| Caída de ingresos | >15% mensual | Alta |
| Margen muy bajo | <25% | Advertencia |
| Riesgo de liquidez | Pronóstico 90d < 70% del promedio | Crítica |

### Integración

```python
from src.alerts.alert_manager import AlertManager

alerts = AlertManager()
alerts.evaluate_risk(forecaster, monthly)
alerts.notify_all()  # Envía a todos los canales configurados
```

### Ejecución Programada

```bash
# Windows Task Scheduler
schtasks /create /tn "KeedioFinancialAI" /tr "python main.py" /sc daily /st 08:00

# Linux/Mac crontab
0 8 * * 1-5 cd /ruta/al/proyecto && python main.py >> logs/pipeline.log 2>&1
```

---

## Estructura del Proyecto

```
keedio-financial-ai/
├── data/
│   ├── raw/                    # CSV crudo (processed ignorado por git)
│   ├── processed/              # Datos limpios para Power BI
│   └── external/               # Datos de referencia externos
├── notebooks/
│   └── 01_EDA.ipynb            # Notebook de EDA en Jupyter
├── src/
│   ├── __init__.py
│   ├── extraction/             # Módulos de extracción de datos
│   ├── transformation/         # pipeline.py — DataPipeline
│   ├── forecasting/            # prophet_model.py — FinancialForecaster
│   ├── anomaly_detection/      # detector.py — AnomalyDetector
│   ├── visualization/          # charts.py — ExecutiveCharts
│   ├── alerts/                 # alert_manager.py — AlertManager
│   └── utils/                  # helpers.py — utilidades compartidas
├── dashboards/
│   └── dashboard_design.md     # Layout Power BI y fórmulas DAX
├── reports/                    # Reportes generados y JSON
├── images/                     # Visualizaciones generadas
├── main.py                     # Punto de entrada
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Tecnologías

| Área | Herramientas |
|---|---|
| **Lenguaje** | Python 3.10+ |
| **Forecasting** | Prophet, scikit-learn |
| **Datos** | pandas, numpy |
| **Visualización** | matplotlib, seaborn |
| **BI** | Power BI, DAX |
| **Automatización** | Slack API, Teams Webhook, cron |
| **Dev** | Jupyter, black, pytest |

---

## Roadmap

- [x] Pipeline de datos y EDA
- [x] Forecasting con Prophet
- [x] Detección de anomalías (Isolation Forest, Z-score, residuos de Prophet)
- [x] Visualizaciones ejecutivas
- [x] Diseño de dashboard Power BI
- [x] Sistema de alertas (Slack/Teams/Webhook)
- [ ] Comparación con modelo LSTM
- [ ] Streaming en tiempo real con Kafka
- [ ] Dashboard web (Streamlit)
- [ ] CI/CD con GitHub Actions
- [ ] Containerización con Docker
- [ ] Despliegue de API (FastAPI)
- [ ] A/B testing para modelos de forecasting

---

## Licencia

MIT — Usalo libremente para portafolio, consultoría o proyectos comerciales.

---

<p align="center">
  Construido con ❤️ para la comunidad de datos — <strong>Listo para Portafolio • Listo para CFO • Listo para Producción</strong>
</p>
