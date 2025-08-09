pip install -r requirements.txt


Script que busca la estrategia de los 3 soldados según:

https://www.asktraders.com/learn-to-trade/technical-analysis/three-white-soldiers-candlestick-pattern/



Detección de Whipsaws (Latigazos) en Tendencias
Este proyecto contiene herramientas para detectar latigazos (whipsaws) al final de tendencias marcadas en datos de mercado tipo OHLCV (Open, High, Low, Close, Volume).

Se incluye:

Cálculo de ATR (Average True Range)

Función detect_whipsaw_global_view para detectar patrones completos de whipsaw

Preparado para integrarse en otros scripts (ej: download_near_tick_data.py)

1. Estructura del DataFrame
El algoritmo espera un pandas.DataFrame con las siguientes columnas:

Columna	Tipo	Descripción
date	datetime	Fecha y hora de la barra/candle
open	float	Precio de apertura
high	float	Precio máximo
low	float	Precio mínimo
close	float	Precio de cierre
volume	float/int	Volumen negociado

El índice puede ser DatetimeIndex o una columna date.

2. Funciones principales
calculate_atr(df, n_atr=14)
Calcula el Average True Range usando el método clásico de Welles Wilder.
Devuelve una pd.Series con el ATR.

Parámetros:

df: DataFrame con columnas high, low, close

n_atr: periodo de ATR (por defecto 14)

detect_whipsaw_global_view(...)
Detecta patrones whipsaw tras tendencias alcistas o bajistas.

Lógica simplificada:

Detecta tendencias mediante regresión lineal (slope) sobre n_trend velas previas.

Confirma que la pendiente (slope) supere slope_min (normalizada por precio medio si use_slope_norm=True).

Busca un movimiento contrario fuerte (>= k1_drop * ATR) en una ventana de w velas.

Confirma un rebote posterior en la dirección original (>= k2_bounce * ATR).

Marca las señales:

whip_after_up: whipsaw tras tendencia alcista

whip_after_down: whipsaw tras tendencia bajista

Parámetros más relevantes:

Parámetro	Descripción
n_trend	Nº de velas usadas para calcular la tendencia
slope_min	Pendiente mínima para considerar tendencia
n_atr	Periodo ATR
w	Ventana máxima para buscar el patrón
k1_drop	Múltiplo de ATR para el movimiento inicial contrario
k2_bounce	Múltiplo de ATR para el rebote posterior
min_gap	Nº mínimo de velas entre señales
use_slope_norm	Si normalizar la pendiente por el precio medio

3. Ejemplo de uso
python
Copiar
Editar
import pandas as pd
from find_whipsaw import detect_whipsaw_global_view

# Ejemplo de DataFrame (puede venir de tu CSV o feed de mercado)
df = pd.DataFrame({
    "date": pd.date_range("2025-07-25 08:00", periods=100, freq="1T"),
    "open": [100 + i*0.01 for i in range(100)],
    "high": [100.2 + i*0.01 for i in range(100)],
    "low": [99.8 + i*0.01 for i in range(100)],
    "close": [100 + i*0.01 for i in range(100)],
    "volume": [1000 for _ in range(100)]
})

# Asegurar índice
df = df.set_index("date")

# Detectar señales
df_with_signals = detect_whipsaw_global_view(df)

# Mostrar señales detectadas
print(df_with_signals[df_with_signals['whip_after_up']])
print(df_with_signals[df_with_signals['whip_after_down']])
4. Integración con download_near_tick_data.py
Si ya tienes un script que lee datos de NinjaTrader u otra fuente:

python
Copiar
Editar
from find_whipsaw import detect_whipsaw_global_view

# df es tu DataFrame OHLCV
df_with_signals = detect_whipsaw_global_view(df)

# Guardar o usar para graficar
df_with_signals.to_csv("ohlcv_with_signals.csv")
5. Visualización de señales (opcional)
Puedes usar Plotly para trazar el close y marcar las señales con triángulos:

python
Copiar
Editar
import plotly.graph_objs as go

def plot_whipsaw(df):
    fig = go.Figure()

    # Línea Close
    fig.add_trace(go.Scatter(
        x=df.index, y=df['close'],
        mode='lines', name='Close', line=dict(color='royalblue', width=2)
    ))

    # Señales alcistas
    up_signals = df[df['whip_after_up']]
    fig.add_trace(go.Scatter(
        x=up_signals.index, y=up_signals['close'],
        mode='markers', name='Whip After Up',
        marker=dict(symbol='triangle-down', size=12, color='red')
    ))

    # Señales bajistas
    down_signals = df[df['whip_after_down']]
    fig.add_trace(go.Scatter(
        x=down_signals.index, y=down_signals['close'],
        mode='markers', name='Whip After Down',
        marker=dict(symbol='triangle-up', size=12, color='green')
    ))

    fig.show()

# Uso:
# plot_whipsaw(df_with_signals)
6. Notas finales
Este algoritmo está pensado para visión global: busca patrones amplios, no micro-movimientos.

Los parámetros (n_trend, k1_drop, k2_bounce, etc.) son ajustables según el activo y timeframe.

===========================================================================================================================

etección de patrones y gráficos (Close + Volumen + Señales)
Este proyecto carga datos OHLCV ya formateados, calcula indicadores (ATR y ATR_fast), detecta patrones (Three White Soldiers y “serpiente” de mechas opuestas) y grafica el close con volumen y marcadores de señales.

1) Estructura de archivos
arduino
Copiar
Editar
tres_soldados/
├─ main.py
├─ chart_volume.py                # contiene plot_close_and_volume()
├─ quant_stat/
│  ├─ find_three_soldiers.py     # contiene find_three_soldiers()
│  └─ serpiente.py               # contiene detectar_mechas_opuestas()
└─ DATA/
   └─ ES_near_tick_data_27_jul_2025.csv
2) Requisitos
bash
Copiar
Editar
pip install pandas ta plotly
ta se usa para ATR/ATR_fast, plotly para gráficos.
Si usas funciones adicionales, instala también numpy, etc.

3) Formato de los datos
CSV con columnas (mínimo):

date (datetime, ISO recomendado)

open, high, low, close (float)

volume (float/int)

Ejemplo:

csv
Copiar
Editar
date,open,high,low,close,volume
2025-07-25 22:55:00,6427.00,6427.00,6426.25,6426.25,308
2025-07-25 22:56:00,6426.25,6427.00,6426.00,6426.75,312
4) main.py — Flujo
python
Copiar
Editar
import pandas as pd
import os
import ta
from chart_volume import plot_close_and_volume
from quant_stat.serpiente import detectar_mechas_opuestas
from quant_stat.find_three_soldiers import find_three_soldiers

symbol = 'ES'
timeframe = '15min'

# 1) Carga de datos
directorio = '../DATA'
nombre_fichero = 'ES_near_tick_data_27_jul_2025.csv'
ruta_completa = os.path.join(directorio, nombre_fichero)

print("\n====== 🔍 Cargando DataFrame Formateado ========")
df = pd.read_csv(ruta_completa, parse_dates=['date'])
df = df.set_index('date')
df = df[df.index.dayofweek < 5]  # filtra fines de semana

print(f"✅ Fichero importado: {ruta_completa}")
print(f"📊 Dimensiones: {df.shape}")

# 2) Señales — Three White Soldiers
df = find_three_soldiers(df)

# 3) Rango de estudio (opcional)
if 'date' not in df.columns:
    df = df.reset_index()
df = df.set_index('date').loc['2020-06-30':'2020-08-22'].reset_index()

# 4) Mostrar señales en el rango
print(df[df['tres_soldados'] == True])
print('número de señales en el rango: ', len(df[df['tres_soldados'] == True]), '\n')

# 5) Indicadores (ATR y ATR_fast)
atr = ta.volatility.AverageTrueRange(high=df['high'], low=df['low'], close=df['close'], window=14)
atr_fast = ta.volatility.AverageTrueRange(high=df['high'], low=df['low'], close=df['close'], window=5)
df['atr'] = atr.average_true_range()
df['atr_fast'] = atr_fast.average_true_range()
print(df.head(30))

# 6) Señal “Serpiente” (mechas opuestas)
serpiente_raw = detectar_mechas_opuestas(df, n=2, ratio_mecha=2.5, f=1.5)
serpiente = pd.DataFrame(serpiente_raw, columns=[
    'golpe', 'fecha_golpe', 'close_golpe',
    'latigo', 'fecha_latigo', 'close_latigo',
    'distancia_velas'
])
print(serpiente.head())

# 7) Gráfico Close + Volumen + Señales
plot_close_and_volume(symbol, timeframe, df, serpiente)
Qué hace cada bloque
Carga: lee el CSV y lo indexa por date.

find_three_soldiers: añade columna booleana tres_soldados.

Rango: recorta por fechas para enfocarte en un periodo.

ATR: calcula atr (14) y atr_fast (5) para análisis adicional.

Serpiente: detecta patrón de mechas opuestas y lo devuelve como tabla.

Gráfico: muestra línea de close con volumen y marca eventos de “serpiente”.

5) Función — find_three_soldiers(df)
python
Copiar
Editar
def find_three_soldiers(df):
    """
    Detecta el patrón 'Three White Soldiers' en un DataFrame OHLCV.
    Añade 'tres_soldados' = True cuando:
      - 3 velas alcistas consecutivas (cierres > aperturas)
      - Cuerpo dominante: (close-open) > 70% del rango (high-low)
      - La apertura de cada vela está dentro del cuerpo de la anterior
      - Cierres crecientes (c1 < c2 < c3)
    """
    df = df.copy()
    df['tres_soldados'] = False

    for i in range(2, len(df)):
        o1, c1, h1, l1 = df.iloc[i-2][['open', 'close', 'high', 'low']]
        o2, c2, h2, l2 = df.iloc[i-1][['open', 'close', 'high', 'low']]
        o3, c3, h3, l3 = df.iloc[i][['open', 'close', 'high', 'low']]

        long1 = c1 > o1 and (c1 - o1) > 0.7 * (h1 - l1)
        long2 = c2 > o2 and (c2 - o2) > 0.7 * (h2 - l2)
        long3 = c3 > o3 and (c3 - o3) > 0.7 * (h3 - l3)

        inside1 = o2 > o1 and o2 < c1
        inside2 = o3 > o2 and o3 < c2

        higher1 = c2 > c1
        higher2 = c3 > c2

        if long1 and long2 and long3 and inside1 and inside2 and higher1 and higher2:
            df.iloc[i, df.columns.get_loc('tres_soldados')] = True

    return df
Notas de uso
Requiere columnas: open, high, low, close (no usa volume).

Funciona tanto si date es índice como si es columna (en main.py ya se gestiona).

6) Gráfico — plot_close_and_volume()
chart_volume.plot_close_and_volume(symbol, timeframe, df, serpiente) debe:

Dibujar línea continua de close (sin range slider).

Mostrar volumen en subplot inferior (si lo implementaste).

(Opcional) Marcar eventos de “serpiente” con puntos/triángulos usando serpiente.

Si aún no lo hace, ajusta la función para añadir un go.Scatter con mode='markers' y las fechas de serpiente['fecha_golpe'] / serpiente['fecha_latigo'].

7) Ejecución
Desde la carpeta del proyecto:

bash
Copiar
Editar
python main.py
Verás por consola:

confirmación de carga + dimensiones,

listado de señales tres_soldados en el rango,

primeras filas con atr y atr_fast,

primeras filas de la tabla “serpiente”.

Y se abrirá (o guardará) el gráfico en tu navegador, según cómo implementaste plot_close_and_volume().

8) Problemas comunes
ParserError: date: asegúrate de parse_dates=['date'] y formato válido.

KeyError: 'open': revisa que el CSV tenga las columnas esperadas.

Huecos de mercado: si usaste resample en la preparación, filtra fines de semana o elimina filas sin datos (df = df[df['volume'] > 0]).

Tipos: si venían comas decimales (,), conviértelas antes a float.

9) Siguientes pasos (opcional)
Integrar detección de whipsaw (latigazos) con tu módulo find_whipsaw.py.

Añadir guardado de resultados (df.to_csv('salida.csv')).

Parametrizar fechas y fichero por CLI (argparse).