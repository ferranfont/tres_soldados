# CLAUDE.md - AI Assistant Context

## Project Overview

**Tres Soldados** is an advanced ES (E-mini S&P 500) futures fractal detection and creek perdices analysis toolkit. The project uses zigzag methodology to detect fractals (TOPs/BOTTOMs) and identifies consolidation zones (creek perdices) where multiple TOPs cluster within a tight price range.

## Core Functionality

### 1. Zigzag Fractal Detection
- Detects TOPs (local highs) and BOTTOMs (local lows)
- Configurable sensitivity via `CHANGE_PCT` parameter (0.05% - 0.20%)
- Calculates swing sizes, distances, and price ratios
- Outputs fractals with timestamps, prices, and metrics

### 2. Creek Perdices Detection
- Clusters consecutive TOPs within ±2.0 point tolerance
- Identifies horizontal resistance/support zones
- Detects breakout candles (first close above creek line)
- Groups TOPs into named clusters (cluster_A, cluster_B, etc.)

### 3. Unified Visualization
- Candlestick chart with volume bars
- Blue dots for fractals (TOPs/BOTTOMs)
- Creek perdices overlay:
  - Orange squares: First TOP in cluster (+1.0 offset)
  - Green squares: Last TOP in cluster (+1.0 offset)
  - Blue horizontal line: Creek resistance level
  - Gray rectangle: Consolidation zone (opacity 0.2)
  - Lime triangle-up: Breakout candle (size 9)

## Project Structure

```
tres_soldados/
├── data/                              # Market data CSV files
│   ├── es_1min_data_2023_03_02.csv           # Sample data (1-minute bars)
│   ├── es_1min_data_2015_2025.csv            # Full historical data
│   └── DATA_DOCUMENTATION.md                 # Data format specs
│
├── quant_stat/                        # Core analysis modules
│   ├── find_tops_and_bottoms.py              # Zigzag fractal detection
│   ├── find_true_tops.py                     # Creek perdices clustering
│   └── consolidation_analysis.py             # Statistical analysis
│
├── outputs/                           # Analysis results (CSV)
│   ├── fractals_es_1min_data_*.csv           # Detected fractals
│   ├── true_tops_creek_perdices.csv          # Creek clusters
│   └── temp_top_consolidation_stats.csv      # Temp analysis data
│
├── charts/                            # Generated HTML charts (gitignored)
│
├── utils/                             # Data processing utilities
│   ├── clean_data_one_day_data.py            # Extract single day from full dataset
│   └── CLEAN_DATA.md                         # Utils documentation
│
├── main.py                            # Main pipeline orchestrator
├── plot_minute_data.py                # Unified chart visualization
├── config.py                          # Configuration settings
├── README.md                          # Project documentation
└── CLAUDE.md                          # This file
```

## Key Files

### Main Pipeline (`main.py`)
- Entry point for complete analysis workflow
- Configurable parameters:
  - `DATA_FILE`: Input data file (default: `es_1min_data_2023_03_02.csv`)
  - `CHANGE_PCT`: Zigzag sensitivity (default: `0.10` = 0.10%)
  - `PLOT_CHART`: Enable/disable chart generation (default: `True`)
- Execution flow:
  1. Detect fractals → `quant_stat/find_tops_and_bottoms.py`
  2. Detect creek perdices → `quant_stat/find_true_tops.py`
  3. Generate chart → `plot_minute_data.py`

### Fractal Detection (`quant_stat/find_tops_and_bottoms.py`)
- Implements zigzag algorithm
- Detects TOPs/BOTTOMs based on percentage change threshold
- Calculates:
  - Distance in USD between fractals
  - Distance in bars (candle count)
  - Distance ratio (USD/bars)
  - Swing size classification (noise/small/big)
- Output: `outputs/fractals_es_1min_data_*.csv`

### Creek Perdices Detection (`quant_stat/find_true_tops.py`)
- Clusters consecutive TOPs within ±2.0 point tolerance
- Algorithm:
  ```python
  TOLERANCE_PRICE = 2.0  # ±2.0 points

  # Group consecutive TOPs if within tolerance of ANY TOP in current cluster
  for current_top in tops:
      if any(abs(current_top.price - cluster_top.price) <= TOLERANCE_PRICE
             for cluster_top in current_cluster):
          current_cluster.append(current_top)
      else:
          # Start new cluster
  ```
- Output: `outputs/true_tops_creek_perdices.csv`
  - Columns: `group, top_index, timestamp, price, next_top_price, price_diff_next, is_same_range, cluster_size, first_top_idx, last_top_idx, last_top_timestamp`

### Unified Visualization (`plot_minute_data.py`)
- Generates interactive Plotly chart
- Automatically detects and overlays creek perdices if CSV exists
- Visual elements:
  - Candlesticks: Green (up) / Red (down) OHLC bars
  - Volume: Blue bars below chart
  - Fractals: Blue dots (size 6)
  - Creek perdices:
    - Orange squares (size 7) at first TOP + 1.0 offset
    - Green squares (size 7) at last TOP + 1.0 offset
    - Blue horizontal line (width 1) at average price
    - Gray rectangle (opacity 0.2) from creek to lowest low
    - Lime triangle-up (size 9) at breakout candle close
- Output: `charts/ES_1min_*.html`

### Configuration (`config.py`)
```python
DATA_DIR = Path('./data')              # Data folder path
SYMBOL = 'ES'                          # Trading symbol
CHART_WIDTH = 1800                     # Chart width (pixels)
CHART_HEIGHT = 900                     # Chart height (pixels)
OHLCV_AGGREGATION = {...}              # Resampling rules
```

## Data Flow

```
1. Raw Data (CSV)
   └── data/es_1min_data_2023_03_02.csv
       ↓
2. Fractal Detection
   └── quant_stat/find_tops_and_bottoms.py
       ↓ (outputs fractals CSV)
3. Creek Perdices Detection
   └── quant_stat/find_true_tops.py
       ↓ (reads fractals CSV, outputs creek perdices CSV)
4. Visualization
   └── plot_minute_data.py
       ↓ (reads data + fractals + creek perdices CSVs)
5. Output Chart
   └── charts/ES_1min_2023_03_02.html
```

## Important Notes

### Data Formats
- **Input CSV**: Must have columns `date,open,high,low,close,volume`
- **Datetime**: ISO format with UTC timezone (e.g., `2023-03-02 09:11:00+00:00`)
- **Fractals CSV**: Contains `index,timestamp,price,type,distance_usd,distance_bars,distance_ratio,swing_size,dist_ratio_avg`
- **Creek CSV**: Contains `group,top_index,timestamp,price,next_top_price,price_diff_next,is_same_range,cluster_size,first_top_idx,last_top_idx,last_top_timestamp`

### Timezone Handling
- All datetime operations use **UTC timezone**
- Always use `pd.to_datetime(..., utc=True)` for consistency

### Creek Perdices Visual Specifications
- **Orange/Green squares**: Size 7, positioned +1.0 points above actual TOP price
- **Blue creek line**: Width 1, at average price of first and last TOP
- **Gray rectangle**: Opacity 0.2, from creek line to lowest low in range
- **Lime triangle**: Size 9, at breakout candle close price
- **Breakout logic**: First candle close above creek line, or extend 2 bars if no breakout

### Clustering Algorithm Details
- Only groups consecutive TOPs (must be adjacent in fractal sequence)
- Cluster must have minimum 2 TOPs
- Uses ±2.0 point tolerance (configurable in `find_true_tops.py`)
- Assigns cluster tags: `cluster_A`, `cluster_B`, etc.
- Tracks first and last TOP timestamps for visualization

## Common Tasks

### Run Complete Pipeline
```bash
python main.py
```

### Extract Single Day from Full Dataset
```bash
python utils/clean_data_one_day_data.py
# Edit TARGET_DATE variable to change date
```

### Run Individual Modules
```bash
# Detect fractals only
python quant_stat/find_tops_and_bottoms.py

# Detect creek perdices only (requires fractals CSV)
python quant_stat/find_true_tops.py

# Plot existing data
python plot_minute_data.py
```

### Adjust Sensitivity

**More fractals** (detect smaller swings):
```python
CHANGE_PCT = 0.05  # in main.py
```

**Fewer fractals** (detect larger swings only):
```python
CHANGE_PCT = 0.20  # in main.py
```

**Tighter creek clustering**:
```python
TOLERANCE_PRICE = 1.5  # in find_true_tops.py
```

**Looser creek clustering**:
```python
TOLERANCE_PRICE = 3.0  # in find_true_tops.py
```

## Code Style Guidelines

### When Editing Code
1. **Never modify working code** unless explicitly requested
2. Use absolute paths with `Path(__file__).parent` for file operations
3. Import configuration from `config.py` (e.g., `from config import DATA_DIR, SYMBOL`)
4. Follow existing naming conventions (lowercase with underscores)
5. Add comments in Spanish (project convention)
6. Use UTC timezone for all datetime operations
7. Maintain visual element specifications (sizes, colors, offsets)

### Import Structure
```python
import os
import sys
import pandas as pd
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from config import DATA_DIR, SYMBOL, CHART_WIDTH, CHART_HEIGHT
from plot_minute_data import plot_minute_data
```

### File Naming
- Processing scripts: `*.py` in `quant_stat/` or `utils/`
- Plotting modules: `plot_*.py` in root
- Documentation: `*.md` files (uppercase)
- Data files: lowercase with underscores

## Git Repository

- **Remote**: https://github.com/ferranfont/tres_soldados.git
- **Branch**: main
- **Ignored**: `charts/` folder (contains generated HTML files)

## Dependencies

```
pandas >= 2.0.0      # Data manipulation
plotly >= 5.0.0      # Interactive charts
python-dotenv >= 1.0 # Environment config
```

## Documentation Files

- **README.md** - Project overview, features, usage guide
- **CLAUDE.md** - This file (AI assistant context)
- **data/DATA_DOCUMENTATION.md** - Data file format specifications
- **utils/CLEAN_DATA.md** - Data processing utilities documentation

## Key Reminders

1. **All code is functional** - Do not modify unless explicitly requested
2. **Use config.py** for all paths and settings
3. **Charts output** to `charts/` folder (gitignored)
4. **UTC timezone** for all datetime operations
5. **Visual specs** are precise - maintain sizes, colors, offsets as specified
6. **Clustering algorithm** only groups consecutive TOPs within tolerance
7. **Comments/prints** are in Spanish (project convention)
8. **Creek perdices CSV** is auto-detected and overlaid if exists
9. **Breakout detection** extends 2 bars if no close above creek
10. **Marker offsets** are +1.0 points to avoid overlap with fractals

## Current Implementation Status

### Working Features ✅
- Zigzag fractal detection (TOPs/BOTTOMs)
- Creek perdices clustering (consecutive TOPs ±2.0 points)
- Unified chart visualization with all elements
- Automatic CSV detection and overlay
- Breakout candle detection with lime triangle
- Interactive HTML charts with hover labels
- Complete pipeline orchestration via main.py

### Visual Elements (Current Specs) ✅
- Orange squares: Size 7, +1.0 offset, first TOP
- Green squares: Size 7, +1.0 offset, last TOP
- Blue creek line: Width 1, average price
- Gray rectangle: Opacity 0.2, consolidation zone
- Lime triangle-up: Size 9, breakout candle

### Removed/Deprecated Scripts
- `plot_true_tops.py` (consolidated into plot_minute_data.py)
- `plot_creek_perdices_final.py` (consolidated into plot_minute_data.py)
- `quant_stat/plot_confirmed_tops.py` (legacy, not used)
- `quant_stat/plot_same_range_tops.py` (legacy, not used)

---

**Last Updated**: January 2025
