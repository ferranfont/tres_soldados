def find_three_soldiers(df):
    """
    Detecta el patrón 'Three White Soldiers' en un DataFrame OHLCV.
    Añade una columna 'three_soldiers' con True si el patrón se detecta, False en caso contrario.
    """
    df = df.copy()
    df['three_soldiers'] = False

    for i in range(2, len(df)):
        o1, c1, h1, l1 = df.loc[i-2, ['open', 'close', 'high', 'low']]
        o2, c2, h2, l2 = df.loc[i-1, ['open', 'close', 'high', 'low']]
        o3, c3, h3, l3 = df.loc[i,   ['open', 'close', 'high', 'low']]

        # Condiciones para que cada vela sea de cuerpo dominante (mínima sombra)
        long1 = c1 > o1 and (c1 - o1) > 0.7 * (h1 - l1)
        long2 = c2 > o2 and (c2 - o2) > 0.7 * (h2 - l2)
        long3 = c3 > o3 and (c3 - o3) > 0.7 * (h3 - l3)

        # La apertura de la vela siguiente debe estar dentro del cuerpo de la anterior
        inside1 = o2 > o1 and o2 < c1
        inside2 = o3 > o2 and o3 < c2

        # Cierres consecutivos más altos
        higher1 = c2 > c1
        higher2 = c3 > c2

        if long1 and long2 and long3 and inside1 and inside2 and higher1 and higher2:
            df.loc[i, 'three_soldiers'] = True

    return df
