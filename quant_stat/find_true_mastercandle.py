"""
Find True Master Candle - Identifica la vela maestra que cruza el creek perdices
Criteria for MASTER CANDLE:
1. Candle closes ABOVE the creek line (breakout candle)
2. Candle range > average range of all candles inside the grey square (consolidation zone)
3. Upper tail <= 20% of candle range (small or no upper tail)
   Upper tail = high - close (for green candles) or high - open (for red candles)
"""

import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from config import DATA_DIR

# ====================================================
# 📊 CONFIGURATION
# ====================================================

BASE_DIR = Path(__file__).parent.parent

# Parameters from main.py
date_str = sys.argv[1] if len(sys.argv) > 1 else '2023_03_02'
tolerance = sys.argv[2] if len(sys.argv) > 2 else '2.0'
UPPER_TAIL_MAX_PCT = float(sys.argv[3]) if len(sys.argv) > 3 else 20.0  # Default: 20%

# File paths
CREEK_CSV = BASE_DIR / 'outputs' / 'fractal_tops_and_bottoms' / f'true_tops_creek_perdices_{date_str}_tol_{tolerance}.csv'
CANDLES_CSV = BASE_DIR / 'data' / 'daily_subdata' / f'es_1min_data_{date_str}.csv'
OUTPUT_CSV = BASE_DIR / 'outputs' / 'fractal_tops_and_bottoms' / f'true_tops_creek_perdices_{date_str}_tol_{tolerance}.csv'

# ====================================================
# 📥 LOAD DATA
# ====================================================

print("="*70)
print("🎯 FIND MASTER CANDLE - CREEK PERDICES BREAKOUT ANALYSIS")
print("="*70)
print(f"Upper tail threshold: <= {UPPER_TAIL_MAX_PCT}%")

# Load creek perdices
if not CREEK_CSV.exists():
    print(f"ERROR: Creek perdices CSV not found: {CREEK_CSV}")
    sys.exit(1)

df_creek = pd.read_csv(CREEK_CSV)
df_creek['timestamp'] = pd.to_datetime(df_creek['timestamp'])
df_creek['last_top_timestamp'] = pd.to_datetime(df_creek['last_top_timestamp'])
df_creek['breakout_timestamp'] = pd.to_datetime(df_creek['breakout_timestamp'])

print(f"✅ Loaded {len(df_creek)} creek perdices clusters")

# Load candles
if not CANDLES_CSV.exists():
    print(f"ERROR: Candles file not found: {CANDLES_CSV}")
    sys.exit(1)

df_candles = pd.read_csv(CANDLES_CSV)
df_candles.columns = [col.strip().lower() for col in df_candles.columns]
df_candles['date'] = pd.to_datetime(df_candles['date'])

print(f"✅ Loaded {len(df_candles)} candles")

# ====================================================
# 📊 ANALYSIS: Find Master Candle for each cluster
# ====================================================

print("\n" + "="*70)
print("ANALYSIS: MASTER CANDLE DETECTION")
print("="*70)

# Initialize master candle column
df_creek['mastercandle'] = 'none'
df_creek['mastercandle_timestamp'] = pd.NaT
df_creek['mastercandle_range'] = 0.0
df_creek['mastercandle_avg_range'] = 0.0
df_creek['mastercandle_upper_tail_pct'] = 0.0

master_count = 0

# Process each cluster
for idx, cluster in df_creek.iterrows():
    group = cluster['group']
    first_top_ts = cluster['timestamp']
    last_top_ts = cluster['last_top_timestamp']
    breakout_ts = cluster['breakout_timestamp']
    creek_price = cluster['creek_price']

    print(f"\n📍 Analyzing {group} (Creek: ${creek_price:.2f})")

    # Get candles in the consolidation zone (grey square: from first TOP to breakout)
    consolidation_candles = df_candles[
        (df_candles['date'] >= first_top_ts) &
        (df_candles['date'] <= breakout_ts)
    ].copy()

    if len(consolidation_candles) == 0:
        print(f"   ⚠️ No candles found in consolidation zone")
        continue

    # Calculate average range of candles in consolidation zone
    consolidation_candles['range'] = consolidation_candles['high'] - consolidation_candles['low']
    avg_range = consolidation_candles['range'].mean()

    print(f"   📊 Consolidation candles: {len(consolidation_candles)}")
    print(f"   📏 Average range: ${avg_range:.2f}")

    # CRITICAL: Only evaluate the ACTUAL breakout candle (not all candles in zone)
    # The breakout_timestamp from creek CSV is already the first candle that closed above creek
    breakout_candle_match = df_candles[df_candles['date'] == breakout_ts]

    if len(breakout_candle_match) == 0:
        print(f"   ❌ Breakout candle not found at timestamp {breakout_ts}")
        continue

    candle = breakout_candle_match.iloc[0]
    candle_range = candle['high'] - candle['low']
    candle_close = candle['close']

    print(f"   🎯 Evaluating breakout candle at {breakout_ts}")
    print(f"      Close: ${candle_close:.2f} | Creek: ${creek_price:.2f}")

    # CRITICAL: Verify the breakout candle actually closes above creek
    if candle_close <= creek_price:
        print(f"   ❌ Breakout candle closes at ${candle_close:.2f} which is NOT above creek ${creek_price:.2f}")
        print(f"      This indicates an issue in find_true_tops.py - skipping this cluster")
        continue

    # Determine candle color
    is_green = candle['close'] >= candle['open']

    # Calculate upper tail based on candle color
    if is_green:
        upper_tail = candle['high'] - candle['close']
    else:
        upper_tail = candle['high'] - candle['open']

    # Calculate upper tail percentage
    if candle_range > 0:
        upper_tail_pct = (upper_tail / candle_range) * 100
    else:
        upper_tail_pct = 0

    # Check criteria:
    # 0. Close MUST be above creek (already verified above)
    # 1. Range > average range
    # 2. Upper tail <= UPPER_TAIL_MAX_PCT% of range
    criteria_1 = candle_range > avg_range
    criteria_2 = upper_tail_pct <= UPPER_TAIL_MAX_PCT

    print(f"      Range: ${candle_range:.2f} (avg: ${avg_range:.2f}) | Tail: {upper_tail_pct:.1f}%")
    print(f"      Criteria: Range>{avg_range:.2f}? {criteria_1} | Tail<{UPPER_TAIL_MAX_PCT}%? {criteria_2}")

    master_found = False

    if criteria_1 and criteria_2:
        # MASTER CANDLE FOUND!
        df_creek.at[idx, 'mastercandle'] = 'master'
        df_creek.at[idx, 'mastercandle_timestamp'] = pd.Timestamp(candle['date'])
        df_creek.at[idx, 'mastercandle_range'] = round(candle_range, 2)
        df_creek.at[idx, 'mastercandle_avg_range'] = round(avg_range, 2)
        df_creek.at[idx, 'mastercandle_upper_tail_pct'] = round(upper_tail_pct, 1)
        df_creek.at[idx, 'mastercandle_close'] = round(candle_close, 2)
        master_found = True
        master_count += 1
        print(f"      ⭐ MASTER CANDLE FOUND! Close ${candle_close:.2f} > Creek ${creek_price:.2f}")
    else:
        print(f"      ❌ Criteria not met - NOT a master candle")

# ====================================================
# 💾 SAVE RESULTS
# ====================================================

# Save updated CSV
df_creek.to_csv(OUTPUT_CSV, index=False)
print(f"\n💾 CSV updated: {OUTPUT_CSV}")

# ====================================================
# 📊 DISPLAY RESULTS
# ====================================================

print("\n" + "="*70)
print("🎯 MASTER CANDLE DETECTION RESULTS")
print("="*70)
print(f"\n✅ Found {master_count} MASTER CANDLES (out of {len(df_creek)} clusters)")

if master_count > 0:
    master_clusters = df_creek[df_creek['mastercandle'] == 'master']
    print(f"\n{'Group':<12} | {'Master Timestamp':<20} | {'Close':<8} | {'Creek':<8} | {'Range':<8} | {'Avg Range':<10} | {'Tail %':<8}")
    print("-" * 100)
    for idx, cluster in master_clusters.iterrows():
        close_val = cluster.get('mastercandle_close', 0.0)
        print(f"{cluster['group']:<12} | {str(cluster['mastercandle_timestamp']):<20} | ${close_val:<7.2f} | ${cluster['creek_price']:<7.2f} | ${cluster['mastercandle_range']:<7.2f} | ${cluster['mastercandle_avg_range']:<9.2f} | {cluster['mastercandle_upper_tail_pct']:<7.1f}%")

    print("\n" + "="*70)
    print("📋 CRITERIA USED:")
    print("="*70)
    print("✅ 0. Candle CLOSE must be ABOVE creek line (CRITICAL)")
    print("✅ 1. Candle range > average range of consolidation zone")
    print(f"✅ 2. Upper tail <= {UPPER_TAIL_MAX_PCT}% of candle range")
    print("="*70)
else:
    print("\n❌ No MASTER CANDLES found with current criteria.")

print("\n✅ Master Candle Analysis Complete!")
