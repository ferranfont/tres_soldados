# main.py
import pandas as pd
import os
import ta
from chart_volume import plot_close_and_volume
from quant_stat.serpiente import detectar_mechas_opuestas
from quant_stat.find_three_soldiers import find_three_soldiers

symbol = 'ES'
timeframe = '15min'

# ====================================================
# 📥 CARGA DE DATOS YA FORMATEADOS
# ====================================================
directorio = '../DATA'
nombre_fichero = 'export_es_SOLO_2020_formatted_15_min.csv'
ruta_completa = os.path.join(directorio, nombre_fichero)

print("\n====== 🔍 Cargando DataFrame Formateado ========")
df = pd.read_csv(ruta_completa, parse_dates=['date'])
df = df.set_index('date')  # opcional, si prefieres trabajar con índice temporal
#df = df[df['volume'] > 0]  # elimina los huecos que genera el resample sin datos en el mercado
df = df[df.index.dayofweek < 5]  # 0 = lunes, 6 = domingo, limina los huecos que genera el resample sin datos en el mercado

print(f"✅ Fichero importado: {ruta_completa}")
print(f"📊 Dimensiones: {df.shape}")

# ====================================================
# 🔍 DETECCIÓN DE SEÑALES
# ====================================================

# --- 1. Aplicar detección sobre TODO el DataFrame ---
df = find_three_soldiers(df)

# --- 2. Filtrar solo lo que deseas ver ---
# Asegurar que 'date' esté como columna primero
if 'date' not in df.columns:
    df = df.reset_index()

# Ahora puedes recortar por fechas con .loc
df = df.set_index('date').loc['2020-06-30':'2020-08-22'].reset_index()

# --- 3. Mostrar resultados SOLO en ese rango ---
print(df[df['tres_soldados'] == True])
print('número de señales en el rango: ', len(df[df['tres_soldados'] == True]),'\n')


# ====================================================
# 🔍 DETECCIÓN DE SEÑALES
# ====================================================
# Asumiendo que 'df' tiene columnas: open, high, low, close
atr = ta.volatility.AverageTrueRange(
    high=df['high'],
    low=df['low'],
    close=df['close'],
    window=14
)
df['atr'] = atr.average_true_range()
print(df.head(30))

# ====================================================
# 🔍 DETECCIÓN DE SERPIENTE
# ====================================================
serpiente_raw = detectar_mechas_opuestas(df, n=2, ratio_mecha=2.5, f=1.5)

serpiente = pd.DataFrame(serpiente_raw, columns=[
    'golpe', 'fecha_golpe', 'close_golpe',
    'latigo', 'fecha_latigo', 'close_latigo',
    'distancia_velas'
])
print(serpiente.head())

# ====================================================
# 📊 GRAFICO
# ====================================================

plot_close_and_volume(symbol, timeframe, df, serpiente)
