"""
Strategy 1: Creek Crossover Above VWAP
=======================================
Entry Conditions:
1. Creek perdices level > VWAP
2. First TOP price (orange square) > VWAP

Target: +5 points
Stop Loss: -5 points
Exit: End of day if position open

Reads creek perdices signals and executes trades based on strategy rules.
Outputs trading record to CSV and generates HTML report.
"""

import pandas as pd
import sys
from pathlib import Path
from datetime import datetime
import webbrowser

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(str(Path(__file__).parent.parent))
from config import DATA_DIR, SYMBOL
from plot_minute_data import plot_minute_data

# ====================================================
# 📊 CONFIGURATION
# ====================================================

BASE_DIR = Path(__file__).parent.parent

# ====================================================
# ⚙️ USER CONFIGURATION - CHANGE THESE PARAMETERS
# ====================================================

# Date to analyze (format: YYYY_MM_DD)
DATE = '2023_03_13'  # Change this to analyze different dates

# Tolerance for creek perdices clustering (in points)
TOLERANCE = 2.0

# Strategy parameters
TARGET_POINTS = 5.0  # Target profit in points
STOP_POINTS = 5.0    # Stop loss in points
POINT_VALUE = 50.0   # 1 ES point = $50 USD

# ====================================================
# Command line arguments override (optional)
# ====================================================
date_str = sys.argv[1] if len(sys.argv) > 1 else DATE
tolerance = str(sys.argv[2]) if len(sys.argv) > 2 else str(TOLERANCE)

# File paths
CREEK_CSV = BASE_DIR / 'outputs' / 'fractal_tops_and_bottoms' / f'true_tops_creek_perdices_{date_str}_tol_{tolerance}.csv'
CANDLES_CSV = BASE_DIR / 'data' / 'daily_subdata' / f'es_1min_data_{date_str}.csv'

# Create tracking_records subfolder if it doesn't exist
TRACKING_DIR = BASE_DIR / 'outputs' / 'tracking_records'
TRACKING_DIR.mkdir(parents=True, exist_ok=True)

# Create tablas_html subfolder for HTML reports
TABLAS_HTML_DIR = BASE_DIR / 'outputs' / 'tablas_html'
TABLAS_HTML_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_CSV = TRACKING_DIR / f'trading_record_strat1_crossover_{date_str}.csv'
OUTPUT_HTML = TABLAS_HTML_DIR / f'trading_report_strat1_crossover_{date_str}.html'

# ====================================================
# 📥 LOAD DATA
# ====================================================

print("="*70)
print("📈 STRATEGY 1: CREEK CROSSOVER ABOVE VWAP")
print("="*70)
print(f"Date: {date_str}")
print(f"Entry Conditions:")
print(f"  1. Creek > VWAP")
print(f"  2. First TOP (orange square) > VWAP")
print(f"Target: +{TARGET_POINTS} points")
print(f"Stop Loss: -{STOP_POINTS} points")
print("="*70)

# Load creek perdices
if not CREEK_CSV.exists():
    print(f"ERROR: Creek perdices CSV not found: {CREEK_CSV}")
    sys.exit(1)

df_creek = pd.read_csv(CREEK_CSV)
# Strip whitespace from column names and values
df_creek.columns = [col.strip() for col in df_creek.columns]
df_creek = df_creek.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
df_creek['timestamp'] = pd.to_datetime(df_creek['timestamp'])
df_creek['breakout_timestamp'] = pd.to_datetime(df_creek['breakout_timestamp'])

print(f"✅ Loaded {len(df_creek)} creek perdices clusters")

# Load candles
if not CANDLES_CSV.exists():
    print(f"ERROR: Candles file not found: {CANDLES_CSV}")
    sys.exit(1)

df_candles = pd.read_csv(CANDLES_CSV)
df_candles.columns = [col.strip().lower() for col in df_candles.columns]
df_candles['date'] = pd.to_datetime(df_candles['date'])

# Check if VWAP/EMA column exists
if 'ema' not in df_candles.columns and 'vwap' not in df_candles.columns:
    print("ERROR: No VWAP/EMA column found in candles data")
    sys.exit(1)

# Use whichever column exists (ema is actually VWAP in clean_data_one_day_data.py)
vwap_col = 'ema' if 'ema' in df_candles.columns else 'vwap'
print(f"✅ Loaded {len(df_candles)} candles (using {vwap_col} as VWAP)")

# ====================================================
# 🔄 FILTER PENDING SIGNALS
# ====================================================

print("\n" + "="*70)
print("🔄 STEP 1: VWAP FILTER")
print("="*70)

print(f"📊 Total clusters loaded: {len(df_creek)}")

# Sort by first TOP timestamp to process chronologically
df_creek = df_creek.sort_values('timestamp').reset_index(drop=True)

# STEP 1: Filter by VWAP conditions FIRST
valid_vwap_indices = []
for idx, cluster in df_creek.iterrows():
    creek_price = cluster['creek_price']
    first_top_price = cluster['price']
    first_top_time = pd.to_datetime(cluster['timestamp'])

    # Get VWAP at FIRST TOP time
    vwap_at_first_top = df_candles[df_candles['date'] == first_top_time]

    if len(vwap_at_first_top) > 0:
        vwap_value = vwap_at_first_top.iloc[0]['ema']

        # Both creek AND first TOP must be above VWAP
        if pd.notna(vwap_value) and creek_price > vwap_value and first_top_price > vwap_value:
            valid_vwap_indices.append(idx)

print(f"✅ Clusters passing VWAP filter: {len(valid_vwap_indices)}")

# Filter to only VWAP-valid clusters
df_creek_vwap_filtered = df_creek.loc[valid_vwap_indices].reset_index(drop=True)

print("\n" + "="*70)
print("🔄 STEP 2: PENDING CANCELLATION (only on VWAP-valid clusters)")
print("="*70)

clusters_to_trade = []
pending_idx = None

# Need to process clusters sequentially, checking if pending crossed before next appears
for i in range(len(df_creek_vwap_filtered)):
    cluster = df_creek_vwap_filtered.iloc[i]
    idx = df_creek_vwap_filtered.index[i]

    first_top_time = pd.to_datetime(cluster['timestamp'])
    last_top_time = pd.to_datetime(cluster['last_top_timestamp'])
    creek_price = cluster['creek_price']

    # If there's a pending, check if it should be cancelled by this new cluster
    if pending_idx is not None:
        prev_cluster = df_creek_vwap_filtered.loc[pending_idx]
        prev_last_top = pd.to_datetime(prev_cluster['last_top_timestamp'])
        prev_creek = prev_cluster['creek_price']

        # RULE 1: If new cluster is at LOWER or EQUAL price, it will cross first - CANCEL pending immediately
        if creek_price <= prev_creek:
            print(f"   ❌ {prev_cluster['group']}: CANCELLED - {cluster['group']} at LOWER/EQUAL price (${creek_price:.2f} <= ${prev_creek:.2f}), will cross first")
            if pending_idx in clusters_to_trade:
                clusters_to_trade.remove(pending_idx)
            pending_idx = None
        else:
            # RULE 2: New cluster is HIGHER - check if pending crossed before new appeared
            candles_before_new = df_candles[(df_candles['date'] > prev_last_top) & (df_candles['date'] < first_top_time)]
            pending_crossed = candles_before_new[candles_before_new['close'] > prev_creek]

            if len(pending_crossed) > 0:
                # Pending crossed before new cluster's first TOP - keep pending
                first_cross = pending_crossed.iloc[0]['date']
                print(f"   ✅ {prev_cluster['group']}: CROSSED at {first_cross} BEFORE {cluster['group']} first TOP ({first_top_time}) - KEEP")
                pending_idx = None  # Clear pending
            else:
                # Pending NOT crossed before new first TOP - CANCEL it
                print(f"   ❌ {prev_cluster['group']}: CANCELLED - {cluster['group']} first TOP appeared ({first_top_time}), pending not crossed yet")
                if pending_idx in clusters_to_trade:
                    clusters_to_trade.remove(pending_idx)
                pending_idx = None

    # Check if THIS cluster will cross before the NEXT cluster appears (or end of day if last)
    # Get the next cluster's first TOP time (if exists)
    if i < len(df_creek_vwap_filtered) - 1:
        next_cluster = df_creek_vwap_filtered.iloc[i + 1]
        next_first_top = pd.to_datetime(next_cluster['timestamp'])
        # Check if crosses BEFORE next cluster appears
        candles_until_next = df_candles[(df_candles['date'] > last_top_time) & (df_candles['date'] < next_first_top)]
        crossed = candles_until_next[candles_until_next['close'] > creek_price]
    else:
        # Last cluster - check all remaining candles
        candles_until_next = df_candles[df_candles['date'] > last_top_time]
        crossed = candles_until_next[candles_until_next['close'] > creek_price]

    if len(crossed) > 0:
        # This cluster crossed before next appeared - keep it
        first_cross = crossed.iloc[0]['date']
        clusters_to_trade.append(idx)
        print(f"   ✅ {cluster['group']}: CROSSED at {first_cross} - KEEP FOR TRADING")
        pending_idx = None  # Not pending anymore
    else:
        # NOT crossed before next - becomes new pending (will be evaluated when next arrives)
        pending_idx = idx
        clusters_to_trade.append(idx)
        print(f"   ⏳ {cluster['group']}: PENDING")

# Filter dataframe to only clusters we want to trade
df_creek = df_creek_vwap_filtered.loc[clusters_to_trade].reset_index(drop=True)
print(f"✅ Final clusters after cancellation: {len(df_creek)}")

# ====================================================
# 📊 TRADING LOGIC
# ====================================================

print("\n" + "="*70)
print("EXECUTING STRATEGY")
print("="*70)

trades = []
trade_id = 1

for idx, cluster in df_creek.iterrows():
    group = cluster['group']
    creek_price = cluster['creek_price']
    first_top_price = cluster['price']  # Precio del primer TOP del cluster
    first_top_time = cluster['timestamp']  # Momento cuando se forma el cuadradito naranja
    breakout_time = cluster['breakout_timestamp']
    is_master = cluster['mastercandle'] == 'master'

    # Get VWAP at FIRST TOP time (cuando se forma el cuadradito naranja, NO en el breakout)
    vwap_at_first_top = df_candles[df_candles['date'] == first_top_time]

    if len(vwap_at_first_top) == 0:
        print(f"⚠️ {group}: No candle data at first TOP time {first_top_time}")
        continue

    vwap_value = vwap_at_first_top.iloc[0][vwap_col]

    # Check entry conditions:
    # 1. creek > VWAP (at first TOP time)
    # 2. first TOP price > VWAP (at first TOP time - cuando se forma el cuadradito naranja)
    if pd.notna(vwap_value) and creek_price > vwap_value and first_top_price > vwap_value:
        # Determine entry price: use master candle close if available, otherwise breakout candle close
        if is_master and pd.notna(cluster['mastercandle_close']):
            entry_price = cluster['mastercandle_close']
            entry_type = "MASTER"
        else:
            # Get breakout candle close
            breakout_candle = df_candles[df_candles['date'] == breakout_time]
            if len(breakout_candle) == 0:
                print(f"⚠️ {group}: No candle data at breakout time {breakout_time}")
                continue
            entry_price = breakout_candle.iloc[0]['close']
            entry_type = "BREAKOUT"

        print(f"\n🟢 {group}: ENTRY SIGNAL ({entry_type})")
        print(f"   Creek: ${creek_price:.2f} > VWAP: ${vwap_value:.2f} (at first TOP time {first_top_time})")
        print(f"   First TOP: ${first_top_price:.2f} > VWAP: ${vwap_value:.2f} (at first TOP time {first_top_time})")
        print(f"   Entry Time: {breakout_time}")

        # Entry details
        entry_time = breakout_time
        target_price = entry_price + TARGET_POINTS
        stop_price = entry_price - STOP_POINTS

        print(f"   Entry: ${entry_price:.2f}")
        print(f"   Target: ${target_price:.2f}")
        print(f"   Stop: ${stop_price:.2f}")

        # Get all candles after entry
        future_candles = df_candles[df_candles['date'] > entry_time].copy()

        if len(future_candles) == 0:
            print(f"   ⚠️ No future candles after entry - skipping")
            continue

        # Track trade outcome
        exit_price = None
        exit_time = None
        exit_reason = None

        for _, candle in future_candles.iterrows():
            candle_high = candle['high']
            candle_low = candle['low']
            candle_close = candle['close']
            candle_time = candle['date']

            # Check if target hit
            if candle_high >= target_price:
                exit_price = target_price
                exit_time = candle_time
                exit_reason = 'TAKE_PROFIT'
                print(f"   ✅ TAKE PROFIT at ${exit_price:.2f} ({candle_time})")
                break

            # Check if stop hit
            if candle_low <= stop_price:
                exit_price = stop_price
                exit_time = candle_time
                exit_reason = 'STOP_LOSS'
                print(f"   ❌ STOP LOSS at ${exit_price:.2f} ({candle_time})")
                break

        # If no exit, close at end of day
        if exit_price is None:
            last_candle = future_candles.iloc[-1]
            exit_price = last_candle['close']
            exit_time = last_candle['date']
            exit_reason = 'CLOSE_EOD'
            print(f"   🔵 CLOSE END OF DAY at ${exit_price:.2f} ({exit_time})")

        # Calculate P&L
        pnl = exit_price - entry_price
        pnl_pct = (pnl / entry_price) * 100
        pnl_usd = pnl * POINT_VALUE

        # Record trade
        trades.append({
            'trade_id': trade_id,
            'cluster': group,
            'entry_type': entry_type,
            'entry_time': entry_time,
            'entry_price': entry_price,
            'exit_time': exit_time,
            'exit_price': exit_price,
            'exit_reason': exit_reason,
            'target': target_price,
            'stop': stop_price,
            'pnl_points': pnl,
            'pnl_usd': pnl_usd,
            'pnl_percent': pnl_pct,
            'creek_price': creek_price,
            'vwap_at_entry': vwap_value
        })

        trade_id += 1
    else:
        # Determine which condition(s) failed
        vwap_display = f"${vwap_value:.2f}" if pd.notna(vwap_value) else "N/A"
        creek_vs_vwap = creek_price > vwap_value if pd.notna(vwap_value) else False
        top_vs_vwap = first_top_price > vwap_value if pd.notna(vwap_value) else False

        # Build failure message
        failed_conditions = []
        if not creek_vs_vwap:
            failed_conditions.append(f"Creek ${creek_price:.2f} <= VWAP {vwap_display}")
        if not top_vs_vwap:
            failed_conditions.append(f"First TOP ${first_top_price:.2f} <= VWAP {vwap_display}")

        print(f"❌ {group}: NO ENTRY - {' AND '.join(failed_conditions)}")

# ====================================================
# 💾 SAVE RESULTS
# ====================================================

if len(trades) > 0:
    df_trades = pd.DataFrame(trades)
    df_trades.to_csv(OUTPUT_CSV, index=False)
    print(f"\n💾 Trading record saved: {OUTPUT_CSV}")

    # ====================================================
    # 📊 GENERATE HTML REPORT
    # ====================================================

    print(f"📊 Generating HTML report...")

    # Calculate statistics
    total_trades = len(df_trades)
    winning_trades = len(df_trades[df_trades['pnl_points'] > 0])
    losing_trades = len(df_trades[df_trades['pnl_points'] < 0])
    breakeven_trades = len(df_trades[df_trades['pnl_points'] == 0])

    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    total_pnl = df_trades['pnl_points'].sum()
    total_pnl_usd = df_trades['pnl_usd'].sum()
    avg_win = df_trades[df_trades['pnl_points'] > 0]['pnl_points'].mean() if winning_trades > 0 else 0
    avg_win_usd = df_trades[df_trades['pnl_usd'] > 0]['pnl_usd'].mean() if winning_trades > 0 else 0
    avg_loss = df_trades[df_trades['pnl_points'] < 0]['pnl_points'].mean() if losing_trades > 0 else 0
    avg_loss_usd = df_trades[df_trades['pnl_usd'] < 0]['pnl_usd'].mean() if losing_trades > 0 else 0

    # Count exit reasons
    take_profit_count = len(df_trades[df_trades['exit_reason'] == 'TAKE_PROFIT'])
    stop_loss_count = len(df_trades[df_trades['exit_reason'] == 'STOP_LOSS'])
    eod_count = len(df_trades[df_trades['exit_reason'] == 'CLOSE_EOD'])

    # Generate HTML
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Strategy 1 - Creek Crossover Report</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px auto;
                max-width: 1800px;
                background-color: #f5f5f5;
                padding: 0 10px;
            }}
            .header {{
                background-color: #2c3e50;
                color: white;
                padding: 20px;
                border-radius: 5px;
                margin-bottom: 20px;
            }}
            .stats {{
                background-color: white;
                padding: 20px;
                border-radius: 5px;
                margin-bottom: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin-top: 15px;
            }}
            .stat-box {{
                padding: 15px;
                background-color: #ecf0f1;
                border-radius: 5px;
                text-align: center;
            }}
            .stat-value {{
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
            }}
            .stat-label {{
                font-size: 12px;
                color: #7f8c8d;
                margin-top: 5px;
            }}
            .positive {{
                color: #27ae60;
            }}
            .negative {{
                color: #e74c3c;
            }}
            .table-container {{
                background-color: white;
                padding: 40px 20px;
                border-radius: 5px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin: 30px auto;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                background-color: white;
            }}
            th {{
                background-color: #34495e;
                color: white;
                padding: 12px;
                text-align: left;
            }}
            td {{
                padding: 10px;
                border-bottom: 1px solid #ecf0f1;
            }}
            tr:hover {{
                background-color: #f8f9fa;
            }}
            .tag {{
                padding: 4px 8px;
                border-radius: 3px;
                font-size: 11px;
                font-weight: bold;
            }}
            .tag-tp {{
                background-color: #d4edda;
                color: #155724;
            }}
            .tag-sl {{
                background-color: #f8d7da;
                color: #721c24;
            }}
            .tag-eod {{
                background-color: #d1ecf1;
                color: #0c5460;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📈 Strategy 1: Creek Crossover Above VWAP</h1>
            <p>Date: {date_str} | Target: +{TARGET_POINTS} pts | Stop: -{STOP_POINTS} pts</p>
        </div>

        <div class="stats">
            <h2>📊 Performance Summary</h2>
            <div class="stats-grid">
                <div class="stat-box">
                    <div class="stat-value">{total_trades}</div>
                    <div class="stat-label">Total Trades</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value positive">{winning_trades}</div>
                    <div class="stat-label">Winners</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value negative">{losing_trades}</div>
                    <div class="stat-label">Losers</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">{win_rate:.1f}%</div>
                    <div class="stat-label">Win Rate</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value {'positive' if total_pnl > 0 else 'negative'}">{total_pnl:+.2f}</div>
                    <div class="stat-label">Total P&L (points)</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value {'positive' if total_pnl_usd > 0 else 'negative'}">${total_pnl_usd:+,.0f}</div>
                    <div class="stat-label">Total P&L (USD)</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value positive">{avg_win:.2f} pts</div>
                    <div class="stat-label">Avg Win (${avg_win_usd:,.0f})</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value negative">{avg_loss:.2f} pts</div>
                    <div class="stat-label">Avg Loss (${avg_loss_usd:,.0f})</div>
                </div>
            </div>

            <h3 style="margin-top: 20px;">Exit Reasons</h3>
            <div class="stats-grid">
                <div class="stat-box">
                    <div class="stat-value positive">{take_profit_count}</div>
                    <div class="stat-label">Take Profit</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value negative">{stop_loss_count}</div>
                    <div class="stat-label">Stop Loss</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">{eod_count}</div>
                    <div class="stat-label">Close EOD</div>
                </div>
            </div>
        </div>

        <div class="table-container">
            <h2>📋 Trade Details</h2>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Cluster</th>
                        <th>Entry Type</th>
                        <th>Entry Time</th>
                        <th>Entry Price</th>
                        <th>Exit Time</th>
                        <th>Exit Price</th>
                        <th>Exit Reason</th>
                        <th>P&L (pts)</th>
                        <th>P&L (USD)</th>
                        <th>P&L %</th>
                    </tr>
                </thead>
                <tbody>
    """

    for _, trade in df_trades.iterrows():
        pnl_class = 'positive' if trade['pnl_points'] > 0 else 'negative' if trade['pnl_points'] < 0 else ''

        if trade['exit_reason'] == 'TAKE_PROFIT':
            tag_class = 'tag-tp'
            tag_text = 'TAKE PROFIT'
        elif trade['exit_reason'] == 'STOP_LOSS':
            tag_class = 'tag-sl'
            tag_text = 'STOP LOSS'
        else:
            tag_class = 'tag-eod'
            tag_text = 'CLOSE EOD'

        html_content += f"""
                <tr>
                    <td>{trade['trade_id']}</td>
                    <td>{trade['cluster']}</td>
                    <td><strong>{trade['entry_type']}</strong></td>
                    <td>{trade['entry_time']}</td>
                    <td>${trade['entry_price']:.2f}</td>
                    <td>{trade['exit_time']}</td>
                    <td>${trade['exit_price']:.2f}</td>
                    <td><span class="tag {tag_class}">{tag_text}</span></td>
                    <td class="{pnl_class}">{trade['pnl_points']:+.2f}</td>
                    <td class="{pnl_class}"><strong>${trade['pnl_usd']:+,.0f}</strong></td>
                    <td class="{pnl_class}">{trade['pnl_percent']:+.2f}%</td>
                </tr>
        """

    html_content += """
            </tbody>
        </table>
        </div>
    </body>
    </html>
    """

    # Save HTML
    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"✅ HTML report saved: {OUTPUT_HTML}")

    # Open in browser
    webbrowser.open(f'file://{OUTPUT_HTML.absolute()}')

    # ====================================================
    # 📊 PRINT SUMMARY
    # ====================================================

    print("\n" + "="*70)
    print("📊 STRATEGY PERFORMANCE SUMMARY")
    print("="*70)
    print(f"Total Trades: {total_trades}")
    print(f"Winners: {winning_trades} | Losers: {losing_trades} | Breakeven: {breakeven_trades}")
    print(f"Win Rate: {win_rate:.1f}%")
    print(f"Total P&L: {total_pnl:+.2f} points (${total_pnl_usd:+,.0f} USD)")
    print(f"Average Win: {avg_win:.2f} points (${avg_win_usd:,.0f} USD)")
    print(f"Average Loss: {avg_loss:.2f} points (${avg_loss_usd:,.0f} USD)")
    print("\nExit Reasons:")
    print(f"  Take Profit: {take_profit_count}")
    print(f"  Stop Loss: {stop_loss_count}")
    print(f"  Close EOD: {eod_count}")
    print("="*70)

    # ====================================================
    # 📈 GENERATE CHART WITH TRADES
    # ====================================================
    print(f"\n{'='*70}")
    print("GENERATING CHART WITH TRADES...")
    print(f"{'='*70}")

    # Normalize columns
    df_candles.columns = [col.strip().lower() for col in df_candles.columns]
    df_candles = df_candles.rename(columns={'volumen': 'volume'})

    # Ensure datetime format
    df_candles['date'] = pd.to_datetime(df_candles['date'], utc=True)

    # Extract date from filename for timeframe
    timeframe = f'1min_{date_str}'

    # Plot chart with trades overlay
    plot_minute_data(
        SYMBOL,
        timeframe,
        df_candles,
        date_filter=date_str,
        tolerance=float(tolerance),
        change_pct=0.10,  # Default zigzag sensitivity
        trades_csv=str(OUTPUT_CSV)
    )

    print(f"\n✅ Chart with trades generated: charts/{SYMBOL}_{timeframe}.html")

else:
    print("\n❌ No trades executed - no entry signals found")
    print("="*70)

print("\n✅ Strategy execution complete!")
