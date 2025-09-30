# Quant Stat - Fractal Detection

## Overview

This folder contains tools for detecting tops and bottoms (fractals) in ES futures price data using the **Zigzag method**.

---

## Files

### 1. `fractal_detector.py` (Library)
**Purpose:** Pure algorithm implementation - Core detection classes

**Contains:**
- `UnifiedZigzagDetector` - Percentage-based zigzag fractal detection algorithm
- Helper classes: `Fractal`, `ZigzagPoint`, `FractalType`, etc.

**Usage:** This is a library file. DO NOT execute directly. It is imported by other scripts.

```python
from quant_stat.fractal_detector import UnifiedZigzagDetector
```

---

### 2. `find_tops_and_bottoms.py` (Application)
**Purpose:** Full pipeline to detect and analyze fractals

**Features:**
- Loads ES data from CSV
- Runs fractal detection using `fractal_detector.py`
- Calculates swing metrics (distance, bars, ratios, classification)
- Saves results to CSV in `outputs/` folder
- Prints detailed reports and summaries

**This is the file you execute.**

---

## How to Use

### Method 1: Using main.py (RECOMMENDED)

Run from the project root:

```bash
python -X utf8 main.py
```

**Configuration:** Edit `main.py` in the root folder:

```python
# Data file to analyze (must be in data/ folder)
DATA_FILE = 'es_1min_data_2023_03_01.csv'

# Zigzag detection sensitivity
CHANGE_PCT = 0.10  # 0.10% minimum change
```

This method allows easy iteration over multiple files in the future.

---

### Method 2: Direct Execution (Alternative)

Execute directly from quant_stat folder:

```bash
python -X utf8 quant_stat/find_tops_and_bottoms.py
```

**Configuration:** Edit the bottom of `find_tops_and_bottoms.py`:

```python
fractals = main(
    change_pct=0.10,  # Minimum % change to detect pivot
    data_filename='es_1min_data_2023_03_01.csv'  # Input CSV file
)
```

---

**Note:** The `-X utf8` flag is required on Windows to display emojis in output.

### Output

Results are saved to: `outputs/fractals_[filename]_zigzag_[pct].csv`

Example: `outputs/fractals_es_1min_data_2023_03_01_zigzag_0.1.csv`

### Parameters

| Parameter | Description | Default | Notes |
|-----------|-------------|---------|-------|
| `change_pct` | Minimum percentage change | 0.10 | Lower value detects more fractals |
| `data_filename` | Input CSV file | `es_1min_data_2023_03_01.csv` | Must be in `data/` folder |

---

## Output CSV Columns

The generated CSV contains the following columns:

| Column | Description |
|--------|-------------|
| `index` | Row index in original data |
| `timestamp` | Date and time of fractal |
| `price` | Price at fractal point |
| `type` | "TOP" or "BOTTOM" |
| `distance_usd` | Price distance from previous fractal ($) |
| `distance_bars` | Number of bars from previous fractal |
| `distance_ratio` | `(distance_usd * 100) / distance_bars` |
| `swing_size` | Classification: "big", "small", or "noise" |
| `dist_ratio_avg` | 3-period moving average of distance_ratio |

---

## Swing Size Classification

Fractals are classified based on price movement:

| Classification | Criteria | Description |
|----------------|----------|-------------|
| **BIG** | ≥ $15.00 | Large price moves |
| **SMALL** | $5.00 - $14.99 | Medium price moves |
| **NOISE** | < $5.00 | Small price moves |

*Thresholds can be adjusted in `classify_swing_size()` function*

---

## Example Results

### Summary Output:
```
Total Fractals Detected: 86
  Tops:               43 (50.0%)
  Bottoms:            43 (50.0%)

Price Analysis:
  Highest Top:      $4483.25
  Lowest Bottom:    $4435.25
  Price Range:      $48.00

Swing Size Analysis:
  BIG      swings:   5 (  5.8%)
  SMALL    swings:  68 ( 79.1%)
  NOISE    swings:  13 ( 15.1%)
```

---

## Important Notes

### Which File to Execute?

✅ **Execute:** `find_tops_and_bottoms.py` (the application)
❌ **DO NOT Execute:** `fractal_detector.py` (it's a library)

### Analogy:
- `fractal_detector.py` = Engine (you use it but don't drive it)
- `find_tops_and_bottoms.py` = Complete car (you drive it)

---

## Data Requirements

Input CSV must have these columns:
- `date`, `time` (or combined datetime)
- `open`, `high`, `low`, `close`
- `volume`

Default data file: `data/es_1min_data_2023_03_01.csv`

---

## Method: Zigzag Detection

The **Zigzag method** detects fractals based on percentage price changes:

1. Tracks highest highs and lowest lows
2. Detects pivot when price reverses by minimum threshold (`change_pct`)
3. Guarantees alternating tops and bottoms
4. No lookahead bias - suitable for real-time trading

### Advantages:
- Clean, alternating fractal patterns
- Adjustable sensitivity via `change_pct`
- No window delay
- Captures significant price swings

---

## Troubleshooting

### Error: "UnicodeEncodeError"
**Solution:** Run with UTF-8 encoding:
```bash
python -X utf8 quant_stat/find_tops_and_bottoms.py
```

### Error: "FileNotFoundError"
**Solution:** Make sure the data file exists in `data/` folder

### Too many fractals detected
**Solution:** Increase `change_pct` (e.g., from 0.10 to 0.15)

### Too few fractals detected
**Solution:** Decrease `change_pct` (e.g., from 0.10 to 0.05)

---

## Future Enhancements

- [ ] Plot fractals as blue dots on charts
- [ ] Integrate with `plot_minute_data.py`
- [ ] Add pending creek analysis
- [ ] Master candle detection
- [ ] Real-time streaming support

---

**Last Updated:** January 2025