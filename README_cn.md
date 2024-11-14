# pypostester

## 简介
基于Python的交易策略回测框架，支持自定义指标计算，提供完整的资金曲线分析与可视化功能。

## 安装

```bash
# 从PyPI安装
pip install pypostester
```

## 快速开始

以下是一个完整的比特币买入持有策略回测示例：

```python
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from pypostester.core import PositionBacktester

# 获取BTC历史数据
end_date = datetime.now()
start_date = end_date - timedelta(days=365 * 2)  # 最近两年
btc = yf.download("BTC-USD", start=start_date, end=end_date, progress=False)

# 准备数据
close = pd.Series(data=btc["Close"].values, index=btc.index, name="close")
position = pd.Series(data=[1.0] * len(close), index=btc.index, name="position")

# 创建回测器实例
backtester = PositionBacktester(
    close=close,
    position=position,
    commission=0.001,  # 0.1% 交易成本
    annual_trading_days=365,  # 加密货币全年交易
    indicators="all"
)

# 运行回测
results = backtester.run()

# 打印主要指标
print(f"年化收益率: {results['annual_return']:.2%}")
print(f"夏普比率: {results['sharpe_ratio']:.2f}")
print(f"最大回撤: {results['max_drawdown']:.2%}")
print(f"最大回撤持续期: {results['max_drawdown_duration']:.0f}天")
print(f"年化波动率: {results['volatility']:.2%}")
print(f"胜率: {results['win_rate']:.2%}")

# 生成HTML报告
from pypostester.utils.visualization import BacktestVisualizer
visualizer = BacktestVisualizer(results, backtester)
visualizer.generate_html_report("btc_backtest_report.html")
```

## 功能特点

### 1. 简单易用的API
- 基于持仓的简单回测
- 全面的绩效指标
- HTML报告生成

### 2. 性能指标
- 年化收益率
- 夏普比率
- 最大回撤
- 波动率
- 胜率
- 更多指标...

### 3. 数据兼容性
- 支持Pandas和Polars
- 兼容多种数据源

## API参考

### PositionBacktester

```python
PositionBacktester(
    close: Union[pd.Series, pl.Series],    # 收盘价序列
    position: Union[pd.Series, pl.Series], # 持仓序列
    commission: float = 0.0,               # 交易成本
    annual_trading_days: int = 252,        # 年化交易日数
    indicators: Union[str, List[str]] = "all" # 需计算的指标
)
```

### 自定义指标

```python
from pypostester.indicators.base import BaseIndicator

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

## 注意事项
1. 持仓值范围应在[-1, 1]之间
2. 交易成本以小数形式输入（如0.001表示0.1%）
3. 确保价格和持仓序列的索引匹配

## 开发激活
- [ ] 新增更多的内置指标