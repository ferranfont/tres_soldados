"""
Main Orchestrator for Strategy 1: Creek Crossover Above VWAP
=============================================================

This script iterates through multiple dates and executes Strategy 1 for each date.
Results are saved to individual trading records and appended to the summary file.

Usage:
    python main_OM_strat1.py

Configuration:
    - Edit the DATES list below to add/remove dates to analyze
    - Edit TOLERANCE to change creek clustering tolerance

Output:
    - Individual trading records: outputs/tracking_records/trading_record_strat1_crossover_{date}.csv
    - Summary file (appended): outputs/tracking_records/tracking_record_SUMMARY_strat1_crossover.csv
    - HTML reports: outputs/tablas_html/trading_report_strat1_crossover_{date}.html
    - Charts: charts/close_vol_chart_ES_1min_{date}.html

Example DATES list:
    DATES = [
        '2023_03_01',
        '2023_03_02',
        '2023_03_06',
        '2023_03_07',
        # Add more dates here...
    ]

Note: Data files must exist in data/daily_subdata/es_1min_data_{date}.csv
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# ====================================================
# ⚙️ CONFIGURATION
# ====================================================

# Option 1: Load dates from CSV file (recommended for large date ranges)
USE_CSV = False  # Set to True to load all dates from data/unique_days_universe.csv

BASE_DIR = Path(__file__).parent

if USE_CSV:
    # Load all dates from CSV
    df_dates = pd.read_csv(BASE_DIR / 'data' / 'unique_days_universe.csv')
    DATES = df_dates['date'].tolist()
    print(f"📅 Loaded {len(DATES)} dates from unique_days_universe.csv")
else:
    # Option 2: Manual list (for specific dates or testing)
    DATES = [
        '2023_03_01',
        '2023_03_02',
        '2023_03_03',
        '2023_03_06',
        '2023_03_07',
        '2023_03_08',
        '2023_03_09',
        '2023_03_10',
        '2023_03_13',
        # Add more dates manually, or set USE_CSV = True above to load all 2679 dates
    ]

# Tolerance for creek perdices clustering (in points)
TOLERANCE = 2.0

# ====================================================
# 🚀 EXECUTION
# ====================================================

STRAT_SCRIPT = BASE_DIR / 'strat_OM' / 'strat_1_crossover_creek.py'

print("="*70)
print("🚀 MAIN ORCHESTRATOR: STRATEGY 1 - CREEK CROSSOVER ABOVE VWAP")
print("="*70)
print(f"Total dates to process: {len(DATES)}")
print(f"Tolerance: {TOLERANCE}")
print(f"Strategy script: {STRAT_SCRIPT}")
print("="*70)

# Track overall statistics
total_executions = 0
successful_executions = 0
failed_executions = 0
failed_dates = []

start_time = datetime.now()

# Iterate through each date
for idx, date_str in enumerate(DATES, 1):
    print(f"\n{'='*70}")
    print(f"📅 Processing date {idx}/{len(DATES)}: {date_str}")
    print(f"{'='*70}")

    try:
        # Execute strategy script with date and tolerance arguments
        result = subprocess.run(
            [sys.executable, str(STRAT_SCRIPT), date_str, str(TOLERANCE)],
            check=True,
            capture_output=False,  # Show output in real-time
            text=True
        )

        print(f"\n✅ Successfully completed: {date_str}")
        successful_executions += 1

    except subprocess.CalledProcessError as e:
        print(f"\n❌ Failed to execute: {date_str}")
        print(f"Error: {e}")
        failed_executions += 1
        failed_dates.append(date_str)

    except Exception as e:
        print(f"\n❌ Unexpected error for {date_str}: {e}")
        failed_executions += 1
        failed_dates.append(date_str)

    total_executions += 1

end_time = datetime.now()
duration = (end_time - start_time).total_seconds()

# ====================================================
# 📊 FINAL SUMMARY
# ====================================================

print("\n" + "="*70)
print("📊 BATCH EXECUTION SUMMARY")
print("="*70)
print(f"Total executions: {total_executions}")
print(f"Successful: {successful_executions}")
print(f"Failed: {failed_executions}")
print(f"Duration: {duration:.2f} seconds ({duration/60:.2f} minutes)")

if failed_dates:
    print("\n❌ Failed dates:")
    for date in failed_dates:
        print(f"  - {date}")
else:
    print("\n✅ All dates processed successfully!")

print("\n📈 Summary file location:")
print(f"  {BASE_DIR / 'outputs' / 'tracking_records' / 'tracking_record_SUMMARY_strat1_crossover.csv'}")

print("\n💾 Individual trading records location:")
print(f"  {BASE_DIR / 'outputs' / 'tracking_records' / 'trading_record_strat1_crossover_*.csv'}")

print("="*70)
print("✅ Batch execution complete!")
print("="*70)
