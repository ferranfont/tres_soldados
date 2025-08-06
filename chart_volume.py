import os
import webbrowser
import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots

def plot_close_and_volume(symbol, timeframe, df):
    html_path = f'charts/candle_vol_chart_{symbol}_{timeframe}.html'
    os.makedirs(os.path.dirname(html_path), exist_ok=True)

    df = df.rename(columns=str.lower)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.8, 0.2],
        vertical_spacing=0.03
    )

    # ✅ SOLO EN FILA 1: Candlestick
    fig.add_trace(go.Candlestick(
        x=df['date'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name='Candlestick',
        increasing=dict(line=dict(color='#696969', width=1), fillcolor='#00FF00'),
        decreasing=dict(line=dict(color='black', width=1), fillcolor='red')
    ), row=1, col=1)


    # ✅ SOLO EN FILA 2: Volumen (NO velas)
    fig.add_trace(go.Bar(
        x=df['date'],
        y=df['volume'],
        marker_color='royalblue',
        marker_line_color='blue',
        marker_line_width=0.4,
        opacity=0.95,
        name='Volume'
    ), row=2, col=1)

    fig.update_layout(
        title=f'{symbol}_{timeframe}',
        width=1800,
        height=800,
        margin=dict(l=20, r=20, t=40, b=20),
        font=dict(size=12, color="black"),
        plot_bgcolor='rgba(255,255,255,0.05)',
        paper_bgcolor='rgba(240,240,240,0.1)',
        showlegend=False,
        template='plotly_white',
        xaxis=dict(
            type='date',
            tickformat="%b %d<br>%Y",
            tickangle=0,
            showgrid=False,
            linecolor='gray',
            linewidth=1
        ),
        yaxis=dict(showgrid=True, linecolor='gray', linewidth=1),
        xaxis2=dict(
            type='date',
            tickformat="%b %d<br>%Y",
            tickangle=45,
            showgrid=False,
            linecolor='gray',
            linewidth=1
        ),
        yaxis2=dict(showgrid=True, linecolor='grey', linewidth=1),
        xaxis_rangeslider_visible=False,
        xaxis2_matches=None,
    )

    fig.write_html(html_path, config={"scrollZoom": True})
    print(f"✅ Gráfico guardado como HTML: '{html_path}'")
    webbrowser.open('file://' + os.path.realpath(html_path))
