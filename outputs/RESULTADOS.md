# Resultados de Análisis - Tres Soldados

Este directorio almacena todos los resultados del análisis de fractales, creek perdices y trading.

## Estructura de Carpetas

```
outputs/
├── fractal_tops_and_bottoms/    # Fractales y creek perdices
├── tracking_records/             # Registros de trading (CSV)
└── tablas_html/                  # Reportes HTML de estrategias
```

---

## 📁 fractal_tops_and_bottoms/

**Propósito**: Almacena los resultados del análisis de fractales (TOPs/BOTTOMs) y creek perdices (zonas de consolidación).

### Archivos Generados

#### 1. Fractales (Detección Zigzag)
```
fractals_es_1min_data_{fecha}_zigzag_{sensibilidad}.csv
```

**Ejemplos:**
- `fractals_es_1min_data_2023_03_02_zigzag_0.1.csv` - Sensibilidad 0.1%
- `fractals_es_1min_data_2023_03_10_zigzag_0.1.csv` - Sensibilidad 0.1%

**Columnas:**
- `index`: Índice de la vela en datos originales
- `timestamp`: Timestamp del fractal (UTC)
- `price`: Precio del fractal
- `type`: TOP o BOTTOM
- `distance_usd`: Distancia en USD al siguiente fractal
- `distance_bars`: Cantidad de velas al siguiente fractal
- `distance_ratio`: Ratio USD/barra
- `swing_size`: Clasificación (noise, small, big)
- `dist_ratio_avg`: Media móvil 3 períodos de distance_ratio

#### 2. Creek Perdices (Zonas de Consolidación)
```
true_tops_creek_perdices_{fecha}_tol_{tolerancia}.csv
```

**Ejemplos:**
- `true_tops_creek_perdices_2023_03_02_tol_2.0.csv` - Tolerancia ±2.0 puntos
- `true_tops_creek_perdices_2023_03_10_tol_2.0.csv` - Tolerancia ±2.0 puntos

**Columnas:**
- `group`: Nombre del cluster (cluster_A, cluster_B, etc.)
- `top_index`: Índice del fractal desde fractals CSV
- `timestamp`: Timestamp del primer TOP
- `price`: Precio del primer TOP
- `cluster_size`: Número de TOPs en el cluster
- `first_top_idx`: Índice del primer TOP
- `last_top_idx`: Índice del último TOP
- `last_top_timestamp`: Timestamp del último TOP
- `creek_price`: Precio promedio (nivel creek)
- `breakout_timestamp`: Primera vela que cierra arriba del creek
- `mastercandle`: "master" o "none"
- `mastercandle_timestamp`: Timestamp del master candle
- `mastercandle_close`: Precio de cierre del master candle
- `mastercandle_range`: Rango del master candle
- `mastercandle_upper_tail_pct`: Porcentaje de mecha superior
- `true_volume1_time`: Timestamp vela alto volumen 1
- `true_volume1_value`: Volumen de vela 1
- `true_volume2_time`: Timestamp vela alto volumen 2
- `true_volume2_value`: Volumen de vela 2
- `true_volume3_time`: Timestamp vela alto volumen 3
- `true_volume3_value`: Volumen de vela 3

### Criterios de Detección

**Creek Perdices:**
1. TOPs consecutivos dentro de tolerancia (default: ±2.0 puntos)
2. Mínimo 2 TOPs en el cluster
3. TOPs deben ser adyacentes en la secuencia de fractales

**Master Candles:**
- Cierre > nivel creek
- Rango > rango promedio de consolidación
- Mecha superior ≤ 20% del rango

**Alto Volumen:**
- Volumen ≥ 1.5x promedio
- Cierre ≤ percentil 70 (porción baja de la zona)
- Hasta 3 velas de mayor volumen por cluster

### Scripts que Generan Estos Archivos

```bash
# Pipeline completo
python main.py

# Scripts individuales
python quant_stat/find_tops_and_bottoms.py         # Fractales
python quant_stat/find_true_tops.py                # Creek perdices
python quant_stat/find_true_mastercandle.py        # Master candles
python quant_stat/find_true_volume.py              # Alto volumen
```

---

## 📁 tracking_records/

**Propósito**: Almacena los registros de trading en formato CSV (trades ejecutados por las estrategias).

### Archivos Generados

```
trading_record_strat1_crossover_{fecha}.csv
```

**Ejemplo:**
- `trading_record_strat1_crossover_2023_03_13.csv`

**Columnas:**
- `trade_id`: ID único del trade
- `cluster`: Nombre del cluster (cluster_A, cluster_B, etc.)
- `entry_type`: MASTER o BREAKOUT
- `entry_time`: Timestamp de entrada (UTC)
- `entry_price`: Precio de entrada
- `exit_time`: Timestamp de salida (UTC)
- `exit_price`: Precio de salida
- `exit_reason`: TAKE_PROFIT, STOP_LOSS, o CLOSE_EOD
- `target`: Precio objetivo (+5 puntos)
- `stop`: Precio de stop (-5 puntos)
- `pnl_points`: P&L en puntos
- `pnl_usd`: P&L en dólares (1 punto ES = $50 USD)
- `pnl_percent`: P&L en porcentaje
- `creek_price`: Precio del nivel creek
- `vwap_at_entry`: VWAP al momento del primer TOP (cuadradito naranja)

### Estrategia 1: Creek Crossover Above VWAP

**Condiciones de Entrada (TODAS deben cumplirse):**
1. Creek price > VWAP (evaluado en momento del primer TOP)
2. First TOP price (cuadradito naranja) > VWAP (evaluado en momento del primer TOP)

**Punto de Entrada:**
- Master candle close (si existe master candle)
- Breakout candle close (si no hay master candle)

**Gestión de Riesgo:**
- Target: +5 puntos desde entrada
- Stop Loss: -5 puntos desde entrada
- Exit EOD: Cierre al final del día si posición abierta

**Nota Importante:**
- Las condiciones se evalúan en el momento del **primer TOP** (cuando se forma el cuadradito naranja), NO en el momento del breakout
- Solo se dibujan y operan clusters que cumplen ambas condiciones
- Clusters que no cumplen son filtrados del gráfico y de las entradas

### Scripts que Generan Estos Archivos

```bash
python strat_OM/strat_1_crossover_creek.py 2023_03_13 2.0
```

---

## 📁 tablas_html/

**Propósito**: Almacena los reportes HTML de las estrategias de trading (visualización web de resultados).

### Archivos Generados

```
trading_report_strat1_crossover_{fecha}.html
```

**Ejemplo:**
- `trading_report_strat1_crossover_2023_03_13.html`

**Contenido del Reporte:**
- **Performance Summary**: Total trades, win rate, P&L total (puntos y USD)
- **Exit Reasons**: Conteo de take profit, stop loss, y close EOD
- **Trade Details Table**: Tabla completa con todos los trades ejecutados

**Características:**
- Diseño responsive con max-width 1800px
- Márgenes ajustados (10px body, 20px tabla)
- Color coding:
  - Verde: Trades ganadores / Take Profit
  - Rojo: Trades perdedores / Stop Loss
  - Gris: Close EOD
- Tags visuales para exit reasons
- Valores en USD además de puntos

### Scripts que Generan Estos Archivos

```bash
python strat_OM/strat_1_crossover_creek.py 2023_03_13 2.0
```

El reporte se abre automáticamente en el navegador web al ejecutar la estrategia.

---

## Flujo de Trabajo Completo

```bash
# 1. Extraer datos de un día específico
python utils/clean_data_one_day_data.py

# 2. Ejecutar análisis completo (fractales + creek + gráfico)
python main.py

# Archivos generados:
# - outputs/fractal_tops_and_bottoms/fractals_es_1min_data_2023_03_02_zigzag_0.1.csv
# - outputs/fractal_tops_and_bottoms/true_tops_creek_perdices_2023_03_02_tol_2.0.csv
# - charts/ES_1min_2023_03_02.html

# 3. Ejecutar estrategia de trading
python strat_OM/strat_1_crossover_creek.py 2023_03_02 2.0

# Archivos generados:
# - outputs/tracking_records/trading_record_strat1_crossover_2023_03_02.csv
# - outputs/tablas_html/trading_report_strat1_crossover_2023_03_02.html
# - charts/ES_1min_2023_03_02.html (actualizado con trades)
```

---

## Configuración de Parámetros

En `main.py`:

```python
CHANGE_PCT = 0.10           # Sensibilidad zigzag (0.10% = sensible)
TOLERANCE_PRICE = 2.0       # Tolerancia clustering creek (±2.0 puntos)
MASTER_UPPER_TAIL_PCT = 20  # Mecha superior máxima master candles (20%)
VOL_MULTIPL = 1.5           # Umbral volumen (1.5x promedio)
VOL_PERCENTILE = 70         # Filtro posición (percentil 70)
```

En `strat_1_crossover_creek.py`:

```python
TARGET_POINTS = 5.0         # Objetivo de ganancia en puntos
STOP_POINTS = 5.0           # Stop loss en puntos
POINT_VALUE = 50.0          # 1 punto ES = $50 USD
```

---

## Dependencias entre Scripts

### Escritores (Output)
- `quant_stat/find_tops_and_bottoms.py` → fractals CSV
- `quant_stat/find_true_tops.py` → creek perdices CSV
- `quant_stat/find_true_mastercandle.py` → actualiza creek CSV
- `quant_stat/find_true_volume.py` → actualiza creek CSV
- `strat_OM/strat_1_crossover_creek.py` → trading CSV + HTML

### Lectores (Input)
- `quant_stat/find_true_tops.py` → lee fractals CSV
- `quant_stat/find_true_mastercandle.py` → lee creek CSV
- `quant_stat/find_true_volume.py` → lee creek CSV
- `strat_OM/strat_1_crossover_creek.py` → lee creek CSV
- `plot_minute_data.py` → lee fractals y creek CSV (auto-detect)

---

## Notas Importantes

- Los archivos se crean automáticamente por el pipeline de análisis
- Cada ejecución sobrescribe resultados previos para misma fecha/parámetros
- Fractals CSV es requerido antes de creek perdices
- Creek CSV se enriquece con datos de master candle y volumen
- Trading CSV se genera cuando la estrategia ejecuta trades
- HTML se genera automáticamente con cada ejecución de estrategia
- Todos los timestamps usan zona horaria UTC
- 1 punto ES = $50 USD (usado en cálculos de P&L)

---

## Carpetas Relacionadas

- `data/daily_subdata/` - Datos de velas diarias (fuente)
- `charts/` - Visualizaciones HTML generadas
- `strat_OM/` - Código de estrategias de trading

---

**Creado**: Octubre 2025
**Última Actualización**: Octubre 2025
