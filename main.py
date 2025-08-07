# main.py
import pandas as pd
import os
from chart_volume import plot_close_and_volume
from strat_OM.find_three_soldiers import find_three_soldiers


symbol = 'ES'

# ====================================================
# 📥 CARGA DE DATOS
# ====================================================
directorio = '../DATA'
nombre_fichero = 'export_es_2015_formatted.csv'        # vela diaria
#nombre_fichero = 'ES_2015_2024_5min_timeframe.csv'
ruta_completa = os.path.join(directorio, nombre_fichero)

print("\n======================== 🔍 df  ===========================")
df = pd.read_csv(ruta_completa)
print('Fichero:', ruta_completa, 'importado')
print(f"Características del Fichero Base: {df.shape}")

# Normalizar columnas a minúsculas y renombrar 'volumen' a 'volume'
df.columns = [col.strip().lower() for col in df.columns]
df = df.rename(columns={'volumen': 'volume'})

# Asegurar formato datetime con zona UTC
df['date'] = pd.to_datetime(df['date'], utc=True)
df = df.set_index('date')
#df = df.loc['2021']



# 🔁 Resample a velas diarias
df = df.resample('1D').agg({
    'open': 'first',
    'high': 'max',
    'low': 'min',
    'close': 'last',
    'volume': 'sum'
}).dropna()


# Reset index para usar 'date' como columna
df = df.reset_index()




# ====================================================
# 🔍 QUANT FIND THREE SOLDIERS
# ====================================================
df = find_three_soldiers(df)
print(df.head())
print(df.loc[df['three_soldiers'] == True])
print ('número de señales encontradas:', len(df.loc[df['three_soldiers'] == True]))

# ====================================================
# 📊 CARGA DE DATOS
# ====================================================
# Ejecutar gráfico


df.loc['2020-04-30':'2020-08-22']


timeframe = '1D'
plot_close_and_volume(symbol, timeframe, df)
