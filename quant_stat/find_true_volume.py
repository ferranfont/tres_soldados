"""
Find True Volume - Identifica las velas con mayor volumen en la zona de consolidación
Criteria for TRUE VOLUME:
1. Volume >= 1.5x average volume in the consolidation zone (grey square)
2. Maximum 3 candles per cluster (true_volume1, true_volume2, true_volume3)
3. Ordered by volume (highest to lowest)
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
VOL_MULTIPL = float(sys.argv[3]) if len(sys.argv) > 3 else 1.5  # Default: 1.5x average volume
VOL_PERCENTILE = int(sys.argv[4]) if len(sys.argv) > 4 else 70  # Default: 70th percentile

# File paths
CREEK_CSV = BASE_DIR / 'outputs' / f'true_tops_creek_perdices_{date_str}_tol_{tolerance}.csv'
CANDLES_CSV = BASE_DIR / 'data' / f'es_1min_data_{date_str}.csv'
OUTPUT_CSV = BASE_DIR / 'outputs' / f'true_tops_creek_perdices_{date_str}_tol_{tolerance}.csv'

# ====================================================
# 📥 LOAD DATA
# ====================================================

print("="*70)
print("🎯 FIND TRUE VOLUME - CONSOLIDATION VOLUME ANALYSIS")
print("="*70)
print(f"Volume threshold: {VOL_MULTIPL}x average volume")
print(f"Position filter: {VOL_PERCENTILE}th percentile")

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
# 📊 ANALYSIS: Find True Volume for each cluster
# ====================================================

print("\n" + "="*70)
print("ANALYSIS: TRUE VOLUME DETECTION")
print("="*70)

# Initialize true volume columns
df_creek['true_volume1_time'] = pd.NaT
df_creek['true_volume1_value'] = 0.0
df_creek['true_volume2_time'] = pd.NaT
df_creek['true_volume2_value'] = 0.0
df_creek['true_volume3_time'] = pd.NaT
df_creek['true_volume3_value'] = 0.0

total_volumes_found = 0

# Process each cluster
for idx, cluster in df_creek.iterrows():
    group = cluster['group']
    first_top_ts = cluster['timestamp']
    breakout_ts = cluster['breakout_timestamp']

    print(f"\n📍 Analyzing {group}")

    # Get candles in the consolidation zone (grey square: from first TOP to breakout)
    consolidation_candles = df_candles[
        (df_candles['date'] >= first_top_ts) &
        (df_candles['date'] <= breakout_ts)
    ].copy()

    if len(consolidation_candles) == 0:
        print(f"   ⚠️ No candles found in consolidation zone")
        continue

    # STEP 1: Calculate percentile threshold FIRST
    # Use the actual percentile of CLOSE prices (not range-based)
    percentile_threshold = consolidation_candles['close'].quantile(VOL_PERCENTILE / 100.0)

    lowest_low = consolidation_candles['low'].min()
    highest_high = consolidation_candles['high'].max()

    print(f"   📊 Consolidation candles: {len(consolidation_candles)}")
    print(f"   📐 Price range: ${lowest_low:.2f} to ${highest_high:.2f}")
    print(f"   📐 {VOL_PERCENTILE}th percentile of CLOSE prices: ${percentile_threshold:.2f}")

    # STEP 2: Filter by position FIRST - keep only candles in lower percentile OR breakout candle
    position_filtered = consolidation_candles[
        (consolidation_candles['close'] <= percentile_threshold) |
        (consolidation_candles['date'] == breakout_ts)
    ].copy()

    print(f"   ✅ After position filter (lower {VOL_PERCENTILE}% + master): {len(position_filtered)} candles")

    if len(position_filtered) == 0:
        print(f"   ❌ No candles in lower {VOL_PERCENTILE}% of range")
        continue

    # STEP 3: Calculate average volume from ALL consolidation candles
    avg_volume = consolidation_candles['volume'].mean()
    volume_threshold = avg_volume * VOL_MULTIPL

    print(f"   📏 Average volume (all candles): {avg_volume:,.0f}")
    print(f"   🎯 Volume threshold (>= {VOL_MULTIPL}x): {volume_threshold:,.0f}")

    # STEP 4: From position-filtered candles, find those with high volume
    high_volume_candles = position_filtered[
        position_filtered['volume'] >= volume_threshold
    ].copy()

    if len(high_volume_candles) == 0:
        print(f"   ❌ No candles with volume >= {VOL_MULTIPL}x average in lower {VOL_PERCENTILE}%")
        continue

    print(f"   ✅ Found {len(high_volume_candles)} high volume candles")

    # Display each candidate
    for candle_idx, candle in high_volume_candles.iterrows():
        candle_close = candle['close']
        candle_time = candle['date']
        candle_volume = candle['volume']
        is_breakout = (candle_time == breakout_ts)
        volume_ratio = candle_volume / avg_volume

        if is_breakout:
            print(f"      • {candle_time} | MASTER | Vol: {candle_volume:,.0f} ({volume_ratio:.2f}x)")
        else:
            print(f"      • {candle_time} | Close: ${candle_close:.2f} | Vol: {candle_volume:,.0f} ({volume_ratio:.2f}x)")

    # STEP 5: Sort by volume (descending) and take top 3
    filtered_candles = high_volume_candles.sort_values('volume', ascending=False).head(3)

    print(f"   ✅ Selected top {len(filtered_candles)} by volume")

    # Assign to true_volume1, true_volume2, true_volume3
    for vol_idx, (candle_idx, candle) in enumerate(filtered_candles.iterrows()):
        vol_num = vol_idx + 1  # 1, 2, or 3
        candle_time = candle['date']
        candle_volume = candle['volume']
        volume_ratio = candle_volume / avg_volume

        print(f"      #{vol_num}: {candle_time} | Vol: {candle_volume:,.0f} ({volume_ratio:.2f}x avg)")

        # Store in dataframe
        df_creek.at[idx, f'true_volume{vol_num}_time'] = pd.Timestamp(candle_time)
        df_creek.at[idx, f'true_volume{vol_num}_value'] = candle_volume
        total_volumes_found += 1

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
print("🎯 TRUE VOLUME DETECTION RESULTS")
print("="*70)

# Count clusters with at least one high volume candle
clusters_with_volume = df_creek[df_creek['true_volume1_value'] > 0]
print(f"\n✅ Found {len(clusters_with_volume)} clusters with high volume candles")
print(f"📊 Total high volume candles identified: {total_volumes_found}")

if len(clusters_with_volume) > 0:
    print(f"\n{'Group':<12} | {'Vol1 Time':<20} | {'Vol1':<10} | {'Vol2 Time':<20} | {'Vol2':<10} | {'Vol3 Time':<20} | {'Vol3':<10}")
    print("-" * 130)
    for idx, cluster in clusters_with_volume.iterrows():
        vol1_time = cluster['true_volume1_time'] if pd.notna(cluster['true_volume1_time']) else 'N/A'
        vol1_val = f"{cluster['true_volume1_value']:,.0f}" if cluster['true_volume1_value'] > 0 else 'N/A'
        vol2_time = cluster['true_volume2_time'] if pd.notna(cluster['true_volume2_time']) else 'N/A'
        vol2_val = f"{cluster['true_volume2_value']:,.0f}" if cluster['true_volume2_value'] > 0 else 'N/A'
        vol3_time = cluster['true_volume3_time'] if pd.notna(cluster['true_volume3_time']) else 'N/A'
        vol3_val = f"{cluster['true_volume3_value']:,.0f}" if cluster['true_volume3_value'] > 0 else 'N/A'

        print(f"{cluster['group']:<12} | {str(vol1_time):<20} | {vol1_val:<10} | {str(vol2_time):<20} | {vol2_val:<10} | {str(vol3_time):<20} | {vol3_val:<10}")

    print("\n" + "="*70)
    print("📋 CRITERIA USED:")
    print("="*70)
    print(f"✅ 1. Volume >= {VOL_MULTIPL}x average volume in consolidation zone")
    print(f"✅ 2. Candle close <= {VOL_PERCENTILE}th percentile (lower {VOL_PERCENTILE}% of range)")
    print(f"✅ 3. Exception: Master candle (breakout) always included")
    print(f"✅ 4. Maximum 3 candles per cluster (highest volume)")
    print("="*70)
else:
    print("\n❌ No high volume candles found with current criteria.")

print("\n✅ Volume Analysis Complete!")
