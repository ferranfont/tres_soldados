# Tres Soldados - ES Futures Fractal Detection & Creek Perdices

Advanced trading analysis toolkit for E-mini S&P 500 (ES) futures featuring zigzag fractal detection and creek perdices (consolidation zone) identification.

## 📊 Overview

**Tres Soldados** detects fractals (TOPs/BOTTOMs) using zigzag methodology and identifies creek perdices patterns - horizontal resistance/support lines formed by consolidation zones where multiple TOPs cluster within a tight price range.

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run complete analysis pipeline
python main.py
```

This will:
1. Detect fractals (TOPs/BOTTOMs) using zigzag algorithm
2. Identify creek perdices clusters (consolidated TOPs)
3. Detect master candles (high-conviction breakout candles)
4. Identify high-volume candles in consolidation zones
5. Generate interactive HTML chart with all visualizations

## 📁 Project Structure

```
tres_soldados/
├── data/                              # Market data files
│   ├── es_1min_data_2023_03_02.csv           # Sample 1-min data
│   ├── es_1min_data_2015_2025.csv            # Full historical data
│   └── DATA_DOCUMENTATION.md                 # Data format specs
│
├── quant_stat/                        # Core analysis modules
│   ├── find_tops_and_bottoms.py              # Zigzag fractal detection
│   ├── find_true_tops.py                     # Creek perdices clustering
│   ├── find_true_mastercandle.py             # Master candle detection
│   ├── find_true_volume.py                   # High volume analysis
│   └── consolidation_analysis.py             # Statistical analysis tools
│
├── outputs/                           # Analysis results (CSV)
│   ├── fractals_*.csv                        # Detected fractals
│   └── true_tops_creek_perdices.csv          # Creek perdices clusters
│
├── charts/                            # Generated charts (gitignored)
│
├── utils/                             # Data processing utilities
│   ├── clean_data_one_day_data.py            # Extract single day
│   └── CLEAN_DATA.md                         # Utils documentation
│
├── main.py                            # Main pipeline orchestrator
├── plot_minute_data.py                # Unified chart visualization
├── config.py                          # Configuration settings
└── README.md                          # This file
```

## 🎯 Core Features

### 1. Zigzag Fractal Detection
- **Algorithm**: Percentage-based pivot detection
- **Configurable**: Adjust `CHANGE_PCT` sensitivity (0.05% - 0.20%)
- **Output**: TOPs and BOTTOMs with timestamps, prices, distances
- **Metrics**: Swing size classification, distance ratios, trend analysis

### 2. Creek Perdices Detection
- **Method**: Cluster consecutive TOPs within ±2.0 point tolerance
- **Output**: Consolidated clusters with first/last TOP timestamps
- **Visualization**: Horizontal resistance lines at consolidation zones
- **Breakout Detection**: Identifies when price closes above creek line

### 3. Master Candle Detection
- **Criteria**:
  - Candle closes ABOVE creek line (breakout)
  - Range > average range of consolidation zone
  - Upper tail ≤ 20% of candle range (configurable)
- **Visualization**: Gold asterisk-open symbols
- **Output**: Master candle timestamp, range, tail percentage

### 4. High Volume Analysis
- **Method**: Identifies candles with volume ≥ 1.5x average (configurable)
- **Position Filter**: Only candles in lower 70th percentile (configurable)
- **Exception**: Master candles always included regardless of position
- **Visualization**: Deep pink hash symbols below candle lows
- **Output**: Up to 3 highest volume candles per cluster

### 5. Integrated Visualization
- **Candlestick Chart**: OHLC bars with volume
- **Fractals**: Blue dots marking TOPs/BOTTOMs
- **Creek Perdices**:
  - Orange squares → First TOP in cluster
  - Green squares → Last TOP in cluster
  - Blue horizontal line → Creek resistance level
  - Gray rectangle → Consolidation zone
  - Lime triangle-up → Breakout candle
- **Master Candles**: Gold asterisk-open symbols
- **High Volume**: Deep pink hash symbols

## 📖 Usage

### Basic Pipeline

```bash
python main.py
```

**Configuration** (`main.py`):
```python
DATA_FILE = 'es_1min_data_2023_03_02.csv'  # Input data
CHANGE_PCT = 0.10                          # Zigzag sensitivity (0.10%)
TOLERANCE_PRICE = 2.0                      # Creek clustering tolerance (±2.0 points)
MASTER_UPPER_TAIL_PCT = 20                 # Master candle max upper tail (20%)
VOL_MULTIPL = 1.5                          # Volume threshold (1.5x average)
VOL_PERCENTILE = 70                        # Position filter (70th percentile)
PLOT_CHART = True                          # Generate chart
```

### Output Files

**1. Fractals CSV** (`outputs/fractals_*.csv`):
```
index, timestamp, price, type, distance_usd, distance_bars, swing_size
551, 2023-03-02 09:11:00, 4431.5, TOP, 12.75, 36, small
```

**2. Creek Perdices CSV** (`outputs/true_tops_creek_perdices.csv`):
```
group, top_index, timestamp, price, next_top_price, cluster_size, last_top_timestamp
cluster_A, 7, 2023-03-02 09:11:00, 4431.5, 4429.75, 2, 2023-03-02 10:31:00
```

**3. Interactive Chart** (`charts/ES_1min_*.html`):
- Fully interactive (zoom, pan, hover)
- Exportable to PNG
- Auto-opens in browser

### Advanced Usage

**Extract single day:**
```bash
python utils/clean_data_one_day_data.py
```

**Run individual modules:**
```bash
# Detect fractals only
python quant_stat/find_tops_and_bottoms.py

# Detect creek perdices only (requires fractals CSV)
python quant_stat/find_true_tops.py

# Plot existing data
python plot_minute_data.py
```

### Configuration (`config.py`)

```python
DATA_DIR = Path('./data')              # Data folder
SYMBOL = 'ES'                          # Trading symbol
CHART_WIDTH = 1800                     # Chart width (px)
CHART_HEIGHT = 900                     # Chart height (px)
```

## 🔬 Creek Perdices Algorithm

### Clustering Logic

```python
TOLERANCE_PRICE = 2.0  # ±2.0 points price range

# Groups consecutive TOPs into clusters:
# - TOP at 4431.5
# - TOP at 4429.75  ← Within ±2.0 range → Same cluster
# - TOP at 4436.75  ← Outside range → New cluster
```

### Consolidation Zone Detection

1. **Identify Cluster**: Group consecutive TOPs within ±2.0 points
2. **Calculate Creek Line**: Average price of first and last TOP
3. **Find Breakout**: First candle close above creek line (or extend 2 bars)
4. **Define Zone**: Rectangle from cluster start to breakout, creek line to lowest low

### Visual Elements

| Element | Description | Color | Position |
|---------|-------------|-------|----------|
| Orange Square | First TOP in cluster | Orange | +1.0 points above TOP |
| Green Square | Last TOP in cluster | Green | +1.0 points above TOP |
| Blue Line | Creek resistance level | Blue | Average of TOPs |
| Gray Rectangle | Consolidation zone | LightGray (20% opacity) | Creek to lowest low |
| Lime Triangle | Breakout candle | Lime | At candle close |

## 📊 How Files Work - Complete Workflow

### Data Pipeline

The project follows a structured pipeline from raw historical data to analyzed single-day charts:

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: Source Data (Full Historical Dataset)                  │
└─────────────────────────────────────────────────────────────────┘
  data/es_1min_data_2015_2025.csv  ← Full 10-year historical data
    │
    │ Extract single day using:
    │ python utils/clean_data_one_day_data.py
    ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: Single Day File (Study Target)                         │
└─────────────────────────────────────────────────────────────────┘
  data/es_1min_data_2023_03_02.csv  ← One trading day
    │
    │ Run analysis pipeline:
    │ python main.py
    ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: Fractal Detection                                      │
└─────────────────────────────────────────────────────────────────┘
  quant_stat/find_tops_and_bottoms.py
    │
    │ Output:
    ↓
  outputs/fractals_es_1min_data_2023_03_02.csv
    ├── Columns: index, timestamp, price, type (TOP/BOTTOM)
    ├── Metrics: distance_usd, distance_bars, swing_size
    └── Example: 88 fractals (44 TOPs, 44 BOTTOMs)
    │
    │ Passed to creek detection:
    ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: Creek Perdices Detection                               │
└─────────────────────────────────────────────────────────────────┘
  quant_stat/find_true_tops.py
    │
    │ Output:
    ↓
  outputs/true_tops_creek_perdices.csv
    ├── Columns: group, top_index, timestamp, price
    ├── Cluster info: cluster_size, first_top_idx, last_top_idx
    └── Example: 9 clusters (cluster_A through cluster_I)
    │
    │ Both CSVs passed to visualization:
    ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: Unified Visualization                                  │
└─────────────────────────────────────────────────────────────────┘
  plot_minute_data.py
    │
    │ Reads:
    │ - data/es_1min_data_2023_03_02.csv (raw OHLCV)
    │ - outputs/fractals_*.csv (TOPs/BOTTOMs)
    │ - outputs/true_tops_creek_perdices.csv (clusters)
    │
    │ Generates:
    ↓
  charts/ES_1min_2023_03_02.html
    ├── Candlestick chart with volume
    ├── Blue dots: Fractals overlay
    ├── Orange/Green squares: Creek cluster boundaries
    ├── Blue lines: Creek resistance levels
    ├── Gray rectangles: Consolidation zones
    └── Lime triangles: Breakout candles
```

### Step-by-Step Instructions

#### 1. Extract Single Day from Full Dataset

**Source file**: `data/es_1min_data_2015_2025.csv` (10 years of 1-minute bars)

**Script**: `utils/clean_data_one_day_data.py`

**How to use**:
```bash
# Edit the script to change target date:
TARGET_DATE = '2023-03-02'

# Run extraction:
python utils/clean_data_one_day_data.py
```

**Output**: `data/es_1min_data_2023_03_02.csv` (one trading day, ~468 rows)

**Purpose**: Creates focused single-day dataset for detailed fractal analysis

---

#### 2. Detect Fractals (TOPs and BOTTOMs)

**Input**: `data/es_1min_data_2023_03_02.csv`

**Script**: `quant_stat/find_tops_and_bottoms.py` (called by `main.py`)

**Algorithm**:
- Zigzag method with configurable `CHANGE_PCT` threshold (default 0.10%)
- Detects local highs (TOPs) and lows (BOTTOMs)
- Calculates swing metrics (distance in USD, bars, ratios)

**Output**: `outputs/fractals_es_1min_data_2023_03_02.csv`

**CSV Structure**:
```csv
index,timestamp,price,type,distance_usd,distance_bars,distance_ratio,swing_size
551,2023-03-02 09:11:00+00:00,4431.5,TOP,12.75,36,0.354,small
587,2023-03-02 09:47:00+00:00,4418.75,BOTTOM,8.5,28,0.304,noise
```

**Configuration** (`main.py`):
```python
CHANGE_PCT = 0.10  # 0.10% sensitivity
# Lower value = more fractals (higher sensitivity)
# Higher value = fewer fractals (lower sensitivity)
```

---

#### 3. Detect Creek Perdices (Consolidation Clusters)

**Input**: `outputs/fractals_es_1min_data_2023_03_02.csv` (TOPs only)

**Script**: `quant_stat/find_true_tops.py` (called by `main.py`)

**Algorithm**:
- Groups **consecutive** TOPs within ±2.0 point tolerance
- Minimum 2 TOPs per cluster
- Assigns cluster names: `cluster_A`, `cluster_B`, etc.
- Tracks first/last TOP timestamps for visualization

**Output**: `outputs/true_tops_creek_perdices.csv`

**CSV Structure**:
```csv
group,top_index,timestamp,price,next_top_price,price_diff_next,is_same_range,cluster_size,first_top_idx,last_top_idx,last_top_timestamp
cluster_A,7,2023-03-02 09:11:00+00:00,4431.5,4429.75,-1.75,True,2,7,9,2023-03-02 10:31:00+00:00
cluster_A,9,2023-03-02 10:31:00+00:00,4429.75,4436.75,7.00,False,2,7,9,2023-03-02 10:31:00+00:00
```

**Configuration** (`find_true_tops.py`):
```python
TOLERANCE_PRICE = 2.0  # ±2.0 points clustering tolerance
# Lower = tighter clusters, more separate groups
# Higher = looser clusters, fewer separate groups
```

---

#### 4. Generate Unified Chart

**Input**:
- `data/es_1min_data_2023_03_02.csv` (raw OHLCV data)
- `outputs/fractals_es_1min_data_2023_03_02.csv` (TOPs/BOTTOMs)
- `outputs/true_tops_creek_perdices.csv` (creek clusters)

**Script**: `plot_minute_data.py` (called by `main.py`)

**Visualization Layers**:
1. **Candlesticks**: Green (up) / Red (down) OHLC bars
2. **Volume**: Blue bars below chart
3. **Fractals**: Blue dots (size 6) at TOP/BOTTOM prices
4. **Creek Perdices**:
   - Orange squares (size 7): First TOP in cluster (+1.0 offset)
   - Green squares (size 7): Last TOP in cluster (+1.0 offset)
   - Blue horizontal line (width 1): Creek resistance level
   - Gray rectangle (opacity 0.2): Consolidation zone
   - Lime triangle-up (size 9): Breakout candle

**Output**: `charts/ES_1min_2023_03_02.html` (interactive Plotly chart)

**Auto-Detection**: Script automatically overlays creek perdices if CSV exists

---

### File Naming Convention

All output files maintain consistent naming based on input data file:

```
Input:  data/es_1min_data_2023_03_02.csv

Outputs:
├── outputs/fractals_es_1min_data_2023_03_02.csv
├── outputs/true_tops_creek_perdices.csv
└── charts/ES_1min_2023_03_02.html
```

### Running the Complete Pipeline

**Single command**:
```bash
python main.py
```

**What happens**:
1. Reads `DATA_FILE = 'es_1min_data_2023_03_02.csv'` from `main.py`
2. Calls `find_tops_and_bottoms.py` → Creates fractals CSV
3. Calls `find_true_tops.py` → Creates creek perdices CSV
4. Calls `plot_minute_data.py` → Creates interactive chart
5. Opens chart in browser automatically

**Configuration** (`main.py`):
```python
DATA_FILE = 'es_1min_data_2023_03_02.csv'  # Change to analyze different day
CHANGE_PCT = 0.10                          # Fractal sensitivity
PLOT_CHART = True                          # Auto-generate chart
```

### Running Individual Steps

```bash
# Step 1: Extract single day (manual date selection)
python utils/clean_data_one_day_data.py

# Step 2: Detect fractals only
python quant_stat/find_tops_and_bottoms.py

# Step 3: Detect creek perdices only (requires fractals CSV)
python quant_stat/find_true_tops.py

# Step 4: Plot existing data (requires all CSVs)
python plot_minute_data.py
```

---

## 📊 Analysis Workflow Summary

```
es_1min_data_2015_2025.csv (10 years)
  → clean_data_one_day_data.py
    → es_1min_data_2023_03_02.csv (1 day)
      → find_tops_and_bottoms.py
        → fractals_es_1min_data_2023_03_02.csv
          → find_true_tops.py
            → true_tops_creek_perdices.csv
              → plot_minute_data.py
                → ES_1min_2023_03_02.html (chart)
```

## 🎨 Chart Legend

- **Green/Red Candles**: Up/Down bars (OHLC)
- **Blue Dots**: Fractals (TOPs = circles, BOTTOMs = triangles)
- **Orange/Green Squares**: Creek perdices cluster boundaries
- **Blue Horizontal Line**: Creek resistance level
- **Gray Rectangle**: Consolidation zone
- **Lime Triangle**: Breakout confirmation

## 📈 Sample Results (2023-03-02)

**Fractals Detected**: 88 (44 TOPs, 44 BOTTOMs)
**Creek Perdices Clusters**: 9
**Sensitivity**: 0.10% (10 basis points)

**Example Cluster**:
```
Cluster C: 5 TOPs from 14:17 to 14:51
├── First TOP: $4430.50 @ 14:17
├── Last TOP:  $4433.00 @ 14:51
├── Creek Line: $4431.75 (average)
├── Breakout:  14:58 @ $4436.00
└── Duration:  41 minutes
```

## 🛠️ Development

### Adding New Data

1. Place CSV in `data/` folder (format: `date,open,high,low,close,volume`)
2. Update `DATA_FILE` in `main.py`
3. Run pipeline: `python main.py`

### Adjusting Sensitivity

**More fractals** (higher sensitivity):
```python
CHANGE_PCT = 0.05  # Detects smaller swings
```

**Fewer fractals** (lower sensitivity):
```python
CHANGE_PCT = 0.20  # Detects larger swings only
```

**Creek tolerance**:
```python
TOLERANCE_PRICE = 1.5  # Tighter clustering (±1.5 points)
TOLERANCE_PRICE = 3.0  # Looser clustering (±3.0 points)
```

## 📚 Documentation

- **[DATA_DOCUMENTATION.md](data/DATA_DOCUMENTATION.md)** - Data format specifications
- **[CLEAN_DATA.md](utils/CLEAN_DATA.md)** - Data processing utilities
- **[CLAUDE.md](CLAUDE.md)** - AI assistant context and project details

## 🔧 Dependencies

```
pandas >= 2.0.0      # Data manipulation
plotly >= 5.0.0      # Interactive charts
python-dotenv >= 1.0 # Environment config
```

## 📄 License

Educational and research purposes only.

## 🤝 Contributing

Personal research project. For suggestions, open an issue on GitHub.

---

**Repository**: [tres_soldados](https://github.com/ferranfont/tres_soldados)
**Last Updated**: January 2025
