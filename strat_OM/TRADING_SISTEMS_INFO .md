# Trading Strategies - Order Management (OM)

This folder contains automated trading strategies based on creek perdices signals.

## Strategy 1: Creek Crossover Above VWAP

### Overview
Trades creek perdices breakouts when the creek level is above VWAP, indicating bullish momentum in a consolidation zone.

### Entry Rules
- **Signal**: Creek perdices level > VWAP at breakout candle
- **Entry Price**:
  - If master candle detected: Use master candle close
  - Otherwise: Use breakout candle close
- **Entry Time**: At breakout timestamp

### Exit Rules
- **Take Profit**: +5 points from entry
- **Stop Loss**: -5 points from entry
- **End of Day**: Close at market if position still open

### Usage

```bash
# Run for specific date
python strat_OM/strat_1_crossover_creek.py 2023_03_02 2.0

# Parameters:
# - arg1: date string (format: YYYY_MM_DD)
# - arg2: tolerance used for creek detection (default: 2.0)
```

### Prerequisites
1. Creek perdices CSV must exist in `outputs/` folder
2. Candle data must exist in `data/` folder
3. Data must have VWAP column (named 'ema' or 'vwap')

### Outputs

#### Trading Record CSV
Saved to: `outputs/trading_record_strat1_crossover_{date}.csv`

Columns:
- `trade_id`: Sequential trade number
- `cluster`: Creek perdices group name
- `entry_type`: MASTER or BREAKOUT
- `entry_time`: Entry timestamp
- `entry_price`: Entry price
- `exit_time`: Exit timestamp
- `exit_price`: Exit price
- `exit_reason`: TAKE_PROFIT, STOP_LOSS, or CLOSE_EOD
- `target`: Target price level
- `stop`: Stop loss price level
- `pnl_points`: Profit/Loss in points
- `pnl_percent`: Profit/Loss percentage
- `creek_price`: Creek level
- `vwap_at_entry`: VWAP value at entry

#### HTML Report
Saved to: `outputs/trading_report_strat1_crossover_{date}.html`

Contains:
- Performance summary statistics
- Win rate and P&L metrics
- Exit reason breakdown
- Detailed trade table with all entries/exits

#### Terminal Summary
Displays at end of execution:
- Total trades executed
- Winners/Losers/Breakeven count
- Win rate percentage
- Total P&L in points
- Average win/loss
- Exit reason counts

### Example Output

```
======================================================================
📊 STRATEGY PERFORMANCE SUMMARY
======================================================================
Total Trades: 9
Winners: 5 | Losers: 4 | Breakeven: 0
Win Rate: 55.6%
Total P&L: +5.00 points
Average Win: 5.00 points
Average Loss: -5.00 points

Exit Reasons:
  Take Profit: 5
  Stop Loss: 4
  Close EOD: 0
======================================================================
```

### Strategy Logic

```python
for each creek perdices cluster:
    if creek_price > vwap_at_breakout:
        # Enter long position
        if is_master_candle:
            entry_price = master_candle_close
        else:
            entry_price = breakout_candle_close

        # Set targets
        target = entry_price + 5.0
        stop = entry_price - 5.0

        # Monitor each future candle
        if high >= target:
            exit at target (TAKE_PROFIT)
        elif low <= stop:
            exit at stop (STOP_LOSS)
        elif end_of_day:
            exit at close (CLOSE_EOD)
```

### Configuration

Edit strategy parameters in the script:

```python
TARGET_POINTS = 5.0  # Target profit in points
STOP_POINTS = 5.0    # Stop loss in points
```

### Notes

- Strategy assumes perfect fills at target/stop levels
- No slippage or commission modeled
- Entry assumes creek crossover happens at breakout timestamp
- Master candles have priority for entry price (higher conviction)
- All timestamps use UTC timezone
- One trade per creek perdices cluster maximum

### Future Enhancements

Potential improvements:
- Multiple entry strategies (scale-in)
- Trailing stop loss
- Time-based exits (e.g., close after X minutes)
- Risk-adjusted position sizing
- Commission and slippage modeling
- Multi-day backtesting
- Walk-forward analysis
- Parameter optimization

---

**Last Updated**: January 2025
