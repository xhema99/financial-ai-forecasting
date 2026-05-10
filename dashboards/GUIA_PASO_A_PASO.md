# Guía Paso a Paso — Dashboard Power BI

> Para el proyecto **Keedio Financial AI** · Basado en `dashboard_design.md`

---

## 📥 1. Instalar Power BI Desktop

Si no lo tenés:

1. Andá a [powerbi.microsoft.com/desktop](https://powerbi.microsoft.com/desktop)
2. Click en **"Descargar gratis"**
3. Ejecutá el instalador (siguiente, siguiente, siguiente)
4. Abrí Power BI Desktop

---

## 📂 2. Cargar los datos

El pipeline ya genera un CSV limpio para Power BI. Sino, usamos el CSV original.

1. En Power BI, andá a la cinta de opciones: **Inicio → Obtener datos → Texto/CSV**
2. Navegá hasta:
   ```
   financial-ai-forecasting-master\data\raw\KEEDIO_Cierre_Mensual.csv
   ```
3. Click en **Cargar**

> Si el pipeline generó `data/processed/for_powerbi.csv`, usá ese (viene más limpio).

4. En el panel derecho (Campos), deberías ver la tabla `KEEDIO_Cierre_Mensual` con todas las columnas.

---

## 📅 3. Crear la tabla de calendario (para inteligencia temporal)

Las funciones como `PREVIOUSMONTH` necesitan una tabla de fechas aparte.

1. Andá a la pestaña **Modelado → Nueva tabla**
2. Pegá esto:

```dax
Calendario = 
CALENDAR(
    MIN(KEEDIO_Cierre_Mensual[Mes]),
    MAX(KEEDIO_Cierre_Mensual[Mes]) + 90
)
```

3. En la misma tabla, creá las columnas calculadas:

```dax
Año = YEAR(Calendario[Date])

Mes = FORMAT(Calendario[Date], "mmm")

MesNum = MONTH(Calendario[Date])
```

4. Ahora relacioná las tablas:
   - Andá a **Modelo** (icono de diagrama a la izquierda)
   - Arrastrá `Calendario[Date]` sobre `KEEDIO_Cierre_Mensual[Mes]`
   - Se crea una línea entre las tablas

---

## 📐 4. Crear las medidas DAX

1. Andá a **Modelado → Nueva medida**
2. Copiá y pega **una por una** estas medidas:

```dax
Total Revenue = SUM(KEEDIO_Cierre_Mensual[Ingresos])
```

```dax
Total Margin = SUM(KEEDIO_Cierre_Mensual[MargenBruto])
```

```dax
Margin % = DIVIDE([Total Margin], [Total Revenue], 0) * 100
```

```dax
Cost Ratio = DIVIDE(SUM(KEEDIO_Cierre_Mensual[CosteEquipo]), [Total Revenue], 0) * 100
```

```dax
Avg Satisfaction = AVERAGE(KEEDIO_Cierre_Mensual[Satisfaccion])
```

```dax
Revenue MoM % = 
VAR IngresoMesActual = [Total Revenue]
VAR IngresoMesAnterior = CALCULATE([Total Revenue], PREVIOUSMONTH('Calendario'[Date]))
RETURN DIVIDE(IngresoMesActual - IngresoMesAnterior, IngresoMesAnterior, 0)
```

```dax
Insight Narrative = 
VAR RevTrend = [Revenue MoM %]
RETURN 
IF(RevTrend < -0.10, 
    "⚠️ Los ingresos cayeron " & FORMAT(RevTrend, "0.0%") & " — revisar pipeline",
    "✅ Ingresos estables o en crecimiento"
)
```

---

## 🎨 5. Armar el dashboard

### 5.1 — Las 6 tarjetas KPI

Vamos a crear la primera fila con 6 tarjetas.

1. En el panel **Visualizaciones**, click en el ícono **Tarjeta** (un rectángulo con número)
2. Arrastrá la medida `Total Revenue` al campo **Campos**
3. Con la tarjeta seleccionada, andá al panel **Formato** (rodillo)
   - **Llamada de valor → Fuente**: Tamaño 24, negrita
   - **Etiqueta de título**: Activado, escribí "Ingresos"
4. Repetí para las otras 5 métricas:
   - `Margin %` → "Margen Bruto"
   - `Cost Ratio` → "Ratio Costo"
   - `Avg Satisfaction` → "Satisfacción"
   - Contá las horas: arrastrá `HorasFacturadas` → **Título**: "Horas Facturadas"
   - Contá los proyectos: arrastrá `Proyecto` (como **Conteo**) → **Título**: "Proyectos Activos"

📌 *Tip: Seleccioná todas las tarjetas (Ctrl+click) y en Formato poné el mismo estilo a todas juntas*

### 5.2 — Pronóstico de ingresos (gráfico de líneas)

1. Click en **Gráfico de líneas** (primer ícono de líneas)
2. Arrastrá `Calendario[Date]` al **Eje X**
3. Arrastrá `Total Revenue` a **Valores**
4. Con el gráfico seleccionado, andá a **Formato → Líneas**:
   - Color: `#2563EB` (azul)
   - Ancho: 3
5. **Título**: "Ingresos + Pronóstico 90 días"

#### Agregar el forecast de Prophet

Para mostrar la predicción, necesitás los datos del modelo:

1. Ejecutá el pipeline: `python main.py` (genera predicciones)
2. Si el forecast se guardó como CSV, importalo como nueva tabla:
   **Inicio → Obtener datos → Texto/CSV → forecast_output.csv**
3. En el gráfico de líneas, agregá la columna `yhat` (predicción Prophet) como segunda línea
4. Cambiale el color a rojo punteado (`#EF4444`, Estilo: guiones)

### 5.3 — Ingresos por Servicio (área apilada)

1. Click en **Gráfico de áreas**
2. **Eje X**: `Calendario[Date]`
3. **Valores**: `Total Revenue`
4. **Leyenda**: `Servicio` (Big Data, Cloud, IA)
5. En **Formato → Áreas → Colores**:
   - Big Data: `#2563EB`
   - Cloud: `#F59E0B`
   - IA: `#8B5CF6`
6. **Título**: "Ingresos por Servicio"

### 5.4 — Tendencia de Margen (combo)

1. Click en **Gráfico de columnas agrupadas y líneas**
2. **Eje compartido**: `Calendario[Date]`
3. **Valores de columna**: `Total Margin`
4. **Valores de línea**: `Margin %`
5. **Título**: "Tendencia del Margen"

### 5.5 — Anomalías (dispersión)

Si tenés los datos de anomalías:

1. Click en **Gráfico de dispersión**
2. **Detalles**: `Proyecto`
3. **Eje X**: `HorasFacturadas`
4. **Eje Y**: `Ingresos`
5. **Título**: "Anomalías Detectadas"
6. En **Formato → Colores de datos**, poné las anomalías en rojo

### 5.6 — Smart Narrative

1. Click en el ícono **Smart Narrative** (cuadro de texto con chispa ✨)
   *Si no lo ves, buscá "Narrativa inteligente" en el panel Visualizaciones*
2. Arrastrá la medida `Insight Narrative` al campo
3. Ajustá el tamaño del cuadro

> Si no aparece Smart Narrative, creá un **Cuadro de texto** y pegá:
> ```
> 📊 Los ingresos muestran una tendencia [alcista/estable].
> ⚠️ El margen bruto se mantiene en [X]%.
> 🚨 [N] anomalías detectadas en el período.
> ```

### 5.7 — Indicadores de riesgo

1. Usá **Gráfico de rectángulos** o **Tarjetas múltiples**
2. Creá una medida de riesgo:

```dax
Risk Level = 
VAR AvgMargin = [Margin %]
RETURN
SWITCH(
    TRUE(),
    AvgMargin > 35, "🟢 Bajo",
    AvgMargin > 25, "🟡 Medio",
    AvgMargin > 15, "🟠 Alto",
    "🔴 Crítico"
)
```

3. Arrastrá `Risk Level` al gráfico

### 5.8 — Feed de alertas

1. Click en **Tabla**
2. Arrastrá el proyecto y las métricas que quieras monitorear
3. **Título**: "Alertas Activas"
4. En **Formato → Estilo**: Elegí un estilo con bordes

---

## 🎯 6. Ajustar colores y formato

Para que el dashboard se vea profesional:

1. **Fondo de página**: 
   - Formato → Fondo de página → Color: `#F8FAFC`

2. **Títulos**:
   - Fuente: Segoe UI (la default de Power BI)
   - Tamaño: 16-18 para gráficos, 12-14 para tarjetas
   - Color: gris oscuro (#333)

3. **Bordes**:
   - Cada visual → Formato → Borde → Activar
   - Color: gris claro (#E2E8F0), radio 4px

---

## 📸 7. Sacar las capturas para el entregable

Una vez que el dashboard está armado:

1. Ajustá la ventana para que se vea todo en pantalla
2. **Archivo → Exportar → Exportar a PDF** (opcional)
3. Presioná **Windows + Shift + S** → seleccioná el área del dashboard
4. Guardalo como `dashboard_keedio.png`
5. Copiá esa imagen al repo:
   ```
   financial-ai-forecasting-master\images\dashboard_keedio.png
   ```

---

## ✅ Checklist de entregables

| # | Entregable | Dónde va |
|---|---|---|
| 1 | Notebook con forecasting | `notebooks/02_Forecasting.ipynb` |
| 2 | Dataset CSV | `data/raw/KEEDIO_Cierre_Mensual.csv` ✅ |
| 3 | Captura del dashboard | `images/dashboard_keedio.png` |
| 4 | Captura Smart Narrative | `images/smart_narrative.png` |
| 5 | Documento de insights | `reports/executive_insights.md` |

---

> 💡 **Tip final**: No intentes que quede perfecto de una. Primero poné todos los gráficos, después ajustá colores y formato. Power BI es 80% funcionalidad, 20% estética. Empezá por lo que funciona.
