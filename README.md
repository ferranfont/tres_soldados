# Tres Soldados - ES Futures Data Analysis & Visualization

Trading analysis and visualization toolkit for E-mini S&P 500 (ES) futures data at multiple timeframes.

## 📊 Overview

**Tres Soldados** processes and visualizes ES futures data from tick-level to daily timeframes, providing comprehensive tools for technical analysis and market research.

## 🚀 Installation

```bash
pip install -r requirements.txt
```

### Dependencies
- **pandas** - Data manipulation and analysis
- **plotly** - Interactive charting
- **python-dotenv** - Environment configuration

## 📁 Project Structure

```
tres_soldados/
├── data/                              # Market data files
│   ├── ES_near_tick_data_27_jul_2025.csv      # Tick data (~547K ticks)
│   ├── es_1min_data_2015_2025.csv             # 1-min data (2015-2025, ~3.5M bars)
│   ├── es_1min_data_2023_03_01.csv            # Single day extract
│   └── DATA_DOCUMENTATION.md                  # Data file documentation
│
├── utils/                             # Data processing scripts
│   ├── clean_data_and_format_tick_data.py     # Tick → Daily resampling
│   ├── clean_data_minut_format_all_dataframe.py # Minute → Daily resampling
│   ├── clean_data_one_day_data.py             # Extract single day data
│   └── CLEAN_DATA.md                          # Processing scripts documentation
│
├── charts/                            # Generated HTML charts (gitignored)
│
├── plot_tick_data.py                  # Tick data plotting (candlestick)
├── plot_minute_data.py                # Minute data plotting (candlestick)
├── plot_chart_volume.py               # Daily data plotting (line + volume)
├── config.py                          # Configuration settings
├── requirements.txt                   # Python dependencies
├── CLAUDE.md                          # AI assistant instructions
└── README.md                          # This file
```

## 🎯 Features

### Data Processing
- **Tick-level data**: Process near-tick resolution data (~547K records per day)
- **Minute-level data**: Handle 10+ years of 1-minute candles
- **Resampling**: Convert tick/minute data to daily candles
- **Single-day extraction**: Extract and analyze specific trading days

### Visualization
- **Candlestick charts**: Full OHLC visualization for intraday data
- **Line charts**: Clean price trends for daily/long-term analysis
- **Volume analysis**: Integrated volume bars on all charts
- **Interactive**: Zoom, pan, and export capabilities (Plotly)

### Data Coverage
- **Timeframes**: Tick, 1-minute, 1-day
- **Period**: 2015-2025 (10+ years of historical data)
- **Instrument**: E-mini S&P 500 (ES) futures

## 📖 Usage

### Quick Start - Plot Different Timeframes

**1. Plot tick data (resampled to 1-minute candles):**
```bash
python utils/clean_data_and_format_tick_data.py
```

**2. Plot 10 years of daily data (line chart):**
```bash
python utils/clean_data_minut_format_all_dataframe.py
```

**3. Plot a specific day (candlestick chart):**
```bash
python utils/clean_data_one_day_data.py
```
Edit `TARGET_DATE` in the script to change the date.

**4. Standalone plotting:**
```bash
# Daily line chart
python plot_chart_volume.py

# Minute candlestick chart
python plot_minute_data.py

# Tick candlestick chart
python plot_tick_data.py
```

### Configuration

Edit `config.py` to customize:
- Data directory path
- Chart dimensions (width/height)
- Chart template/theme
- OHLCV aggregation rules

## 📊 Data Files

| File | Timeframe | Records | Date Range | Size |
|------|-----------|---------|------------|------|
| `ES_near_tick_data_27_jul_2025.csv` | Tick | ~547K | July 25, 2025 | Single day |
| `es_1min_data_2015_2025.csv` | 1-minute | ~3.5M | 2015-2025 | 10+ years |
| `es_1min_data_2023_03_01.csv` | 1-minute | ~1.4K | March 1, 2023 | Single day |

📝 See [`data/DATA_DOCUMENTATION.md`](data/DATA_DOCUMENTATION.md) for detailed data format specifications.

## 🔧 Processing Scripts

| Script | Input | Output | Purpose |
|--------|-------|--------|---------|
| `clean_data_and_format_tick_data.py` | Tick data | Candlestick chart | Visualize tick-level price action |
| `clean_data_minut_format_all_dataframe.py` | 10 years minute data | Daily line chart | Long-term trend analysis |
| `clean_data_one_day_data.py` | Full dataset | Single day CSV + chart | Intraday analysis |

📝 See [`utils/CLEAN_DATA.md`](utils/CLEAN_DATA.md) for detailed script documentation.

## 📈 Output

All charts are saved as interactive HTML files in the `charts/` folder:
- **Tick charts**: `charts/ES_tick_1min.html`
- **Daily charts**: `charts/ES_1D.html`
- **Single day charts**: `charts/ES_1min_YYYY-MM-DD.html`

Charts automatically open in your default browser after generation.

## 🎨 Chart Types

### Candlestick Charts (Minute/Tick Data)
- Full OHLC bars with green (up) / red (down) coloring
- Black semi-transparent borders
- Hourly time labels (HH:MM format)
- Volume bars below price chart

### Line Charts (Daily Data)
- Close price line (blue)
- Date labels (MMM DD YYYY format)
- Volume bars below price chart
- Optimized for long-term trend visualization

## 📚 Documentation

- **[DATA_DOCUMENTATION.md](data/DATA_DOCUMENTATION.md)** - Data file formats and specifications
- **[CLEAN_DATA.md](utils/CLEAN_DATA.md)** - Processing scripts detailed guide
- **[CLAUDE.md](CLAUDE.md)** - AI assistant context and instructions

## 🛠️ Development

### Adding New Data
1. Place CSV file in `data/` folder
2. Update data paths in scripts or `config.py`
3. Run appropriate processing script

### Custom Timeframes
Modify `resample_seconds` parameter in `plot_tick_data()`:
```python
plot_tick_data(symbol, timeframe, df, resample_seconds=30)  # 30-second bars
```

## 📄 License

This project is for educational and research purposes.

## 🤝 Contributing

This is a personal research project. For suggestions or issues, please open an issue on GitHub.

---

**Repository**: [tres_soldados](https://github.com/ferranfont/tres_soldados)

**Last Updated**: January 2025