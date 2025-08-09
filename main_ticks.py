# FILE: main_ticks.py
import pandas as pd
import numpy as np
import os

from quant_stat.find_whipsaw import detect_trend_end_whipsaw
from chart_ticks import plot_high_low_with_whipsaw, plot_close_line

# ==== PARÁMETROS FINALES WHIPSAW (optimizados) ====
WHIPSAW_PARAMS = dict(
    n_trend=30,                        # Nº mínimo de velas para considerar una tendencia antes del latigazo
    slope_min = 1.9e-05,   # más laxo, más señales     #2.6337448559670783e-05,  # Pendiente mínima (normalizada si use_slope_norm=True) para aceptar que hubo tendencia
    n_atr=14,                          # Periodo para cálculo de ATR (volatilidad)
    w=40,                              # Ventana (en velas) para buscar el rebote después de la caída/subida
    k1_drop=0.75,                      # Múltiplo de ATR para definir la caída mínima tras una tendencia alcista (whip_after_up)
    k2_bounce=0.8,                     # Múltiplo de ATR para definir el rebote mínimo tras la caída (whip_after_up) o viceversa
    min_gap=100,                        # Nº mínimo de velas entre dos señales para evitar racimos
    use_slope_norm=True                # True = pendiente normalizada por el precio medio (mejor para comparar distintos activos)
)

# ==== 1) Cargar CSV ====
directorio = '../DATA'
nombre_fichero = 'ES_near_tick_data_27_jul_2025.csv'
ruta_completa = os.path.join(directorio, nombre_fichero)

df_raw = pd.read_csv(ruta_completa, sep=';')

# helper: coma->punto y a float
def _to_float(s):
    return (s.astype(str).str.replace(',', '.', regex=False)
            .str.replace(' ', '', regex=False)
            .replace({'': np.nan}).astype(float))

def preparar_df_simple(df_crudo: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza columnas y convierte a formato numérico.
    Devuelve DataFrame con índice datetime ordenado.
    """
    df = df_crudo.iloc[:, :6].copy()
    df.columns = ['date', 'open', 'high', 'low', 'close', 'volume']
    df['date'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce')
    for c in ['open','high','low','close','volume']:
        df[c] = _to_float(df[c])
    return df.dropna(subset=['date','open','high','low','close']).set_index('date').sort_index()



df = preparar_df_simple(df_raw)   # índice = date


# ===== 🔁 Resample por número de ticks (N filas por vela) =====
N = 50  # <- ajusta a tu gusto

dfr = df.reset_index().copy()      # ahora 'date' es columna
dfr['block'] = np.floor(np.arange(len(dfr)) / N)

df_resampled = (dfr.groupby('block', as_index=False)
                  .agg({
                      'date':   'first',
                      'open':   'first',
                      'high':   'max',
                      'low':    'min',
                      'close':  'last',
                      'volume': 'sum'
                  }))

df_resampled = df_resampled.drop(columns='block').set_index('date').sort_index()

# Reemplaza df por el agrupado para lo que sigue
df = df_resampled
# ==============================================================



df_res = df.reset_index()         # columnas: date, open, high, low, close, volume

# ==== 2) Detectar whipsaw con parámetros fijos ====
df_res = detect_trend_end_whipsaw(df_res.copy(), **WHIPSAW_PARAMS)

# ==== 3) Resultados ====
cuenta = df_res[['whip_after_up','whip_after_down']].sum().to_dict()
print("📊 Señales detectadas:", cuenta)
print("⚙ Parámetros aplicados:", WHIPSAW_PARAMS)

# Mostrar lista de señales con fecha y precio
print("\n📅 Lista de señales:")
up_signals = df_res[df_res['whip_after_up'] == 1][['date', 'close']]
down_signals = df_res[df_res['whip_after_down'] == 1][['date', 'close']]

if not up_signals.empty:
    print("\n--- Whipsaw después de tendencia alcista ---")
    print(up_signals.to_string(index=False))

if not down_signals.empty:
    print("\n--- Whipsaw después de tendencia bajista ---")
    print(down_signals.to_string(index=False))

# ==== 4) Guardar resultados completos ====
out_csv = "outputs/es_whipsaw_full.csv"
df_res.to_csv(out_csv, index=False)
print(f"\n💾 Guardado: {out_csv}")

# ==== 5) Gráficos ====
plot_high_low_with_whipsaw(df_res, symbol="ES", timeframe="1min")
#plot_close_line(df, symbol="ES", timeframe="1min")
