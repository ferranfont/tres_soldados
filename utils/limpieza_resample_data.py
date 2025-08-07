import os
import pandas as pd

def preprocesar_export_es(
    entrada_csv='../DATA/export_es_2015_formatted.csv',
    salida_csv='../DATA/export_es_SOLO_2020_formatted_15_min.csv',
    timeframe='15min'
):
    """
    Preprocesa el archivo CSV original:
    - Limpieza y normalización de columnas
    - Conversión a datetime e indexado
    - Resampleo a 15 minutos
    - Filtrado por año 2020
    - Eliminación de fines de semana (sábados y domingos)
    Guarda el resultado en un CSV listo para análisis.
    """

    print("\n======================== 🔍 Iniciando preprocesado ===========================")
    print(f"📂 Archivo de entrada: {entrada_csv}")
    
    # Leer CSV original
    df = pd.read_csv(entrada_csv)
    print(f"✅ Fichero cargado. Dimensiones originales: {df.shape}")

    # Limpieza y normalización
    df.columns = [col.strip().lower() for col in df.columns]
    if 'volumen' in df.columns:
        df = df.rename(columns={'volumen': 'volume'})

    # Asegurar tipo datetime
    df['date'] = pd.to_datetime(df['date'], utc=True)
    df = df.set_index('date')

    # Resampleo
    df_resampled = df.resample(timeframe).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna().reset_index()

    # Filtrar solo el año 2020
    df_resampled = df_resampled[df_resampled['date'].dt.year == 2020]

    # Eliminar fines de semana (sábado = 5, domingo = 6)
    n_antes = len(df_resampled)
    df_resampled = df_resampled[df_resampled['date'].dt.dayofweek < 5]
    n_despues = len(df_resampled)
    n_eliminadas = n_antes - n_despues

    # Guardar archivo final
    df_resampled.to_csv(salida_csv, index=False)
    print(f"✅ Preprocesado terminado. Archivo guardado como: {salida_csv}")
    print(f"📊 Dimensiones del nuevo dataset: {df_resampled.shape}")
    print(f"🧹 Velas eliminadas por ser fines de semana: {n_eliminadas}")

    return df_resampled

# Ejecutar directamente
df = preprocesar_export_es()
