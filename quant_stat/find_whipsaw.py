import numpy as np
import pandas as pd
from scipy.stats import linregress

__all__ = ["detect_trend_end_whipsaw", "calculate_atr"]

def calculate_atr(df: pd.DataFrame, n_atr: int = 14) -> pd.Series:
    """ATR simple (SMA del True Range). Requiere: high, low, close."""
    high_low = df['high'] - df['low']
    high_close = (df['high'] - df['close'].shift()).abs()
    low_close = (df['low'] - df['close'].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(n_atr, min_periods=1).mean()

def detect_trend_end_whipsaw(
    df: pd.DataFrame,
    n_trend: int = 20,
    slope_min: float = 0.0002,
    n_atr: int = 14,
    w: int = 12,
    k1_drop: float = 1.25,
    k2_bounce: float = 1.10,
    min_gap: int = 12,
    use_slope_norm: bool = True,
) -> pd.DataFrame:
    """
    Detecta whipsaws al final de una tendencia.
    Añade columnas:
      - atr, slope
      - whip_after_up   (tras tendencia alcista: caída fuerte + rebote)
      - whip_after_down (tras tendencia bajista: subida fuerte + slam)
    Requiere columnas: 'date','high','low','close' (volume opcional).
    """
    data = df.copy()

    # Asegura 'date' y tipos
    if 'date' not in data.columns:
        data = data.reset_index().rename(columns={'index': 'date'})
    data['date'] = pd.to_datetime(data['date'], errors='coerce')
    for c in ['high', 'low', 'close']:
        data[c] = pd.to_numeric(data[c], errors='coerce')
    data = data.dropna(subset=['date','high','low','close']).sort_values('date').reset_index(drop=True)

    # ATR
    data['atr'] = calculate_atr(data, n_atr=n_atr)

    # Pendiente (regresión lineal) en ventana n_trend de 'close'
    slopes = np.full(len(data), np.nan, dtype=float)
    x = np.arange(n_trend, dtype=float)
    for i in range(n_trend, len(data)):
        y = data['close'].iloc[i-n_trend:i].to_numpy()
        slope, _, _, _, _ = linregress(x, y)
        if use_slope_norm:
            m = y.mean()
            slope = slope / (m if (m and np.isfinite(m)) else 1.0)
        slopes[i] = slope
    data['slope'] = slopes

    # Señales
    data['whip_after_up'] = False
    data['whip_after_down'] = False
    last_sig = -10**9

    for i in range(n_trend, len(data)-1):
        a = data.at[i, 'atr']
        s = data.at[i, 'slope']
        if not np.isfinite(a) or a <= 0 or not np.isfinite(s):
            continue

        # --- Tendencia alcista previa ---
        if s >= slope_min:
            high_ref = data.at[i, 'high']
            found_drop = None
            for j in range(i+1, min(i+w+1, len(data))):
                drop = high_ref - data.at[j, 'low']
                if drop >= k1_drop * a:
                    found_drop = j
                    break
            if found_drop is not None:
                low_val = data.at[found_drop, 'low']
                for k in range(found_drop+1, min(found_drop+w+1, len(data))):
                    rebound = data.at[k, 'high'] - low_val
                    if rebound >= k2_bounce * a and (k - last_sig) >= min_gap:
                        data.at[k, 'whip_after_up'] = True
                        last_sig = k
                        break

        # --- Tendencia bajista previa ---
        elif s <= -slope_min:
            low_ref = data.at[i, 'low']
            found_pop = None
            for j in range(i+1, min(i+w+1, len(data))):
                pop = data.at[j, 'high'] - low_ref
                if pop >= k1_drop * a:
                    found_pop = j
                    break
            if found_pop is not None:
                high_val = data.at[found_pop, 'high']
                for k in range(found_pop+1, min(found_pop+w+1, len(data))):
                    slam = high_val - data.at[k, 'low']
                    if slam >= k2_bounce * a and (k - last_sig) >= min_gap:
                        data.at[k, 'whip_after_down'] = True
                        last_sig = k
                        break

    return data
