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


def plot_minute_data(symbol, timeframe, df, fractals_csv=None, confirmed_tops_csv=None, same_range_tops_csv=None):
    """
    Función especializada para graficar datos de minutos con etiquetas de hora en el eje X

    Args:
        symbol: Trading symbol (e.g., 'ES')
        timeframe: Timeframe string for chart title
        df: DataFrame with OHLC data
        fractals_csv: Optional path to fractals CSV file. If None, will try to auto-detect.
        confirmed_tops_csv: Optional path to confirmed TOPs CSV for horizontal lines
        same_range_tops_csv: Optional path to same range TOPs CSV for orange dots
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

    # Plot Creek Perdices (TRUE TOPs) if available
    # Look for any creek perdices CSV matching the pattern
    import glob
    creek_csvs = glob.glob('outputs/true_tops_creek_perdices_*.csv')
    true_tops_csv = creek_csvs[0] if creek_csvs else 'outputs/true_tops_creek_perdices.csv'

    if os.path.exists(true_tops_csv):
        df_true_tops = pd.read_csv(true_tops_csv)
        df_true_tops['timestamp'] = pd.to_datetime(df_true_tops['timestamp'])
        df_true_tops['last_top_timestamp'] = pd.to_datetime(df_true_tops['last_top_timestamp'])

        print(f"🎯 Plotting {len(df_true_tops)} Creek Perdices clusters...")

        # Plot orange squares (first TOP in cluster) - slightly above the actual price
        fig.add_trace(go.Scatter(
            x=df_true_tops['timestamp'],
            y=df_true_tops['price'] + 1.0,  # Offset 1.0 points above
            mode='markers',
            marker=dict(
                color='orange',
                size=7,
                symbol='square',
                line=dict(color='darkorange', width=1)
            ),
            name='Creek Start',
            hovertemplate='%{customdata[0]}<br>Time: %{x}<br>Price: $%{customdata[1]:.2f}<br>Last TOP: $%{customdata[2]:.2f}<extra></extra>',
            customdata=list(zip(df_true_tops['group'], df_true_tops['price'], df_true_tops['next_top_price'])),
            showlegend=True
        ), row=1, col=1)

        # Plot red dots (last TOP in cluster) and blue lines
        for idx, cluster in df_true_tops.iterrows():
            # Green square at last TOP - slightly above the actual price
            fig.add_trace(go.Scatter(
                x=[cluster['last_top_timestamp']],
                y=[cluster['next_top_price'] + 1.0],  # Offset 1.0 points above
                mode='markers',
                marker=dict(
                    color='green',
                    size=7,
                    symbol='square',
                    line=dict(color='darkgreen', width=1)
                ),
                name='Creek End' if idx == 0 else None,
                hovertemplate=f"{cluster['group']} End<br>Time: %{{x}}<br>Price: ${cluster['next_top_price']:.2f}<extra></extra>",
                showlegend=(idx == 0)
            ), row=1, col=1)

            # Calculate average price for creek line
            avg_price = (cluster['price'] + cluster['next_top_price']) / 2

            # Find breakout point
            candles_after = df[df['date'] > cluster['last_top_timestamp']].copy()
            breakout = candles_after[candles_after['close'] > avg_price]

            if len(breakout) > 0:
                end_time = breakout.iloc[0]['date']
                breakout_price = breakout.iloc[0]['close']
                breakout_found = True
            else:
                # Extend 2 candles beyond last TOP
                last_idx = df[df['date'] == cluster['last_top_timestamp']].index
                if len(last_idx) > 0 and last_idx[0] + 2 < len(df):
                    end_time = df.iloc[last_idx[0] + 2]['date']
                else:
                    end_time = cluster['last_top_timestamp']
                breakout_found = False

            # Find lowest low in range
            range_candles = df[(df['date'] >= cluster['timestamp']) & (df['date'] <= end_time)]
            lowest_low = range_candles['low'].min() if len(range_candles) > 0 else avg_price - 5

            # Draw gray rectangle
            fig.add_shape(
                type="rect",
                x0=cluster['timestamp'],
                x1=end_time,
                y0=lowest_low,
                y1=avg_price,
                fillcolor='lightgray',
                opacity=0.2,
                line=dict(width=0),
                row=1, col=1
            )

            # Draw blue horizontal creek line
            fig.add_trace(go.Scatter(
                x=[cluster['timestamp'], end_time],
                y=[avg_price, avg_price],
                mode='lines',
                line=dict(
                    color='blue',
                    width=1,
                    dash='solid'
                ),
                name='Creek Perdices' if idx == 0 else None,
                hovertemplate=f"{cluster['group']}<br>Creek: ${avg_price:.2f}<extra></extra>",
                showlegend=(idx == 0)
            ), row=1, col=1)

            # Draw lime triangle-up marker at breakout candle close
            if breakout_found:
                fig.add_trace(go.Scatter(
                    x=[end_time],
                    y=[breakout_price],
                    mode='markers',
                    marker=dict(
                        color='lime',
                        size=9,
                        symbol='triangle-up',
                        line=dict(color='green', width=1)
                    ),
                    name='Breakout' if idx == 0 else None,
                    hovertemplate=f"{cluster['group']} Breakout<br>Time: %{{x}}<br>Close: ${breakout_price:.2f}<extra></extra>",
                    showlegend=(idx == 0)
                ), row=1, col=1)

    # Plot same range TOPs as orange dots (legacy support)
    elif same_range_tops_csv and os.path.exists(same_range_tops_csv):
        df_same_range = pd.read_csv(same_range_tops_csv)
        df_same_range['timestamp'] = pd.to_datetime(df_same_range['timestamp'])

        print(f"🟠 Plotting {len(df_same_range)} same range TOPs as orange dots...")

        fig.add_trace(go.Scatter(
            x=df_same_range['timestamp'],
            y=df_same_range['price'],
            mode='markers',
            marker=dict(
                color='orange',
                size=15,
                symbol='circle',
                line=dict(color='darkorange', width=2)
            ),
            name='Same Range TOPs',
            hovertemplate='Same Range TOP<br>Time: %{x}<br>Price: $%{y:.2f}<br>Next: $%{customdata:.2f}<extra></extra>',
            customdata=df_same_range['next_top_price'],
            showlegend=True
        ), row=1, col=1)

    # Plot confirmed TOPs as horizontal lines
    if confirmed_tops_csv and os.path.exists(confirmed_tops_csv):
        df_confirmed = pd.read_csv(confirmed_tops_csv)
        df_confirmed['timestamp'] = pd.to_datetime(df_confirmed['timestamp'])

        print(f"📊 Plotting {len(df_confirmed)} confirmed TOPs as horizontal lines...")

        colors = ['red', 'orange', 'purple', 'brown', 'pink', 'darkred', 'crimson', 'maroon']

        for idx, top in df_confirmed.iterrows():
            # Use different color for each line
            color = colors[idx % len(colors)]

            # Find the time range for the horizontal line
            # Start from the TOP timestamp
            start_time = top['timestamp']

            # End at the next confirmed TOP or end of data
            if idx + 1 < len(df_confirmed):
                end_time = df_confirmed.iloc[idx + 1]['timestamp']
            else:
                end_time = df['date'].max()

            # Draw thick horizontal line
            fig.add_shape(
                type="line",
                x0=start_time,
                x1=end_time,
                y0=top['price'],
                y1=top['price'],
                line=dict(
                    color=color,
                    width=3,
                    dash='solid'
                ),
                row=1, col=1
            )

            # Add simple text label at the start
            fig.add_annotation(
                x=start_time,
                y=top['price'],
                text=f"#{idx+1}: ${top['price']:.2f}",
                showarrow=False,
                xanchor='left',
                yanchor='bottom',
                xshift=5,
                yshift=5,
                bgcolor='rgba(255,255,255,0.9)',
                bordercolor=color,
                borderwidth=2,
                font=dict(size=12, color=color, family='Arial Black'),
                row=1, col=1
            )

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