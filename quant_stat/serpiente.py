import pandas as pd

def detectar_mechas_opuestas(df, n=3, ratio_mecha=2.5, f=1.0):
    """
    Detecta dos velas con mechas largas en direcciones opuestas, separadas por hasta n velas.
    
    Condición adicional:
    Ambas velas deben tener un rango (high-low) mayor a f * atr.

    Parámetros:
    - df: DataFrame con columnas ['date', 'open', 'high', 'low', 'close', 'atr']
    - n: número máximo de velas intermedias permitidas
    - ratio_mecha: cuán larga debe ser la mecha respecto al cuerpo
    - f: multiplicador del ATR mínimo requerido para validar la vela

    Retorna:
    - Lista de tuplas con:
      (idx_golpe, fecha_golpe, close_golpe, idx_latigo, fecha_latigo, close_latigo, distancia)
    """
    patrones = []

    df = df.copy()
    df['body'] = abs(df['close'] - df['open'])
    df['upper_wick'] = df['high'] - df[['open', 'close']].max(axis=1)
    df['lower_wick'] = df[['open', 'close']].min(axis=1) - df['low']
    df['rango'] = df['high'] - df['low']

    # Clasificación de tipo de vela
    df['tipo'] = df.apply(lambda row: (
        'lower_wick_long' if row['lower_wick'] > ratio_mecha * row['body'] and row['lower_wick'] > row['upper_wick']
        else 'upper_wick_long' if row['upper_wick'] > ratio_mecha * row['body'] and row['upper_wick'] > row['lower_wick']
        else 'none'
    ), axis=1)

    indices = df.index.tolist()

    for i in range(len(df)):
        tipo_actual = df.loc[indices[i], 'tipo']
        if tipo_actual in ['lower_wick_long', 'upper_wick_long']:
            # Validar rango de ATR en el golpe
            if df.loc[indices[i], 'rango'] <= f * df.loc[indices[i], 'atr']:
                continue

            tipo_opuesto = 'upper_wick_long' if tipo_actual == 'lower_wick_long' else 'lower_wick_long'

            for j in range(i+1, min(i+1+n+1, len(df))):
                if df.loc[indices[j], 'tipo'] == tipo_opuesto:
                    # Validar rango de ATR en el látigo
                    if df.loc[indices[j], 'rango'] <= f * df.loc[indices[j], 'atr']:
                        continue
                    
                    distancia = j - i
                    patrones.append((
                        indices[i], df.loc[indices[i], 'date'], df.loc[indices[i], 'close'],
                        indices[j], df.loc[indices[j], 'date'], df.loc[indices[j], 'close'],
                        distancia
                    ))
                    break

    return patrones
