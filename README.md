# PyPosTester

## Introduction
A Python-based backtesting framework for evaluating trading strategies. The framework supports custom indicator calculations and provides comprehensive equity curve analysis.

## Installation
### From PyPI
```bash
pip install pypostester
```

### From Source
```bash
git clone https://github.com/xuanronaldo/pypostester.git
cd pypostester
pip install -e .
```

## Quick Start

```python
from core.backtester import PositionBacktester
import polars as pl

# Prepare data
close_prices = pl.Series([100, 101, 102, 101, 103])
positions = pl.Series([0, 1, 1, 0, 1])

# Create backtester instance
backtester = PositionBacktester(
    close=close_prices,
    position=positions,
    commission=0.001,  # 0.1% trading cost
    annual_trading_days=252
)

# Run backtest
results = backtester.run()
```

## Detailed Example

### BTC Strategy Backtesting Example

This example demonstrates how to backtest a simple Bitcoin strategy using the framework.

```python
from core.backtester import PositionBacktester
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# Get BTC historical data
end_date = datetime.now()
start_date = end_date - timedelta(days=365 * 2)  # Last 2 years
btc = yf.download("BTC-USD", start=start_date, end=end_date, progress=False)

# Prepare data
close = pd.Series(data=btc["Close"].values, index=btc.index, name="close")
position = pd.Series(data=[1.0] * len(close), index=btc.index, name="position")

# Create backtester instance
backtester = PositionBacktester(
    close=close,
    position=position,
    commission=0.001,  # 0.1% trading cost
    annual_trading_days=365,  # Crypto trades all year
    indicators="all"  # Calculate all available indicators
)

# Run backtest
results = backtester.run()

# View main metrics
print(f"Annual Return: {results['annual_return']:.2%}")
print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {results['max_drawdown']:.2%}")

# Generate visual report
from utils.visualization import BacktestVisualizer
visualizer = BacktestVisualizer(results, backtester)
visualizer.generate_html_report("btc_backtest_report.html")
```

### Running the Example
1. Install additional dependency:
```bash
pip install yfinance
```

2. Run the example script:
```bash
python examples/backtest_btc.py
```

3. View results:
- Main backtest metrics will be displayed in console
- HTML backtest report will be generated in `examples/output` directory

## Core Features

### 1. Equity Curve Calculation
- Supports position-based returns calculation
- Includes transaction cost handling
- Generates complete equity curve

### 2. Indicator System
- Supports built-in indicators
- Allows custom indicator addition
- Automatic indicator dependency resolution

### 3. Data Compatibility
- Supports both Polars and Pandas data formats
- Automatic data format conversion and validation

## API Reference

### PositionBacktester

```python
PositionBacktester(
    close: Union[pl.Series, pd.Series],    # Close price series
    position: Union[pl.Series, pd.Series], # Position series
    commission: float = 0.0,               # Trading cost
    annual_trading_days: int = 252,        # Annual trading days
    indicators: Union[str, List[str]] = "all" # Indicators to calculate
)
```

### Adding Custom Indicators

```python
### Adding Custom Indicators

```python
from indicators.base import BaseIndicator

class MyIndicator(BaseIndicator):
    @property
    def name(self) -> str:
        return "my_indicator"
    
    @property
    def requires(self) -> set:
        return set()  # Required indicators set
    
    def calculate(self, curve: pl.Series, cache: Dict) -> float:
        # Indicator calculation logic
        return result

# Register indicator
backtester.add_indicator(MyIndicator)
```

## Important Notes
1. Ensure close price and position series have the same length
2. Trading costs should be input as decimals (e.g., 0.001 for 0.1%)
3. Position values should be within [-1, 1] range

## Roadmap
- [ ] Add more built-in indicators