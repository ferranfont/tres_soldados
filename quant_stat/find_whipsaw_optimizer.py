# FILE: download_near_tick_data.py
import os
import numpy as np
import pandas as pd

from quant_stat.find_whipsaw import detect_trend_end_whipsaw
from chart_ticks import plot_high_low_with_whipsaw, plot_close_line


# --- TUNER bidireccional: ajusta hasta 4–6 señales en un subset y devuelve (df_out, params) ---
def tune_whipsaw_to_target(df_in,
                           target_lo=4, target_hi=6,
                           start_params=None,
                           last_n=50000):
    """
    Ajusta parámetros para que el nº de señales caiga entre [target_lo, target_hi].
    Trabaja sobre las últimas `last_n` filas (si hay más), para acelerar.
    Devuelve: (df_tuned, params_usados)
    """
    work = df_in.tail(last_n).copy() if last_n and len(df_in) > last_n else df_in.copy()

    # Base pensada para pendiente NORMALIZADA por precio (ES ~6400)
    # OJO: si cambias use_slope_norm a False, recuerda ajustar slope_min (puntos/vela)
    p = dict(
        n_trend=20,
        slope_min=0.0002,  # muy pequeño si use_slope_norm=True
        n_atr=10,
        w=14,
        k1_drop=1.25,
        k2_bounce=1.10,
        min_gap=12,
        use_slope_norm=True,
    )
    if start_params:
        p.update(start_params)

    def run(params):
        out = detect_trend_end_whipsaw(work.copy(), **params)
        total = int(out[['whip_after_up','whip_after_down']].sum().sum())
        return out, total

    out, cnt = run(p)
    if target_lo <= cnt <= target_hi:
        return out, p

    steps = 0
    while steps < 300:
        changed = False

        if cnt > target_hi:
            # Endurecer: menos señales
            if p['k1_drop'] < 2.5:
                p['k1_drop'] = round(p['k1_drop'] + 0.10, 2); changed = True
            if cnt > target_hi and p['k2_bounce'] < 2.0:
                p['k2_bounce'] = round(p['k2_bounce'] + 0.10, 2); changed = True
            if cnt > target_hi:
                if p['use_slope_norm']:
                    p['slope_min'] = round(max(p['slope_min'] * 1.5, 1e-7), 7); changed = True
                else:
                    p['slope_min'] = round(p['slope_min'] + 0.1, 3); changed = True
            if cnt > target_hi and p['n_trend'] < 60:
                p['n_trend'] += 4; changed = True
            if cnt > target_hi and p['min_gap'] < 80:
                p['min_gap'] += 8; changed = True
            if cnt > target_hi and p['w'] > 8:
                p['w'] -= 1; changed = True

        else:
            # Aflojar: más señales (pocas o 0)
            if p['k1_drop'] > 0.8:
                p['k1_drop'] = round(p['k1_drop'] - 0.10, 2); changed = True
            if cnt < target_lo and p['k2_bounce'] > 0.8:
                p['k2_bounce'] = round(p['k2_bounce'] - 0.10, 2); changed = True
            if cnt < target_lo:
                if p['use_slope_norm']:
                    p['slope_min'] = max(p['slope_min'] / 1.5, 1e-7); changed = True
                else:
                    if p['slope_min'] > 0.1:
                        p['slope_min'] = round(p['slope_min'] * 0.8, 3); changed = True
            if cnt < target_lo and p['n_trend'] > 10:
                p['n_trend'] -= 2; changed = True
            if cnt < target_lo and p['min_gap'] > 0:
                p['min_gap'] = max(0, p['min_gap'] - 5); changed = True
            if cnt < target_lo and p['w'] < 25:
                p['w'] += 1; changed = True

        out, cnt = run(p)
        steps += 1
        if target_lo <= cnt <= target_hi:
            break
        if not changed:
            break

    return out, p


# ========= 1) Cargar CSV =========
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
    Espera columnas: (fecha, open, high, low, close, volume) en ese orden en el CSV (NinjaTrader ;).
    Devuelve DF con índice datetime y columnas OHLCV en float.
    """
    df = df_crudo.iloc[:, :6].copy()
    df.columns = ['date', 'open', 'high', 'low', 'close', 'volume']
    df['date'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce')
    for c in ['open','high','low','close','volume']:
        df[c] = _to_float(df[c])
    return (df
            .dropna(subset=['date','open','high','low','close'])
            .set_index('date')
            .sort_index())

df = preparar_df_simple(df_raw)     # índice = date
df_res = df.reset_index()           # columnas: date, open, high, low, close, volume

# ========= 2) Detectar whipsaw con auto-tuner (4–6 señales en últimas 50k) =========
df_sample, params = tune_whipsaw_to_target(
    df_res,
    target_lo=4, target_hi=6,
    start_params=dict(use_slope_norm=True, slope_min=0.0002),
    last_n=50000
)

print("Señales (muestra):", df_sample[['whip_after_up','whip_after_down']].sum().to_dict())
print("Parámetros finales:", params)

# ========= 3) Aplicar parámetros a TODO el dataframe =========
params_full = params.copy()
# (opcional) en histórico completo, espacia un poco más:
params_full['min_gap'] = max(params_full.get('min_gap', 0), 20)

df_full = df.reset_index()
df_full = detect_trend_end_whipsaw(df_full, **params_full)

print("Señales en TODO el dataset:",
      df_full[['whip_after_up','whip_after_down']].sum().to_dict())
print("Parámetros aplicados:", params_full)

# ========= 4) Guardar y graficar =========
os.makedirs("DATA", exist_ok=True)
out_csv = "DATA/es_whipsaw_full.csv"
df_full.to_csv(out_csv, index=False)
print(f"💾 Guardado: {out_csv}")

plot_high_low_with_whipsaw(df_full, symbol="ES", timeframe="1min")
plot_close_line(df, symbol="ES", timeframe="1min")
