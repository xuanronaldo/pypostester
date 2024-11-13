# PyPosTester

## 项目简介
这是一个基于Python的交易策略回测框架，用于评估交易策略的表现。框架支持自定义指标计算，提供完整的资金曲线分析功能。

## 依赖安装
```bash
pip install -r requirements.txt
```

## 快速开始

```python
from core.backtester import PositionBacktester
import polars as pl

# 准备数据
close_prices = pl.Series([100, 101, 102, 101, 103])
positions = pl.Series([0, 1, 1, 0, 1])

# 创建回测器实例
backtester = PositionBacktester(
    close=close_prices,
    position=positions,
    commission=0.001,  # 0.1% 交易成本
    annual_trading_days=252
)

# 运行回测
results = backtester.run()
```

## 核心功能

### 1. 资金曲线计算
- 支持持仓收益计算
- 包含交易成本处理
- 生成完整的资金曲线

### 2. 指标系统
- 支持内置指标计算
- 允许添加自定义指标
- 自动处理指标间依赖关系

### 3. 数据兼容性
- 支持 Polars 和 Pandas 数据格式
- 自动数据格式转换和验证

## 详细示例

### BTC策略回测示例

这个示例展示了如何使用框架回测比特币的简单策略。

```python
from core.backtester import PositionBacktester
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# 获取BTC历史数据
end_date = datetime.now()
start_date = end_date - timedelta(days=365 * 2)  # 最近两年数据
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
    indicators="all"  # 计算所有可用指标
)

# 运行回测
results = backtester.run()

# 查看主要指标
print(f"年化收益率: {results['annual_return']:.2%}")
print(f"夏普比率: {results['sharpe_ratio']:.2f}")
print(f"最大回撤: {results['max_drawdown']:.2%}")

# 生成可视化报告
from utils.visualization import BacktestVisualizer
visualizer = BacktestVisualizer(results, backtester)
visualizer.generate_html_report("btc_backtest_report.html")
```

### 完整示例代码
完整的示例代码可以在 `examples/backtest_btc.py` 中找到，包含了：
- BTC数据获取
- 回测执行
- 结果展示
- HTML报告生成

### 运行示例
1. 安装额外依赖：
```bash
pip install yfinance
```

2. 运行示例脚本：
```bash
python examples/backtest_btc.py
```

3. 查看结果：
- 控制台将显示主要回测指标
- 在 `examples/output` 目录下会生成HTML格式的回测报告

### 回测报告内容
生成的HTML报告包含：
- 资金曲线图表
- 收益指标统计
- 风险指标分析
- 交易统计信息

## API参考

### PositionBacktester

```python
PositionBacktester(
    close: Union[pl.Series, pd.Series],    # 收盘价序列
    position: Union[pl.Series, pd.Series], # 持仓序列
    commission: float = 0.0,               # 交易成本
    annual_trading_days: int = 252,        # 年化交易日数
    indicators: Union[str, List[str]] = "all" # 需计算的指标
)
```

### 添加自定义指标

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
backtester.add_indicator(MyIndicator())
```

## 注意事项
1. 确保收盘价和持仓序列长度相同
2. 交易成本以小数形式输入（如0.001表示0.1%）
3. 持仓值范围建议在[-1, 1]之间

## 开发计划
- [ ] 添加更多内置指标
