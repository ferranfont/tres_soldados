

import sys
import os
import pandas as pd
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from quant_stat.find_tops_and_bottoms import main as detect_fractals
from plot_minute_data import plot_minute_data
from config import DATA_DIR, SYMBOL


# ====================================================
# 📊 CONFIGURATION
# ====================================================

# Data file to analyze (must be in data/ folder) - create it before running this script
DATA_FILE = 'es_1min_data_2023_03_02.csv'
# Zigzag detection sensitivity
CHANGE_PCT = 0.10  # 0.10% minimum change,  try 0.05 for more sensitivity.
# Creek perdices clustering tolerance
TOLERANCE_PRICE = 2.0  # ±2.0 points tolerance for clustering TOPs
# Plot chart after detection?
PLOT_CHART = True  # Set to False to skip plotting


# ====================================================
# 🚀 EXECUTION
# ====================================================

if __name__ == "__main__":
    print("="*70)
    print("TRES SOLDADOS - FRACTAL DETECTION MAIN")
    print("="*70)
    print(f"Data file: {DATA_FILE}")
    print(f"Zigzag sensitivity: {CHANGE_PCT}%")
    print(f"Plot chart: {'Yes' if PLOT_CHART else 'No'}")
    print("="*70)

    # Run fractal detection
    fractals = detect_fractals(
        change_pct=CHANGE_PCT,
        data_filename=DATA_FILE
    )

    if fractals:
        print(f"\n{'='*70}")
        print(f"SUCCESS: {len(fractals)} fractals detected and saved to outputs/")
        print(f"{'='*70}")

        # Run Creek Perdices detection (TRUE TOPs clustering)
        print(f"\n{'='*70}")
        print("DETECTING TRUE TOPS - CREEK PERDICES...")
        print(f"{'='*70}")

        import subprocess
        # Extract date from DATA_FILE to pass to find_true_tops.py
        date_str = DATA_FILE.replace('es_1min_data_', '').replace('.csv', '')
        result = subprocess.run(
            [sys.executable, "-X", "utf8", "quant_stat/find_true_tops.py", str(TOLERANCE_PRICE), date_str],
            cwd=str(Path(__file__).parent),
            capture_output=False
        )

        if result.returncode == 0:
            # Build the correct filename with date and tolerance
            date_str = DATA_FILE.replace('es_1min_data_', '').replace('.csv', '')
            creek_csv = f"outputs/true_tops_creek_perdices_{date_str}_tol_{TOLERANCE_PRICE}.csv"

            print(f"\n{'='*70}")
            print("SUCCESS: Creek Perdices detection completed")
            print(f"Results saved to: {creek_csv}")
            print(f"{'='*70}")
        else:
            print(f"\n{'='*70}")
            print("WARNING: Creek Perdices detection failed")
            print(f"{'='*70}")

        # Plot chart if enabled (AFTER creek perdices detection)
        if PLOT_CHART:
            print(f"\n{'='*70}")
            print("PLOTTING CHART WITH FRACTALS & CREEK PERDICES...")
            print(f"{'='*70}")

            # Load data
            file_path = os.path.join(str(DATA_DIR), DATA_FILE)
            df = pd.read_csv(file_path)

            # Normalize columns
            df.columns = [col.strip().lower() for col in df.columns]
            df = df.rename(columns={'volumen': 'volume'})

            # Ensure datetime format
            df['date'] = pd.to_datetime(df['date'], utc=True)

            # Extract date from filename for timeframe
            date_str = DATA_FILE.replace('es_1min_data_', '').replace('.csv', '')
            timeframe = f'1min_{date_str}'

            # Plot chart
            print(f"\nGenerating chart for {date_str}...")
            plot_minute_data(SYMBOL, timeframe, df)

            print(f"\nChart generated: charts/{SYMBOL}_{timeframe}.html")

    else:
        print(f"\n{'='*70}")
        print("WARNING: No fractals detected. Try lowering CHANGE_PCT.")
        print(f"{'='*70}")