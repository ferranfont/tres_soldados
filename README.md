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
3. Generate interactive HTML chart with all visualizations

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

### 3. Integrated Visualization
- **Candlestick Chart**: OHLC bars with volume
- **Fractals**: Blue dots marking TOPs/BOTTOMs
- **Creek Perdices**:
  - Orange squares → First TOP in cluster
  - Green squares → Last TOP in cluster
  - Blue horizontal line → Creek resistance level
  - Gray rectangle → Consolidation zone
  - Lime triangle-up → Breakout candle

## 📖 Usage

### Basic Pipeline

```bash
python main.py
```

**Configuration** (`main.py`):
```python
DATA_FILE = 'es_1min_data_2023_03_02.csv'  # Input data
CHANGE_PCT = 0.10                          # Zigzag sensitivity (0.10%)
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

## 📊 Analysis Workflow

```
1. Load 1-minute ES data
   ↓
2. Detect Zigzag Fractals
   ├── Find TOPs (local highs)
   ├── Find BOTTOMs (local lows)
   └── Calculate distances & metrics
   ↓
3. Identify Creek Perdices
   ├── Group consecutive TOPs (±2.0 points)
   ├── Calculate cluster statistics
   └── Detect breakout candles
   ↓
4. Generate Unified Chart
   ├── Plot candlesticks + volume
   ├── Overlay fractals (blue dots)
   ├── Draw creek perdices elements
   └── Save interactive HTML
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
