# pypostester

## Introduction
A Python-based backtesting framework for evaluating trading strategies, supporting custom indicator calculations and providing comprehensive equity curve analysis and visualization capabilities.

## Installation

```bash
# Install from PyPI
pip install pypostester
```

## Quick Start

Here's a complete example of backtesting a Bitcoin buy-and-hold strategy:

```python
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from pypostester import PositionBacktester

# Get BTC historical data
end_date = datetime.now()
start_date = end_date - timedelta(days=365 * 2)  # Last 2 years
btc = yf.download("BTC-USD", start=start_date, end=end_date, progress=False)

# Prepare data
close_df = pd.DataFrame({
    "time": btc.index,
    "close": btc["Close"].values
})
position_df = pd.DataFrame({
    "time": btc.index,
    "position": [1.0] * len(btc)  # Buy and hold
})

# Create backtester instance
backtester = PositionBacktester(
    close_df=close_df,
    commission=0.001,  # 0.1% trading cost
    annual_trading_days=365,  # Crypto trades all year
    indicators="all"
)

# Run backtest
results = backtester.run(position_df)

# Print main metrics
print(f"Annual Return: {results['annual_return']:.2%}")
print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {results['max_drawdown']:.2%}")
print(f"Max Drawdown Duration: {results['max_drawdown_duration']:.0f} days")
print(f"Annual Volatility: {results['volatility']:.2%}")
print(f"Win Rate: {results['win_rate']:.2%}")

# Generate HTML report
from pypostester import BacktestVisualizer
visualizer = BacktestVisualizer(results, backtester)
visualizer.generate_html_report("btc_backtest_report.html")
```

## Features

### 1. Easy-to-use API
- Simple position-based backtesting
- Comprehensive performance metrics
- HTML report generation

### 2. Performance Metrics
- Annual return
- Sharpe ratio
- Maximum drawdown
- Volatility
- Win rate
- And more...

### 3. Data Compatibility
- Supports both Pandas and Polars DataFrames
- Flexible time frequency (seconds, minutes, hours, days)
- Automatic time alignment validation

## API Reference

### PositionBacktester

```python
PositionBacktester(
    close_df: Union[pl.DataFrame, pd.DataFrame],  # DataFrame with time and close columns
    commission: float = 0.0,                      # Trading cost
    annual_trading_days: int = 252,               # Annual trading days
    indicators: Union[str, List[str]] = "all"     # Indicators to calculate
)
```

Required DataFrame columns:
- close_df: ["time", "close"]
- position_df: ["time", "position"]

### Custom Indicators

```python
from pypostester import BaseIndicator

class MyIndicator(BaseIndicator):
    @property
    def name(self) -> str:
        return "my_indicator"
    
    @property
    def requires(self) -> set:
        return set()  # Required indicators set
    
    def calculate(self, cache: Dict) -> float:
        # Access data from cache
        curve_df = cache["curve_df"]
        returns = cache["returns"]
        # Your calculation logic here
        return result

# Register indicator
backtester.add_indicator(MyIndicator())
```

## Important Notes
1. Position values should be within [-1, 1] range
2. Trading costs should be input as decimals (e.g., 0.001 for 0.1%)
3. Time columns must be datetime type
4. Data will be automatically sorted by time
5. Close and position data must have matching timestamps

## Roadmap
- [ ] Add more built-in indicators
- [ ] Support multiple assets backtesting
- [ ] Add portfolio optimization tools
- [ ] Provide more visualization options