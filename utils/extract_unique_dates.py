"""
Extract Unique Dates from ES Data
==================================

This script extracts unique dates from the datetime column in es_1min_data_2015_2025.csv
and stores them in a CSV file in the data folder.

Usage:
    python utils/extract_unique_dates.py

Input:
    - data/es_1min_data_2015_2025.csv (source data with datetime column)

Output:
    - data/unique_days_universe.csv (CSV with unique dates in YYYY_MM_DD format)
      Single column: date (ready to use in DATES list)
"""

import pandas as pd
from pathlib import Path
import sys

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# ====================================================
# 📊 CONFIGURATION
# ====================================================

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / 'data' / 'es_1min_data_2015_2025.csv'
OUTPUT_FILE = BASE_DIR / 'data' / 'unique_days_universe.csv'

# ====================================================
# 🚀 EXECUTION
# ====================================================

print("="*70)
print("📅 EXTRACTING UNIQUE DATES FROM ES DATA")
print("="*70)
print(f"Source file: {DATA_FILE}")
print(f"Output file: {OUTPUT_FILE}")
print("="*70)

# Read the CSV file (only the date column for efficiency)
print("\n📖 Reading data file...")
df = pd.read_csv(DATA_FILE, usecols=['date'])

print(f"✅ Loaded {len(df):,} rows")

# Convert to datetime
print("\n🔄 Converting to datetime and extracting dates...")
df['date'] = pd.to_datetime(df['date'], utc=True)

# Extract only the date portion (without time)
df['date_only'] = df['date'].dt.date

# Get unique dates
unique_dates = sorted(df['date_only'].unique())

print(f"✅ Found {len(unique_dates)} unique dates")
print(f"   First date: {unique_dates[0]}")
print(f"   Last date: {unique_dates[-1]}")

# ====================================================
# 💾 SAVE RESULTS
# ====================================================

print("\n💾 Saving unique dates to CSV file...")

# Create DataFrame with dates in YYYY_MM_DD format (ready to use)
dates_formatted = [str(d).replace('-', '_') for d in unique_dates]
df_output = pd.DataFrame({
    'date': dates_formatted
})

# Save to CSV
df_output.to_csv(OUTPUT_FILE, index=False)

print(f"✅ Saved to: {OUTPUT_FILE}")
print(f"   Total dates: {len(unique_dates)}")
print(f"   Format: YYYY_MM_DD (ready to use in DATES list)")

# ====================================================
# 📊 DISPLAY RESULTS
# ====================================================

print("\n" + "="*70)
print("📊 UNIQUE DATES LIST")
print("="*70)

# Display first 20 dates
print("\nFirst 20 dates:")
for i, date in enumerate(unique_dates[:20], 1):
    print(f"  {i:2d}. {date}")

if len(unique_dates) > 40:
    print("\n  ... ({} more dates) ...".format(len(unique_dates) - 40))

# Display last 20 dates
if len(unique_dates) > 20:
    print("\nLast 20 dates:")
    for i, date in enumerate(unique_dates[-20:], len(unique_dates) - 19):
        print(f"  {i:2d}. {date}")

print("\n" + "="*70)
print("✅ Extraction complete!")
print("="*70)

# ====================================================
# 📋 PYTHON LIST FORMAT (for copy-paste)
# ====================================================

print("\n" + "="*70)
print("📋 PYTHON LIST FORMAT (for main_OM_strat1.py)")
print("="*70)
print("\nCopy this list to your script:")
print("-"*70)
print("DATES = [")

# Convert to YYYY_MM_DD format for consistency with existing code
for date in unique_dates[:10]:  # Show first 10 as example
    date_str = str(date).replace('-', '_')
    print(f"    '{date_str}',")

if len(unique_dates) > 10:
    print(f"    # ... ({len(unique_dates) - 10} more dates)")

print("]")
print("-"*70)
print(f"\n💡 Tip: Full list saved in {OUTPUT_FILE.name}")
print("="*70)
