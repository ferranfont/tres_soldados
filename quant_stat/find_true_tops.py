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
FRACTALS_CSV = BASE_DIR / 'outputs' / 'fractals_es_1min_data_2023_03_02_zigzag_0.1.csv'
CANDLES_CSV = BASE_DIR / 'data' / 'es_1min_data_2023_03_02.csv'
OUTPUT_CSV = BASE_DIR / 'outputs' / 'true_tops_creek_perdices.csv'

# Analysis parameters
TOLERANCE_PRICE = 2.0  # Price tolerance for "same level" detection (points)

# ====================================================
# 📥 LOAD DATA
# ====================================================

print("="*70)
print("🎯 FIND TRUE TOPS - CREEK PERDICES DETECTION")
print("="*70)

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

    analysis_results.append({
        'group': cluster['group'],
        'top_index': cluster['indices'][0],
        'timestamp': first_top['timestamp'],
        'price': first_top['price'],
        'next_top_price': last_top['price'],
        'price_diff_next': round(abs(last_top['price'] - first_top['price']), 2),
        'is_same_range': True,
        'cluster_size': len(cluster['indices']),
        'first_top_idx': cluster['indices'][0],
        'last_top_idx': cluster['indices'][-1],
        'last_top_timestamp': last_top['timestamp']
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
    print(f"\n{'Group':<12} | {'Size':<5} | {'First TOP':<20} | {'Price':<10} | {'Last TOP':<20} | {'Last Price':<10} | {'Diff':<8}")
    print("-" * 110)
    for idx, top in df_true_tops.iterrows():
        print(f"{top['group']:<12} | {top['cluster_size']:<5} | {str(top['timestamp']):<20} | ${top['price']:<9.2f} | {str(top['last_top_timestamp']):<20} | ${top['next_top_price']:<9.2f} | ${top['price_diff_next']:.2f}")

    print("\n" + "="*70)
    print("📋 CRITERIA USED:")
    print("="*70)
    print(f"✅ ONLY ONE CRITERION: Next TOP is within ±{TOLERANCE_PRICE} points (SAME RANGE)")
    print("="*70)
else:
    print("\n❌ No TRUE TOPs found with current criteria.")
    print("Consider adjusting the parameters in the configuration section.")

print("\n✅ Analysis Complete!")
