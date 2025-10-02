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


def plot_minute_data(symbol, timeframe, df, fractals_csv=None, confirmed_tops_csv=None, same_range_tops_csv=None, date_filter=None, tolerance=None, change_pct=None, trades_csv=None):
    """
    Función especializada para graficar datos de minutos con etiquetas de hora en el eje X

    Args:
        symbol: Trading symbol (e.g., 'ES')
        timeframe: Timeframe string for chart title
        df: DataFrame with OHLC data
        fractals_csv: Optional path to fractals CSV file. If None, will try to auto-detect.
        confirmed_tops_csv: Optional path to confirmed TOPs CSV for horizontal lines
        same_range_tops_csv: Optional path to same range TOPs CSV for orange dots
        date_filter: Date string (YYYY_MM_DD) to filter creek perdices CSV
        tolerance: Tolerance value to construct creek perdices filename
        change_pct: Zigzag change percentage for chart title
        trades_csv: Optional path to trades CSV file for entry/exit lines
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
        outputs_dir = os.path.join('outputs', 'fractal_tops_and_bottoms')
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
    # Build the exact filename based on date and tolerance if provided
    import glob

    if date_filter and tolerance is not None:
        # Use exact filename matching the date and tolerance
        true_tops_csv = f'outputs/fractal_tops_and_bottoms/true_tops_creek_perdices_{date_filter}_tol_{tolerance}.csv'
        print(f"🔍 Looking for creek perdices file: {true_tops_csv}")
    else:
        # Fallback: look for any creek perdices CSV
        creek_csvs = sorted(glob.glob('outputs/fractal_tops_and_bottoms/true_tops_creek_perdices_*.csv'), key=os.path.getmtime, reverse=True)
        true_tops_csv = creek_csvs[0] if creek_csvs else 'outputs/fractal_tops_and_bottoms/true_tops_creek_perdices.csv'

    if os.path.exists(true_tops_csv):
        df_true_tops = pd.read_csv(true_tops_csv)
        df_true_tops['timestamp'] = pd.to_datetime(df_true_tops['timestamp'])
        df_true_tops['last_top_timestamp'] = pd.to_datetime(df_true_tops['last_top_timestamp'])

        # Handle master candle timestamp if present
        if 'mastercandle_timestamp' in df_true_tops.columns:
            df_true_tops['mastercandle_timestamp'] = pd.to_datetime(df_true_tops['mastercandle_timestamp'], errors='coerce')

        # FILTER CLUSTERS: Only plot clusters that meet entry conditions
        # Conditions: creek_price > VWAP AND first_top_price > VWAP (at FIRST TOP time, not breakout)
        if 'ema' in df.columns and 'timestamp' in df_true_tops.columns and 'creek_price' in df_true_tops.columns:
            print(f"📊 Total clusters loaded: {len(df_true_tops)}")

            valid_clusters = []
            for idx, cluster in df_true_tops.iterrows():
                creek_price = cluster['creek_price']
                first_top_price = cluster['price']
                first_top_time = pd.to_datetime(cluster['timestamp'])  # Momento del cuadradito naranja

                # Get VWAP at FIRST TOP time (cuando se forma el cuadradito naranja)
                vwap_at_first_top = df[df['date'] == first_top_time]
                if len(vwap_at_first_top) > 0:
                    vwap_value = vwap_at_first_top.iloc[0]['ema']

                    # Check BOTH conditions with AND: creek > VWAP AND first_top > VWAP
                    condition1 = creek_price > vwap_value
                    condition2 = first_top_price > vwap_value

                    if pd.notna(vwap_value) and condition1 and condition2:
                        valid_clusters.append(idx)
                        print(f"   ✅ {cluster['group']}: Creek ${creek_price:.2f} > VWAP ${vwap_value:.2f} AND First TOP ${first_top_price:.2f} > VWAP ${vwap_value:.2f} (at {first_top_time})")
                    else:
                        # Debug: show which condition failed
                        if not condition1:
                            print(f"   ❌ {cluster['group']}: Creek ${creek_price:.2f} <= VWAP ${vwap_value:.2f} - FILTERED OUT")
                        if not condition2:
                            print(f"   ❌ {cluster['group']}: First TOP ${first_top_price:.2f} <= VWAP ${vwap_value:.2f} (at {first_top_time}) - FILTERED OUT")

            # Filter dataframe to only valid clusters
            df_true_tops = df_true_tops.loc[valid_clusters].reset_index(drop=True)
            print(f"✅ Clusters meeting entry conditions (creek>VWAP AND first_top>VWAP): {len(df_true_tops)}")

        # FILTER PENDING SIGNALS: Sequential temporal processing
        # Process clusters chronologically and cancel pending when new one appears BEFORE crossover
        if len(df_true_tops) > 0 and 'last_top_timestamp' in df_true_tops.columns:
            print(f"\n🔄 Applying sequential pending signal cancellation...")

            # Sort by first TOP timestamp to process chronologically
            df_true_tops = df_true_tops.sort_values('timestamp').reset_index(drop=True)

            clusters_to_keep = []
            pending_cluster_idx = None  # Track current pending signal

            for idx, cluster in df_true_tops.iterrows():
                first_top_time = pd.to_datetime(cluster['timestamp'])
                last_top_time = pd.to_datetime(cluster['last_top_timestamp'])
                creek_price = cluster['creek_price']

                # Check if ANY candle AFTER last TOP closed above creek
                candles_after_last_top = df[df['date'] > last_top_time]
                crossed_candles = candles_after_last_top[candles_after_last_top['close'] > creek_price]
                is_crossed = len(crossed_candles) > 0

                if is_crossed:
                    first_cross_time = crossed_candles.iloc[0]['date']

                    # If there was a pending signal, check if this new signal appeared BEFORE pending crossed
                    if pending_cluster_idx is not None:
                        pending_cluster = df_true_tops.loc[pending_cluster_idx]

                        # If new signal's first TOP appeared BEFORE pending was crossed, cancel pending
                        if first_top_time < first_cross_time:
                            print(f"   ❌ {pending_cluster['group']}: CANCELLED - {cluster['group']} appeared at {first_top_time} before cross at {first_cross_time}")
                            if pending_cluster_idx in clusters_to_keep:
                                clusters_to_keep.remove(pending_cluster_idx)

                    # This cluster crossed - keep it and clear pending
                    clusters_to_keep.append(idx)
                    pending_cluster_idx = None
                    print(f"   ✅ {cluster['group']}: CROSSED at {first_cross_time} - KEEP")
                else:
                    # Cluster NOT crossed yet
                    if pending_cluster_idx is not None:
                        pending_cluster = df_true_tops.loc[pending_cluster_idx]
                        pending_creek_price = pending_cluster['creek_price']
                        pending_last_top_time = pd.to_datetime(pending_cluster['last_top_timestamp'])

                        # Check if pending was crossed BEFORE this new signal appeared
                        candles_between = df[(df['date'] > pending_last_top_time) & (df['date'] <= first_top_time)]
                        pending_crossed_before_new = len(candles_between[candles_between['close'] > pending_creek_price]) > 0

                        if pending_crossed_before_new:
                            # Pending was crossed before new signal - keep pending and don't replace
                            print(f"   ✅ {pending_cluster['group']}: Already CROSSED before {cluster['group']} appeared - KEEP BOTH")
                            # Add this new cluster as well
                            clusters_to_keep.append(idx)
                            # Note: pending_cluster_idx stays the same, but we're keeping both
                        else:
                            # Pending NOT crossed before new signal - cancel it
                            print(f"   ❌ {pending_cluster['group']}: CANCELLED - {cluster['group']} appeared, pending not crossed")
                            if pending_cluster_idx in clusters_to_keep:
                                clusters_to_keep.remove(pending_cluster_idx)

                            # This becomes the new pending signal
                            pending_cluster_idx = idx
                            clusters_to_keep.append(idx)
                            print(f"   ⏳ {cluster['group']}: NEW PENDING at {first_top_time}")
                    else:
                        # No pending signal - this becomes pending
                        pending_cluster_idx = idx
                        clusters_to_keep.append(idx)
                        print(f"   ⏳ {cluster['group']}: PENDING at {first_top_time}")

            # Filter to only clusters we want to keep
            df_true_tops = df_true_tops.loc[clusters_to_keep].reset_index(drop=True)
            print(f"✅ Final clusters after sequential cancellation: {len(df_true_tops)}")

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

            # Draw gray rectangle with gradient effect (darker at top near creek, lighter at bottom)
            # Create gradient by stacking multiple rectangles with different opacities
            num_layers = 8
            price_step = (avg_price - lowest_low) / num_layers

            for layer in range(num_layers):
                y0_layer = lowest_low + (layer * price_step)
                y1_layer = lowest_low + ((layer + 1) * price_step)

                # Opacity increases from bottom (0.05) to top (0.25)
                # layer 0 (bottom) = 0.05, layer 7 (top) = 0.25
                # Step: (0.25 - 0.05) / 7 = 0.0286
                opacity_layer = 0.05 + (layer * 0.0286)

                # Add border line only on the top layer
                if layer == num_layers - 1:
                    line_style = dict(color='gray', width=1)
                else:
                    line_style = dict(width=0)

                fig.add_shape(
                    type="rect",
                    x0=cluster['timestamp'],
                    x1=end_time,
                    y0=y0_layer,
                    y1=y1_layer,
                    fillcolor='gray',
                    opacity=opacity_layer,
                    line=line_style,
                    row=1, col=1
                )

            # Draw blue horizontal creek line with enhanced hover info
            hover_text = (
                f"{cluster['group']}<br>"
                f"Creek: ${avg_price:.2f}<br>"
                f"TOPs: {cluster.get('top_count', 'N/A')}<br>"
                f"Bars: {cluster.get('cluster_size', 'N/A')}<br>"
                f"Touch: {cluster.get('touches_creek', 'N/A')}<br>"
                f"<extra></extra>"
            )

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
                hovertemplate=hover_text,
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
                        size=12,
                        symbol='triangle-up',
                        line=dict(color='green', width=1)
                    ),
                    name='Breakout' if idx == 0 else None,
                    hovertemplate=f"{cluster['group']} Breakout<br>Time: %{{x}}<br>Close: ${breakout_price:.2f}<extra></extra>",
                    showlegend=(idx == 0)
                ), row=1, col=1)

            # TEST: Plot black dots on candles touching quantile 90 (for testing only)
            # Calculate quantile 90 threshold
            quantile_90_threshold = lowest_low + (avg_price - lowest_low) * 0.90

            # Get extended range: 5 candles BEFORE first TOP to breakout
            first_top_idx_in_df = df[df['date'] == cluster['timestamp']].index
            if len(first_top_idx_in_df) > 0:
                start_idx_with_lookback = max(0, first_top_idx_in_df[0] - 5)
                start_time_with_lookback = df.iloc[start_idx_with_lookback]['date']
            else:
                start_time_with_lookback = cluster['timestamp']

            # Get extended range candles (5 bars before to breakout)
            range_candles_extended = df[(df['date'] >= start_time_with_lookback) &
                                        (df['date'] <= end_time)].copy()

            # Identify candle type (green = bullish, red = bearish)
            range_candles_extended['is_green'] = range_candles_extended['close'] >= range_candles_extended['open']

            # Filter candles touching quantile 90 based on candle type:
            # - Red candles: high OR open >= threshold
            # - Green candles: high OR close >= threshold
            range_candles_filtered = range_candles_extended[
                (
                    (~range_candles_extended['is_green']) &  # Red candles
                    ((range_candles_extended['high'] >= quantile_90_threshold) |
                     (range_candles_extended['open'] >= quantile_90_threshold))
                ) |
                (
                    (range_candles_extended['is_green']) &  # Green candles
                    ((range_candles_extended['high'] >= quantile_90_threshold) |
                     (range_candles_extended['close'] >= quantile_90_threshold))
                )
            ].copy()

            if len(range_candles_filtered) > 0:
                fig.add_trace(go.Scatter(
                    x=range_candles_filtered['date'],
                    y=range_candles_filtered['high'],  # Always plot at the high
                    mode='markers',
                    marker=dict(
                        color='black',
                        size=4,
                        symbol='circle'
                    ),
                    name='Q90 Touch' if idx == 0 else None,
                    hovertemplate=f"{cluster['group']} Q90<br>Time: %{{x}}<br>High: $%{{y:.2f}}<extra></extra>",
                    showlegend=(idx == 0)
                ), row=1, col=1)

        # Plot Master Candles (yellow asterisk 2 points below the low)
        if 'mastercandle' in df_true_tops.columns and 'mastercandle_timestamp' in df_true_tops.columns:
            master_candles = df_true_tops[df_true_tops['mastercandle'] == 'master'].copy()

            if len(master_candles) > 0:
                print(f"⭐ Plotting {len(master_candles)} Master Candles...")

                # For each master candle, find the low of that candle and build custom data
                master_lows = []
                master_times = []
                master_customdata = []

                for idx, mc in master_candles.iterrows():
                    mc_timestamp = mc['mastercandle_timestamp']
                    if pd.notna(mc_timestamp):
                        # Find the candle at this timestamp
                        candle_at_timestamp = df[df['date'] == mc_timestamp]
                        if len(candle_at_timestamp) > 0:
                            candle_low = candle_at_timestamp.iloc[0]['low']
                            master_lows.append(candle_low - 2.0)  # 2 points below the low
                            master_times.append(mc_timestamp)

                            # Get mastercandle data for hover
                            mc_range = mc.get('mastercandle_range', 0.0)
                            mc_tail_pct = mc.get('mastercandle_upper_tail_pct', 0.0)
                            mc_close = mc.get('mastercandle_close', 0.0)
                            mc_group = mc.get('group', 'N/A')

                            master_customdata.append([mc_group, mc_close, mc_range, mc_tail_pct])

                if len(master_times) > 0:
                    fig.add_trace(go.Scatter(
                        x=master_times,
                        y=master_lows,
                        mode='markers',
                        marker=dict(
                            color='gold',
                            size=12,
                            symbol='asterisk-open',
                            line=dict(color='orange', width=2)
                        ),
                        name='Master Candle',
                        customdata=master_customdata,
                        hovertemplate=(
                            'Master Candle<br>'
                            'Group: %{customdata[0]}<br>'
                            'Time: %{x}<br>'
                            'Close: $%{customdata[1]:.2f}<br>'
                            'Range: $%{customdata[2]:.2f}<br>'
                            'Upper Tail: %{customdata[3]:.1f}%<br>'
                            '<extra></extra>'
                        ),
                        showlegend=True
                    ), row=1, col=1)

        # Plot True Volume candles (red hash below the low)
        if 'true_volume1_time' in df_true_tops.columns:
            print(f"📊 Plotting True Volume candles...")

            # Collect all volume candles from all clusters
            volume_times = []
            volume_lows = []
            volume_customdata = []

            for idx, cluster in df_true_tops.iterrows():
                group = cluster['group']
                first_top_ts = cluster['timestamp']
                breakout_ts = cluster['breakout_timestamp']

                # Calculate average volume for this cluster's consolidation zone
                cluster_candles = df[
                    (df['date'] >= first_top_ts) &
                    (df['date'] <= breakout_ts)
                ]
                avg_volume = cluster_candles['volume'].mean() if len(cluster_candles) > 0 else 0

                # Check each volume slot (1, 2, 3)
                for vol_num in [1, 2, 3]:
                    vol_time_col = f'true_volume{vol_num}_time'
                    vol_value_col = f'true_volume{vol_num}_value'

                    if vol_time_col in cluster and pd.notna(cluster[vol_time_col]):
                        vol_time = cluster[vol_time_col]
                        vol_value = cluster[vol_value_col]

                        # Calculate volume ratio (as percentage)
                        vol_ratio_pct = (vol_value / avg_volume * 100) if avg_volume > 0 else 0

                        # Find the candle at this timestamp to get the low
                        candle_at_time = df[df['date'] == vol_time]
                        if len(candle_at_time) > 0:
                            candle_low = candle_at_time.iloc[0]['low']
                            volume_times.append(vol_time)
                            volume_lows.append(candle_low - 0.5)  # 0.5 points below the low
                            volume_customdata.append([group, vol_time, vol_value, avg_volume, vol_ratio_pct])

            if len(volume_times) > 0:
                fig.add_trace(go.Scatter(
                    x=volume_times,
                    y=volume_lows,
                    mode='markers',
                    marker=dict(
                        color='deeppink',
                        size=10,
                        symbol='hash-open',
                        line=dict(color='hotpink', width=2)
                    ),
                    name='High Volume',
                    customdata=volume_customdata,
                    hovertemplate=(
                        'High Volume<br>'
                        'Group: %{customdata[0]}<br>'
                        'Time: %{customdata[1]}<br>'
                        'Volume: %{customdata[2]:,.0f}<br>'
                        'Avg Volume: %{customdata[3]:,.0f}<br>'
                        'Ratio: %{customdata[4]:.1f}%<br>'
                        '<extra></extra>'
                    ),
                    showlegend=True
                ), row=1, col=1)
                print(f"   ✅ Plotted {len(volume_times)} high volume candles")

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

    # ====================================================
    # TRADES: Entry/Exit Lines (Dashed Grey)
    # ====================================================
    if trades_csv and os.path.exists(trades_csv):
        try:
            df_trades = pd.read_csv(trades_csv)
            df_trades['entry_time'] = pd.to_datetime(df_trades['entry_time'])
            df_trades['exit_time'] = pd.to_datetime(df_trades['exit_time'])
            print(f"📊 Loaded {len(df_trades)} trades from {os.path.basename(trades_csv)}")

            for idx, trade in df_trades.iterrows():
                entry_time = trade['entry_time']
                entry_price = trade['entry_price']
                exit_time = trade['exit_time']
                exit_price = trade['exit_price']

                # Determine line color based on exit reason
                exit_reason = trade['exit_reason']
                if exit_reason == 'TAKE_PROFIT':
                    line_color = 'green'
                elif exit_reason == 'STOP_LOSS':
                    line_color = 'red'
                else:  # CLOSE_EOD
                    line_color = 'grey'

                # Draw solid line from entry to exit
                fig.add_trace(go.Scatter(
                    x=[entry_time, exit_time],
                    y=[entry_price, exit_price],
                    mode='lines',
                    line=dict(
                        color=line_color,
                        width=1,
                        dash='solid'
                    ),
                    name='Trades' if idx == 0 else None,
                    hovertemplate=(
                        f"Trade #{trade['trade_id']} ({trade['entry_type']})<br>"
                        f"Entry: ${entry_price:.2f} @ %{{x}}<br>"
                        f"Exit: ${exit_price:.2f}<br>"
                        f"P&L: {trade['pnl_points']:+.2f} pts (${trade['pnl_usd']:+,.0f})<br>"
                        f"Exit: {trade['exit_reason']}<extra></extra>"
                    ),
                    showlegend=(idx == 0)
                ), row=1, col=1)

                # Add red triangle-down marker at exit point
                fig.add_trace(go.Scatter(
                    x=[exit_time],
                    y=[exit_price],
                    mode='markers',
                    marker=dict(
                        color='red',
                        size=10,
                        symbol='triangle-down',
                        line=dict(color='darkred', width=1)
                    ),
                    name='Exit' if idx == 0 else None,
                    hovertemplate=(
                        f"EXIT - Trade #{trade['trade_id']}<br>"
                        f"Price: ${exit_price:.2f}<br>"
                        f"Time: %{{x}}<br>"
                        f"Reason: {trade['exit_reason']}<br>"
                        f"P&L: {trade['pnl_points']:+.2f} pts (${trade['pnl_usd']:+,.0f})<extra></extra>"
                    ),
                    showlegend=(idx == 0)
                ), row=1, col=1)

        except Exception as e:
            print(f"⚠️ Error loading trades CSV: {e}")

    # Build title with parameters including day of week
    # Extract date from timeframe to get day of week
    date_part = timeframe.replace('1min_', '').replace('_', '-')
    try:
        date_obj = pd.to_datetime(date_part)
        day_of_week = date_obj.strftime('%A')  # Full day name (Monday, Tuesday, etc.)
        title_parts = [f'{symbol}_{timeframe} ({day_of_week}) - tres_soldados']
    except:
        title_parts = [f'{symbol}_{timeframe} - tres_soldados']

    if change_pct is not None:
        title_parts.append(f'ZigZag: {change_pct}%')
    if tolerance is not None:
        title_parts.append(f'Tol: {tolerance}')
    chart_title = ' | '.join(title_parts)

    fig.update_layout(
        dragmode='pan',
        title=chart_title,
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