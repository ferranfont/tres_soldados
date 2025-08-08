import os
import webbrowser
import pandas as pd
import plotly.graph_objs as go

from quant_stat.find_whipsaw import detect_trend_end_whipsaw

def plot_close_line(
    df: pd.DataFrame,
    symbol="ES",
    timeframe="15min",
    html_path=None,
    line_color="royalblue",
    line_width=2,
    show_only_horizontal_grid=True
):
    data = df.copy()
    if 'date' not in data.columns:
        data = data.reset_index().rename(columns={'index': 'date'})
    data['date'] = pd.to_datetime(data['date'], errors='coerce')
    data['close'] = pd.to_numeric(data['close'], errors='coerce')
    data = data.dropna(subset=['date', 'close']).sort_values('date')

    if html_path is None:
        html_path = f"charts/close_line_{symbol}_{timeframe}.html"
    os.makedirs(os.path.dirname(html_path), exist_ok=True)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=data['date'], y=data['close'],
        mode='lines', name='Close',
        line=dict(width=line_width, color=line_color)
    ))
    fig.update_layout(
        title=f"{symbol} - {timeframe} (Close)",
        width=1800, height=800,
        margin=dict(l=20, r=20, t=40, b=20),
        template="plotly_white",
        showlegend=True,
        xaxis_rangeslider_visible=False
    )
    if show_only_horizontal_grid:
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=True)

    fig.write_html(html_path, config={"scrollZoom": True})
    print(f"✅ Gráfico guardado en: '{html_path}'")
    try:
        webbrowser.open("file://" + os.path.realpath(html_path))
    except Exception:
        pass

def plot_high_low_with_whipsaw(
    df: pd.DataFrame,
    symbol="ES",
    timeframe="15min",
    html_path=None,
    fill_between=True,
    high_color="rgba(0, 0, 255, 1.0)",        # Azul fuerte para la línea de máximos
    low_color="rgba(70, 130, 180, 1.0)",      # Azul acero para la línea de mínimos
    band_color="rgba(0, 0, 255, 0.15)",       # Azul transparente para la banda
    show_only_horizontal_grid=True
):

    """Pinta High/Low y marca whipsaws (si no existen columnas, las calcula)."""
    data = df.copy()
    if 'date' not in data.columns:
        data = data.reset_index().rename(columns={'index': 'date'})
    for c in ['high', 'low', 'close']:
        data[c] = pd.to_numeric(data[c], errors='coerce')
    data['date'] = pd.to_datetime(data['date'])
    data = data.sort_values('date')

    need_detect = not {'whip_after_up', 'whip_after_down', 'atr', 'slope'}.issubset(data.columns)
    if need_detect:
        data = detect_trend_end_whipsaw(data)

    if html_path is None:
        html_path = f"charts/high_low_whipsaw_{symbol}_{timeframe}.html"
    os.makedirs(os.path.dirname(html_path), exist_ok=True)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=data['date'], y=data['low'],
        mode='lines', name='Low',
        line=dict(width=2, color=low_color), fill=None
    ))
    fig.add_trace(go.Scatter(
        x=data['date'], y=data['high'],
        mode='lines', name='High',
        line=dict(width=2, color=high_color),
        fill='tonexty' if fill_between else None,
        fillcolor=band_color if fill_between else None
    ))

    wu = data.loc[data['whip_after_up']]
    wd = data.loc[data['whip_after_down']]
    if not wu.empty:
        fig.add_trace(go.Scatter(
            x=wu['date'], y=wu['high'],
            mode='markers', name='Whipsaw after Up',
            marker=dict(symbol='triangle-down', size=14, line=dict(width=1)),
            customdata=wu[['atr','slope']].to_numpy(),
            hovertemplate=("Whipsaw after Up<br>"
                           "Date: %{x}<br>High: %{y:.2f}<br>"
                           "ATR: %{customdata[0]:.2f}<br>"
                           "Slope: %{customdata[1]:.4f}<extra></extra>")
        ))
    if not wd.empty:
        fig.add_trace(go.Scatter(
            x=wd['date'], y=wd['low'],
            mode='markers', name='Whipsaw after Down',
            marker=dict(symbol='triangle-up', size=14, line=dict(width=1)),
            customdata=wd[['atr','slope']].to_numpy(),
            hovertemplate=("Whipsaw after Down<br>"
                           "Date: %{x}<br>Low: %{y:.2f}<br>"
                           "ATR: %{customdata[0]:.2f}<br>"
                           "Slope: %{customdata[1]:.4f}<extra></extra>")
        ))

    fig.update_layout(
        title=f"{symbol} - {timeframe} (High & Low + Whipsaw)",
        width=1800, height=800,
        margin=dict(l=20, r=20, t=40, b=20),
        template="plotly_white",
        showlegend=True,
        xaxis_rangeslider_visible=False
    )
    if show_only_horizontal_grid:
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=True)

    fig.write_html(html_path, config={"scrollZoom": True})
    print(f"✅ Gráfico guardado en: '{html_path}'")
    try:
        webbrowser.open("file://" + os.path.realpath(html_path))
    except Exception:
        pass
