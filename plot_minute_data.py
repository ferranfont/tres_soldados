import os
import webbrowser
import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import plotly.express as px
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from config import CHART_WIDTH, CHART_HEIGHT, CHART_TEMPLATE, get_chart_path, DATA_DIR, SYMBOL

MINUTE_DATA_FILE = 'es_1min_data_2015_2025.csv' 



def load_fractals_csv(fractal_csv_path):
    """
    Load fractals from CSV file
    Returns DataFrame with fractals or None if file doesn't exist
    """
    if not os.path.exists(fractal_csv_path):
        print(f"No fractals file found: {fractal_csv_path}")
        return None

    try:
        df_fractals = pd.read_csv(fractal_csv_path)
        df_fractals['timestamp'] = pd.to_datetime(df_fractals['timestamp'])
        print(f"Loaded {len(df_fractals)} fractals from {os.path.basename(fractal_csv_path)}")
        return df_fractals
    except Exception as e:
        print(f"Error loading fractals: {e}")
        return None


def plot_minute_data(symbol, timeframe, df, fractals_csv=None):
    """
    Función especializada para graficar datos de minutos con etiquetas de hora en el eje X

    Args:
        symbol: Trading symbol (e.g., 'ES')
        timeframe: Timeframe string for chart title
        df: DataFrame with OHLC data
        fractals_csv: Optional path to fractals CSV file. If None, will try to auto-detect.
    """
    html_path = get_chart_path(symbol, timeframe)

    df = df.rename(columns=str.lower)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')

    # Load fractals if CSV provided or try to auto-detect
    df_fractals = None
    if fractals_csv:
        df_fractals = load_fractals_csv(fractals_csv)
    else:
        # Try to auto-detect fractals CSV based on timeframe
        outputs_dir = 'outputs'
        if os.path.exists(outputs_dir):
            # Extract date from timeframe (e.g., '1min_2023_03_01' -> '2023_03_01')
            date_part = timeframe.replace('1min_', '')
            fractal_pattern = f'fractals_es_1min_data_{date_part}_zigzag_*.csv'
            import glob
            matching_files = glob.glob(os.path.join(outputs_dir, fractal_pattern))
            if matching_files:
                # Use most recent file if multiple matches
                fractals_csv = max(matching_files, key=os.path.getctime)
                df_fractals = load_fractals_csv(fractals_csv)

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.80, 0.20],
        vertical_spacing=0.03,
    )

    # Gráfico de velas (candlestick) con outline negro semi-transparente
    fig.add_trace(go.Candlestick(
        x=df['date'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        increasing_line_color='rgba(0,0,0,0.8)',     # Outline negro con alpha 0.8 para velas alcistas
        decreasing_line_color='rgba(0,0,0,0.8)',     # Outline negro con alpha 0.8 para velas bajistas
        increasing_fillcolor='rgba(0,255,0,0.8)',    # Relleno verde lima con alpha 0.8
        decreasing_fillcolor='rgba(255,0,0,0.8)',    # Relleno rojo con alpha 0.8
        line=dict(width=1),
        name='OHLC',
        opacity=0.8
    ), row=1, col=1)

    # Plot VWAP if present in dataframe
    if 'ema' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['ema'],
            mode='lines',
            line=dict(color='rgba(255,0,255,0.6)', width=1),
            name=f'VWAP',
            showlegend=True
        ), row=1, col=1)

    # Plot fractals as blue dots and line
    if df_fractals is not None and len(df_fractals) > 0:
        # Plot blue line connecting all fractals
        fig.add_trace(go.Scatter(
            x=df_fractals['timestamp'],
            y=df_fractals['price'],
            mode='lines',
            line=dict(
                color='rgba(0,0,255,0.5)',
                width=1
            ),
            name='Fractal Line',
            hoverinfo='skip',
            showlegend=False
        ), row=1, col=1)

        # Separate tops and bottoms
        tops = df_fractals[df_fractals['type'] == 'TOP']
        bottoms = df_fractals[df_fractals['type'] == 'BOTTOM']

        # Plot TOPS as blue dots on highs
        if len(tops) > 0:
            fig.add_trace(go.Scatter(
                x=tops['timestamp'],
                y=tops['price'],
                mode='markers',
                marker=dict(
                    color='blue',
                    size=6,
                    symbol='circle'
                ),
                name='Top Fractals',
                customdata=tops['swing_size'],
                hovertemplate='%{customdata}<br>Time: %{x}<br>Price: $%{y:.2f}<extra></extra>',
                showlegend=False
            ), row=1, col=1)

        # Plot BOTTOMS as blue dots on lows
        if len(bottoms) > 0:
            fig.add_trace(go.Scatter(
                x=bottoms['timestamp'],
                y=bottoms['price'],
                mode='markers',
                marker=dict(
                    color='blue',
                    size=6,
                    symbol='circle'
                ),
                name='Bottom Fractals',
                customdata=bottoms['swing_size'],
                hovertemplate='%{customdata}<br>Time: %{x}<br>Price: $%{y:.2f}<extra></extra>',
                showlegend=False
            ), row=1, col=1)

        print(f"Plotted {len(df_fractals)} fractals ({len(tops)} tops, {len(bottoms)} bottoms)")

    # Barras de volumen
    fig.add_trace(go.Bar(
        x=df['date'],
        y=df['volume'],
        marker_color='royalblue',
        marker_line_color='blue',
        marker_line_width=0.4,
        opacity=0.95,
        name='Volumen'
    ), row=2, col=1)

    fig.update_layout(
        dragmode='pan',
        title=f'{symbol}_{timeframe} - tres_soldados',
        width=CHART_WIDTH,
        height=CHART_HEIGHT,
        margin=dict(l=20, r=20, t=40, b=20),
        font=dict(size=12, color="black"),
        plot_bgcolor='white',  # Light grey with alpha 0.1
        paper_bgcolor='white',
        showlegend=False,
        template='plotly_white',
        xaxis=dict(
            type='date',
            tickformat="%H:%M",  # Solo mostrar hora:minuto
            tickangle=0,
            showgrid=False,  # Sin grid vertical
            linecolor='black',
            linewidth=1,
            range=[df['date'].min(), df['date'].max()],
            # Mostrar ticks cada hora
            dtick=3600000,  # 1 hora en milisegundos
            rangeslider=dict(visible=False)  # Ocultar el range slider
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(128,128,128,0.2)',  # Gris muy pálido, casi transparente
            gridwidth=1,
            linecolor='black',
            linewidth=1
        ),
        xaxis2=dict(
            type='date',
            tickformat="%H:%M",  # Solo mostrar hora:minuto
            tickangle=45,
            showgrid=False,  # Sin grid vertical
            linecolor='black',
            linewidth=1,
            range=[df['date'].min(), df['date'].max()],
            # Mostrar ticks cada hora
            dtick=3600000  # 1 hora en milisegundos
        ),
        yaxis2=dict(
            showgrid=True,
            gridcolor='rgba(128,128,128,0.1)',  # Gris muy pálido, casi transparente
            gridwidth=1,
            linecolor='black',
            linewidth=1
        ),
    )

    fig.write_html(html_path, config={
        "scrollZoom": True,
        "displayModeBar": True,  # Mostrar barra de navegación
        "staticPlot": False,
        "toImageButtonOptions": {
            "format": "png",
            "filename": "chart",
            "height": 500,
            "width": 700,
            "scale": 1
        }
    })
    print(f"✅ Gráfico de minutos guardado como HTML: '{html_path}'")

    webbrowser.open('file://' + os.path.realpath(html_path))


if __name__ == "__main__":
    # Configuración para ejecución directa
    TARGET_DATE = '2023-03-01'  # Cambiar esta fecha según necesidad
    symbol = SYMBOL

    # ====================================================
    # 📥 CARGA DE DATOS
    # ====================================================
    directorio = str(DATA_DIR)
    nombre_fichero = MINUTE_DATA_FILE
    ruta_completa = os.path.join(directorio, nombre_fichero)

    print(f"\n======================== 🔍 Extrayendo datos del {TARGET_DATE} ===========================")
    df = pd.read_csv(ruta_completa)
    print('Fichero:', ruta_completa, 'importado')
    print(f"Características del Fichero Base: {df.shape}")

    # Normalizar columnas a minúsculas y renombrar 'volumen' a 'volume'
    df.columns = [col.strip().lower() for col in df.columns]
    df = df.rename(columns={'volumen': 'volume'})

    # Asegurar formato datetime con zona UTC
    df['date'] = pd.to_datetime(df['date'], utc=True)

    # Filtrar datos solo para la fecha objetivo
    target_date_start = pd.to_datetime(TARGET_DATE, utc=True)
    target_date_end = target_date_start + pd.Timedelta(days=1)

    df_filtered = df[(df['date'] >= target_date_start) & (df['date'] < target_date_end)].copy()

    print(f"Datos encontrados para {TARGET_DATE}: {len(df_filtered)} registros")

    if len(df_filtered) > 0:
        # Mostrar estadísticas básicas
        print("\n📈 Estadísticas del día:")
        print(f"Open: {df_filtered['open'].iloc[0]:.2f}")
        print(f"High: {df_filtered['high'].max():.2f}")
        print(f"Low: {df_filtered['low'].min():.2f}")
        print(f"Close: {df_filtered['close'].iloc[-1]:.2f}")
        print(f"Volume total: {df_filtered['volume'].sum():,.0f}")

        # Crear gráfico con los datos del día específico
        print(f"\n📊 Generando gráfico para {TARGET_DATE}...")
        timeframe = f'1min_{TARGET_DATE}'
        plot_minute_data(symbol, timeframe, df_filtered)

    else:
        print(f"❌ No se encontraron datos para la fecha {TARGET_DATE}")
        print("Verifique que la fecha esté disponible en el archivo de datos.")