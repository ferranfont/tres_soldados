import os
import webbrowser
import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots

def plot_close_and_volume(symbol, timeframe, df, serpiente):
    html_path = f'charts/candle_vol_chart_{symbol}_{timeframe}.html'
    os.makedirs(os.path.dirname(html_path), exist_ok=True)

    df = df.rename(columns=str.lower)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')

    # ⬇️ secondary_y=True SOLO en la fila 1
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.8, 0.2],
        vertical_spacing=0.03,
        specs=[[{"secondary_y": True}],
               [{"secondary_y": False}]]
    )

    # ✅ FILA 1: Candlestick (eje izquierdo)
    fig.add_trace(go.Candlestick(
        x=df['date'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name='Candlestick',
        increasing=dict(line=dict(color='#696969', width=1), fillcolor='#00FF00'),
        decreasing=dict(line=dict(color='black', width=1), fillcolor='red')
    ), row=1, col=1, secondary_y=False)

    # 🔵 ATR y ATR fast en el EJE DERECHO de la fila 1
    if 'atr' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['atr'],
            mode='lines',
            name='ATR (14)',
            line=dict(width=2)
        ), row=1, col=1, secondary_y=True)

    if 'atr_fast' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['atr_fast'],
            mode='lines',
            name='ATR fast (5)',
            line=dict(width=1.5, dash='solid')
        ), row=1, col=1, secondary_y=True)

    # 🔶 Señales "Three Soldiers"
    if 'tres_soldados' in df.columns:
        soldiers = df[df['tres_soldados'] == True]
        if not soldiers.empty:
            fig.add_trace(go.Scatter(
                x=soldiers['date'],
                y=soldiers['high'] + 1,
                mode='markers',
                marker=dict(symbol='circle', size=12, color='orange',
                            line=dict(color='black', width=1)),
                name='tres_soldados'
            ), row=1, col=1, secondary_y=False)

    # ✅ FILA 2: Volumen
    fig.add_trace(go.Bar(
        x=df['date'],
        y=df['volume'],
        marker_color='royalblue',
        marker_line_color='blue',
        marker_line_width=0.4,
        opacity=0.95,
        name='Volume'
    ), row=2, col=1)

    # 🟢 Puntos "Serpiente Látigo" (si existen índices válidos)
    if serpiente is not None and not serpiente.empty and 'latigo' in serpiente.columns:
        latigos = serpiente['latigo'].dropna().astype(int).unique()
        latigos = latigos[(latigos >= 0) & (latigos < len(df))]
        if len(latigos) > 0:
            puntos = df.iloc[latigos].copy()
            fig.add_trace(go.Scatter(
                x=puntos['date'],
                y=puntos['high'] + 0.25,
                mode='markers',
                marker=dict(symbol='circle', size=10, color='green',
                            line=dict(color='black', width=1)),
                name='Serpiente Latigo'
            ), row=1, col=1, secondary_y=False)

    # --- Ejes y layout limpios usando update_*axes por fila/columna ---
    fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])], row=1, col=1)
    fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])], row=2, col=1)

    fig.update_yaxes(title_text="Precio", row=1, col=1, secondary_y=False, showgrid=True)
    fig.update_yaxes(title_text="ATR / ATR fast", row=1, col=1, secondary_y=True, showgrid=False)
    fig.update_yaxes(title_text="Volumen", row=2, col=1, showgrid=True)

    fig.update_layout(
        title=f'{symbol}_{timeframe}',
        width=1800,
        height=800,
        margin=dict(l=20, r=20, t=40, b=20),
        font=dict(size=12, color="black"),
        plot_bgcolor='rgba(255,255,255,0.05)',
        paper_bgcolor='rgba(240,240,240,0.1)',
        showlegend=True,             # <- muestra leyenda para distinguir ATRs
        template='plotly_white',
        xaxis_rangeslider_visible=False
    )

    fig.write_html(html_path, config={"scrollZoom": True})
    print(f"✅ Gráfico guardado como HTML: '{html_path}'")
    webbrowser.open('file://' + os.path.realpath(html_path))
