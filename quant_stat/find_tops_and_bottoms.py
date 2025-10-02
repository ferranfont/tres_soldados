"""
Find Tops and Bottoms - ES Futures Fractal Detection
Uses Zigzag method to detect significant tops and bottoms in price data
"""

import pandas as pd
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from config import DATA_DIR, SYMBOL
from quant_stat.fractal_detector import UnifiedZigzagDetector, FractalType


def load_es_data(filename: str) -> pd.DataFrame:
    """Load ES minute data from file"""
    # Try daily_subdata subfolder first, then root data folder
    file_path_daily = os.path.join(str(DATA_DIR), 'daily_subdata', filename)
    file_path_root = os.path.join(str(DATA_DIR), filename)

    if os.path.exists(file_path_daily):
        file_path = file_path_daily
    elif os.path.exists(file_path_root):
        file_path = file_path_root
    else:
        file_path = file_path_root  # Will raise error below

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Data file not found: {file_path}")

    df = pd.read_csv(file_path)

    # Normalize columns
    df.columns = [col.strip().lower() for col in df.columns]

    print(f"✅ Loaded {len(df)} records from {filename}")
    print(f"📊 Columns: {list(df.columns)}")

    # Show date range
    if 'date' in df.columns:
        print(f"📅 Date range: {df['date'].iloc[0]} to {df['date'].iloc[-1]}")

    return df


def classify_swing_size(distance_usd: float, distance_bars: int) -> str:
    """
    Classify swing size based on price movement and time duration

    Args:
        distance_usd: Price movement in dollars
        distance_bars: Number of bars between fractals

    Returns:
        Classification: 'big', 'small', or 'noise'
    """
    # ES futures typical swing classification
    # Adjust these thresholds based on market volatility

    if distance_usd >= 15.0:  # Large price moves
        return "big"
    elif distance_usd >= 5.0:  # Medium price moves
        return "small"
    else:  # Small price moves
        return "noise"


def detect_fractals_zigzag(df: pd.DataFrame, min_change_pct: float = 0.10) -> list:
    """
    Detect fractals using Zigzag method

    Args:
        df: DataFrame with OHLC data
        min_change_pct: Minimum percentage change to detect pivot (default 0.10%)

    Returns:
        List of detected fractals with all metadata
    """
    print(f"\n🔍 Detecting fractals with Zigzag method (min_change: {min_change_pct}%)")

    detector = UnifiedZigzagDetector(min_change_pct=min_change_pct)
    fractals = []

    for idx, row in df.iterrows():
        # Build timestamp
        if 'date' in df.columns and 'time' in df.columns:
            timestamp = f"{row['date']} {row['time']}"
        elif 'date' in df.columns:
            timestamp = str(row['date'])
        else:
            timestamp = f"Bar {idx}"

        # Detect pivot
        pivot = detector.add_candle(
            high=row['high'],
            low=row['low'],
            index=idx,
            timestamp=timestamp
        )

        if pivot:
            fractal_type = "TOP" if pivot.direction.value == "up" else "BOTTOM"

            # Calculate distance from previous fractal
            distance_usd = 0.0
            distance_bars = 0
            distance_ratio = 0.0
            swing_size = "noise"

            if len(fractals) > 0:
                prev_fractal = fractals[-1]
                distance_usd = round(abs(pivot.price - prev_fractal['price']), 2)
                distance_bars = pivot.index - prev_fractal['index']

                # Calculate ratio: (distance_usd * 100) / distance_bars
                if distance_bars > 0:
                    distance_ratio = round((distance_usd * 100) / distance_bars, 2)

                # Classify swing size
                swing_size = classify_swing_size(distance_usd, distance_bars)

            fractals.append({
                'index': pivot.index,
                'timestamp': pivot.timestamp,
                'price': round(pivot.price, 2),
                'type': fractal_type,
                'distance_usd': distance_usd,
                'distance_bars': distance_bars,
                'distance_ratio': distance_ratio,
                'swing_size': swing_size
            })

            print(f"  ➤ {fractal_type} at {pivot.timestamp} - ${pivot.price:.2f} - Swing: {swing_size}")

    return fractals


def save_fractals_to_csv(fractals: list, output_filename: str) -> str:
    """
    Save detected fractals to CSV file

    Args:
        fractals: List of fractal dictionaries
        output_filename: Name of output file

    Returns:
        Path to saved file
    """
    # Create outputs/fractal_tops_and_bottoms directory if it doesn't exist
    output_dir = os.path.join("outputs", "fractal_tops_and_bottoms")
    os.makedirs(output_dir, exist_ok=True)

    # Convert to DataFrame
    df_fractals = pd.DataFrame(fractals)

    # Calculate 3-period moving average of distance_ratio
    if 'distance_ratio' in df_fractals.columns and len(df_fractals) > 0:
        df_fractals['dist_ratio_avg'] = df_fractals['distance_ratio'].rolling(
            window=3, min_periods=1
        ).mean().round(2)

    # Save to CSV
    output_path = os.path.join(output_dir, output_filename)
    df_fractals.to_csv(output_path, index=False)

    print(f"\n💾 Fractals saved to: {output_path}")
    return output_path


def analyze_fractals(fractals: list) -> dict:
    """
    Analyze detected fractals and return statistics

    Args:
        fractals: List of fractal dictionaries

    Returns:
        Dictionary with analysis statistics
    """
    if not fractals:
        return {
            "total": 0, "tops": 0, "bottoms": 0,
            "top_percentage": 0, "bottom_percentage": 0,
            "highest_top": 0, "lowest_bottom": 0,
            "price_range": 0, "avg_top_price": 0, "avg_bottom_price": 0
        }

    df_fractals = pd.DataFrame(fractals)

    total_fractals = len(fractals)
    tops = len(df_fractals[df_fractals['type'] == 'TOP'])
    bottoms = len(df_fractals[df_fractals['type'] == 'BOTTOM'])

    # Price statistics
    prices = [f['price'] for f in fractals]
    top_prices = [f['price'] for f in fractals if f['type'] == 'TOP']
    bottom_prices = [f['price'] for f in fractals if f['type'] == 'BOTTOM']

    stats = {
        'total': total_fractals,
        'tops': tops,
        'bottoms': bottoms,
        'top_percentage': round((tops / total_fractals * 100), 1) if total_fractals > 0 else 0,
        'bottom_percentage': round((bottoms / total_fractals * 100), 1) if total_fractals > 0 else 0,
        'highest_top': max(top_prices) if top_prices else 0,
        'lowest_bottom': min(bottom_prices) if bottom_prices else 0,
        'price_range': round(max(prices) - min(prices), 2) if prices else 0,
        'avg_top_price': round(sum(top_prices) / len(top_prices), 2) if top_prices else 0,
        'avg_bottom_price': round(sum(bottom_prices) / len(bottom_prices), 2) if bottom_prices else 0
    }

    return stats


def print_fractal_summary(fractals: list):
    """Print formatted summary of detected fractals"""
    stats = analyze_fractals(fractals)

    print(f"\n{'='*70}")
    print(f"📊 FRACTAL ANALYSIS SUMMARY - ZIGZAG METHOD")
    print(f"{'='*70}")
    print(f"Total Fractals Detected: {stats['total']}")
    print(f"  Tops:               {stats['tops']} ({stats['top_percentage']}%)")
    print(f"  Bottoms:            {stats['bottoms']} ({stats['bottom_percentage']}%)")
    print(f"\n💰 Price Analysis:")
    print(f"  Highest Top:      ${stats['highest_top']:.2f}")
    print(f"  Lowest Bottom:    ${stats['lowest_bottom']:.2f}")
    print(f"  Price Range:      ${stats['price_range']:.2f}")
    print(f"  Avg Top Price:    ${stats['avg_top_price']:.2f}")
    print(f"  Avg Bottom Price: ${stats['avg_bottom_price']:.2f}")

    if fractals:
        df_fractals = pd.DataFrame(fractals)
        first_fractal = df_fractals.iloc[0]
        last_fractal = df_fractals.iloc[-1]
        print(f"\n⏰ Timing Analysis:")
        print(f"  First Fractal: {first_fractal['type']} at {first_fractal['timestamp']} (${first_fractal['price']:.2f})")
        print(f"  Last Fractal:  {last_fractal['type']} at {last_fractal['timestamp']} (${last_fractal['price']:.2f})")

        # Swing size analysis
        print_swing_analysis(fractals)

    print(f"{'='*70}")


def print_swing_analysis(fractals: list):
    """Print detailed analysis of swing sizes"""
    if not fractals:
        return

    df_fractals = pd.DataFrame(fractals)

    # Count swing sizes
    swing_counts = df_fractals['swing_size'].value_counts()

    print(f"\n📈 SWING SIZE ANALYSIS:")
    print(f"{'-'*70}")
    for swing_type in ['big', 'small', 'noise']:
        count = swing_counts.get(swing_type, 0)
        percentage = (count / len(fractals) * 100) if len(fractals) > 0 else 0
        print(f"  {swing_type.upper():8} swings: {count:3d} ({percentage:5.1f}%)")

    # Detailed analysis of BIG moves
    big_swings = df_fractals[df_fractals['swing_size'] == 'big']

    if len(big_swings) > 0:
        print(f"\n🎯 BIG MOVES DETAILS:")
        print(f"{'-'*90}")
        print(f"{'#':<3} {'Time':<20} {'Type':<7} {'Price':<10} {'Move $':<10} {'Bars':<7} {'Ratio':<8}")
        print(f"{'-'*90}")

        for i, (idx, swing) in enumerate(big_swings.iterrows(), 1):
            print(f"{i:<3} {swing['timestamp']:<20} {swing['type']:<7} "
                  f"${swing['price']:<9.2f} ${swing['distance_usd']:<9.2f} "
                  f"{swing['distance_bars']:<7} {swing['distance_ratio']:<8.2f}")

        # Summary stats
        total_big_move = big_swings['distance_usd'].sum()
        avg_big_move = big_swings['distance_usd'].mean()
        max_big_move = big_swings['distance_usd'].max()
        avg_bars = big_swings['distance_bars'].mean()

        print(f"{'-'*90}")
        print(f"BIG MOVES SUMMARY:")
        print(f"  Total Movement:   ${total_big_move:.2f}")
        print(f"  Average Move:     ${avg_big_move:.2f}")
        print(f"  Largest Move:     ${max_big_move:.2f}")
        print(f"  Average Duration: {avg_bars:.1f} bars")
    else:
        print(f"\n⚠️  No BIG moves detected (threshold: ≥$15.00)")


def print_detailed_fractals(fractals: list, max_display: int = 20):
    """Print detailed list of detected fractals"""
    if not fractals:
        print("❌ No fractals detected.")
        return

    df_fractals = pd.DataFrame(fractals)

    # Calculate 3-period MA if not present
    if 'distance_ratio' in df_fractals.columns and 'dist_ratio_avg' not in df_fractals.columns:
        df_fractals['dist_ratio_avg'] = df_fractals['distance_ratio'].rolling(
            window=3, min_periods=1
        ).mean().round(2)

    print(f"\n📋 DETAILED FRACTAL LIST (showing first {min(max_display, len(fractals))} of {len(fractals)}):")
    print(f"{'='*140}")
    print(f"{'Index':<7} {'Timestamp':<22} {'Type':<7} {'Price':<10} {'Dist $':<10} "
          f"{'Bars':<7} {'Ratio':<10} {'Avg3':<10} {'Swing':<10}")
    print(f"{'-'*140}")

    for i in range(min(max_display, len(df_fractals))):
        fractal = df_fractals.iloc[i]
        type_icon = "▲" if fractal['type'] == 'TOP' else "▼"

        print(f"{fractal['index']:<7} {fractal['timestamp']:<22} {type_icon} {fractal['type']:<5} "
              f"${fractal['price']:<9.2f} ${fractal.get('distance_usd', 0):<9.2f} "
              f"{fractal.get('distance_bars', 0):<7} {fractal.get('distance_ratio', 0):<10.2f} "
              f"{fractal.get('dist_ratio_avg', 0):<10.2f} {fractal.get('swing_size', 'noise'):<10}")

    if len(fractals) > max_display:
        print(f"\n... and {len(fractals) - max_display} more fractals")
    print(f"{'-'*140}")


def main(change_pct=0.10, data_filename='es_1min_data_2023_03_01.csv'):
    """
    Main function to detect tops and bottoms in ES data

    Args:
        change_pct: Minimum percentage change for zigzag detection (default 0.10%)
        data_filename: Input CSV filename (default: March 1, 2023 data)
    """
    print("=" * 70)
    print("🔍 FRACTAL DETECTION - TOPS AND BOTTOMS FINDER")
    print("=" * 70)
    print(f"Method: ZIGZAG ({change_pct}% minimum change)")
    print(f"Data: {data_filename}")
    print("=" * 70)

    try:
        # Load data
        print("\n📂 Loading ES 1-minute data...")
        df = load_es_data(data_filename)

        # Detect fractals
        fractals = detect_fractals_zigzag(df, min_change_pct=change_pct)

        # Display results
        if fractals:
            print_fractal_summary(fractals)
            print_detailed_fractals(fractals, max_display=25)

            # Save to CSV
            output_filename = f'fractals_{data_filename.replace(".csv", "")}_zigzag_{change_pct}.csv'
            output_path = save_fractals_to_csv(fractals, output_filename)

            # Show saved file preview
            print(f"\n📄 Preview of {output_filename}:")
            print("-" * 70)
            df_output = pd.read_csv(output_path)
            print(df_output.head(10).to_string(index=False))
            if len(df_output) > 10:
                print(f"\n... and {len(df_output) - 10} more rows")

            print(f"\n✅ Fractal detection completed successfully!")
            print(f"📊 Total fractals detected: {len(fractals)}")

            return fractals
        else:
            print("\n❌ No fractals detected with current settings.")
            print("💡 Try lowering the min_change_pct parameter.")
            return []

    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print(f"💡 Make sure the file exists in: {DATA_DIR}")
        return []
    except Exception as e:
        print(f"\n❌ Error during fractal detection: {e}")
        import traceback
        traceback.print_exc()
        return []


if __name__ == "__main__":
    # Run with default settings
    # You can customize these parameters:
    fractals = main(
        change_pct=0.10,  # 0.10% minimum change
        data_filename='es_1min_data_2023_03_01.csv'
    )