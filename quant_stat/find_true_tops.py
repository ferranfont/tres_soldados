"""
Find True TOPs - Creek Perdices Detection
Identifies TRUE TOPs that meet strict criteria for consolidation trading
Criteria for TRUE TOP:
ONLY ONE CRITERION: Next TOP is in SAME RANGE within tolerance (is_same_range = True)
This identifies consolidation zones where the next TOP is within ±2 points.
"""

import pandas as pd
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from config import DATA_DIR

# ====================================================
# 📊 CONFIGURATION
# ====================================================

# Get absolute paths
BASE_DIR = Path(__file__).parent.parent

# Analysis parameters from main.py
TOLERANCE_PRICE = float(sys.argv[1]) if len(sys.argv) > 1 else 2.0
date_str = sys.argv[2] if len(sys.argv) > 2 else '2023_03_02'  # Date from main.py

# Build file paths based on date received
import glob
import re

# Find fractals file matching the specific date
fractals_pattern = str(BASE_DIR / 'outputs' / f'fractals_es_1min_data_{date_str}_zigzag_*.csv')
fractals_files = glob.glob(fractals_pattern)

if not fractals_files:
    print(f"ERROR: No fractals CSV found for date {date_str}")
    print(f"Looking for: {fractals_pattern}")
    sys.exit(1)

FRACTALS_CSV = Path(fractals_files[0])
print(f"📂 Using fractals file: {FRACTALS_CSV.name}")

CANDLES_CSV = BASE_DIR / 'data' / f'es_1min_data_{date_str}.csv'

if not CANDLES_CSV.exists():
    print(f"ERROR: Candles file not found: {CANDLES_CSV}")
    sys.exit(1)

OUTPUT_CSV = BASE_DIR / 'outputs' / f'true_tops_creek_perdices_{date_str}_tol_{TOLERANCE_PRICE}.csv'

# ====================================================
# 📥 LOAD DATA
# ====================================================

print("="*70)
print("🎯 FIND TRUE TOPS - CREEK PERDICES DETECTION")
print("="*70)
print(f"Tolerance: ±{TOLERANCE_PRICE} points")

# Load fractals
df_fractals = pd.read_csv(FRACTALS_CSV)
df_fractals['timestamp'] = pd.to_datetime(df_fractals['timestamp'])

# Load candles
df_candles = pd.read_csv(CANDLES_CSV)
df_candles.columns = [col.strip().lower() for col in df_candles.columns]
df_candles['date'] = pd.to_datetime(df_candles['date'])

print(f"✅ Loaded {len(df_fractals)} fractals")
print(f"✅ Loaded {len(df_candles)} candles")

# Filter only TOPs
df_tops = df_fractals[df_fractals['type'] == 'TOP'].copy().reset_index(drop=True)
print(f"📈 Analyzing {len(df_tops)} TOPs")

# ====================================================
# 📊 ANALYSIS: Find True TOPs
# ====================================================

print("\n" + "="*70)
print("ANALYSIS: TRUE TOP DETECTION")
print("="*70)

# Group TOPs into clusters based on price proximity
# A cluster is a group of consecutive TOPs within TOLERANCE_PRICE of each other
clusters = []
current_cluster = []
cluster_counter = 0

for i in range(len(df_tops)):
    current_top = df_tops.iloc[i]

    if len(current_cluster) == 0:
        # Start new cluster
        current_cluster.append(i)
    else:
        # Check if current TOP is within range of ANY TOP in current cluster
        in_range = False
        for cluster_idx in current_cluster:
            cluster_top = df_tops.iloc[cluster_idx]
            if abs(current_top['price'] - cluster_top['price']) <= TOLERANCE_PRICE:
                in_range = True
                break

        if in_range:
            # Add to current cluster
            current_cluster.append(i)
        else:
            # Save current cluster if it has at least 2 TOPs
            if len(current_cluster) >= 2:
                cluster_counter += 1
                cluster_tag = f"cluster_{chr(64 + cluster_counter)}"
                clusters.append({
                    'group': cluster_tag,
                    'indices': current_cluster.copy()
                })
            # Start new cluster
            current_cluster = [i]

# Save last cluster if valid
if len(current_cluster) >= 2:
    cluster_counter += 1
    cluster_tag = f"cluster_{chr(64 + cluster_counter)}"
    clusters.append({
        'group': cluster_tag,
        'indices': current_cluster.copy()
    })

# Create analysis results from clusters
analysis_results = []
for cluster in clusters:
    cluster_tops = df_tops.iloc[cluster['indices']]
    first_top = cluster_tops.iloc[0]
    last_top = cluster_tops.iloc[-1]

    # Calculate average price for creek line (mean of ALL TOPs in cluster)
    avg_price = cluster_tops['price'].mean()

    # Find breakout candle (first close above creek line after last TOP)
    first_candle_idx = first_top['index']  # Index in original candles dataframe
    last_top_candle_idx = last_top['index']

    # Get candles after the last TOP
    candles_after_last_top = df_candles[df_candles['date'] > last_top['timestamp']].copy()

    # Find first candle that closes above the creek line
    breakout_candles = candles_after_last_top[candles_after_last_top['close'] > avg_price]

    if len(breakout_candles) > 0:
        # Found breakout - use first breakout candle
        breakout_candle = breakout_candles.iloc[0]
        breakout_idx = breakout_candle.name  # DataFrame index
        breakout_timestamp = breakout_candle['date']
    else:
        # No breakout found - extend 2 candles beyond last TOP
        last_top_df_idx = df_candles[df_candles['date'] == last_top['timestamp']].index
        if len(last_top_df_idx) > 0 and last_top_df_idx[0] + 2 < len(df_candles):
            breakout_idx = last_top_df_idx[0] + 2
            breakout_timestamp = df_candles.iloc[breakout_idx]['date']
        else:
            # Fallback to last TOP
            breakout_idx = last_top_candle_idx
            breakout_timestamp = last_top['timestamp']

    # Calculate cluster_size as number of bars from first TOP to breakout candle
    cluster_bars = breakout_idx - first_candle_idx + 1  # +1 to include both ends

    # Get candles starting from 5 bars BEFORE first TOP to breakout (for Touch calculation)
    first_top_df_idx = df_candles[df_candles['date'] == first_top['timestamp']].index
    if len(first_top_df_idx) > 0:
        start_idx_with_lookback = max(0, first_top_df_idx[0] - 5)  # 5 bars before, or 0 if not enough
        start_timestamp_with_lookback = df_candles.iloc[start_idx_with_lookback]['date']
    else:
        start_timestamp_with_lookback = first_top['timestamp']

    # Get all candles in the extended range (5 bars before first TOP to breakout)
    cluster_candles_extended = df_candles[(df_candles['date'] >= start_timestamp_with_lookback) &
                                          (df_candles['date'] <= breakout_timestamp)].copy()

    # Get candles in the normal cluster range (from first TOP to breakout) for lowest_low calculation
    cluster_candles = df_candles[(df_candles['date'] >= first_top['timestamp']) &
                                  (df_candles['date'] <= breakout_timestamp)].copy()

    # Find the lowest low in the normal range to calculate quantile 90
    lowest_low = cluster_candles['low'].min()

    # Calculate quantile 90 threshold (90% of the way from lowest low to creek)
    price_range = avg_price - lowest_low
    quantile_90_threshold = lowest_low + (price_range * 0.90)

    # Identify candle type (green = bullish, red = bearish) in EXTENDED range
    cluster_candles_extended['is_green'] = cluster_candles_extended['close'] >= cluster_candles_extended['open']

    # Count candles touching quantile 90 based on candle type (using EXTENDED range with 5 bars lookback):
    # - Red candles: high OR open >= threshold
    # - Green candles: high OR close >= threshold
    candles_touching_creek = cluster_candles_extended[
        (
            (~cluster_candles_extended['is_green']) &  # Red candles
            ((cluster_candles_extended['high'] >= quantile_90_threshold) |
             (cluster_candles_extended['open'] >= quantile_90_threshold))
        ) |
        (
            (cluster_candles_extended['is_green']) &  # Green candles
            ((cluster_candles_extended['high'] >= quantile_90_threshold) |
             (cluster_candles_extended['close'] >= quantile_90_threshold))
        )
    ]
    touch_count = len(candles_touching_creek)

    analysis_results.append({
        'group': cluster['group'],
        'top_index': cluster['indices'][0],
        'timestamp': first_top['timestamp'],
        'price': first_top['price'],
        'next_top_price': last_top['price'],
        'price_diff_next': round(abs(last_top['price'] - first_top['price']), 2),
        'is_same_range': True,
        'top_count': len(cluster['indices']),  # Number of TOPs in cluster
        'cluster_size': cluster_bars,  # Number of bars from first TOP to breakout
        'touches_creek': touch_count,  # Candles touching/near creek (quantile 90)
        'first_top_idx': cluster['indices'][0],
        'last_top_idx': cluster['indices'][-1],
        'last_top_timestamp': last_top['timestamp'],
        'breakout_timestamp': breakout_timestamp,
        'creek_price': round(avg_price, 2)
    })

# Create DataFrame with results
df_true_tops = pd.DataFrame(analysis_results)

# ====================================================
# 💾 SAVE RESULTS
# ====================================================

# Save CSV
df_true_tops.to_csv(OUTPUT_CSV, index=False)
print(f"\n💾 CSV saved: {OUTPUT_CSV}")

# ====================================================
# 📊 DISPLAY RESULTS
# ====================================================

print("\n" + "="*70)
print("🎯 TRUE TOPS DETECTED - CREEK PERDICES CANDIDATES")
print("="*70)
print(f"\n✅ Found {len(df_true_tops)} TRUE TOPs (out of {len(df_tops)} total TOPs)")

if len(df_true_tops) > 0:
    print(f"\n{'Group':<12} | {'TOPs':<5} | {'Bars':<5} | {'Touch':<6} | {'Creek':<10} | {'First TOP':<20} | {'Price':<10} | {'Last TOP':<20} | {'Last Price':<10} | {'Diff':<8}")
    print("-" * 145)
    for idx, top in df_true_tops.iterrows():
        print(f"{top['group']:<12} | {top['top_count']:<5} | {top['cluster_size']:<5} | {top['touches_creek']:<6} | ${top['creek_price']:<9.2f} | {str(top['timestamp']):<20} | ${top['price']:<9.2f} | {str(top['last_top_timestamp']):<20} | ${top['next_top_price']:<9.2f} | ${top['price_diff_next']:.2f}")

    print("\n" + "="*70)
    print("📋 CRITERIA USED:")
    print("="*70)
    print(f"✅ ONLY ONE CRITERION: Next TOP is within ±{TOLERANCE_PRICE} points (SAME RANGE)")
    print("="*70)
else:
    print("\n❌ No TRUE TOPs found with current criteria.")
    print("Consider adjusting the parameters in the configuration section.")

print("\n✅ Analysis Complete!")
