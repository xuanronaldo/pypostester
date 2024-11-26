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
from pypostester import PositionBacktester

# 获取BTC历史数据
end_date = datetime.now()
start_date = end_date - timedelta(days=365 * 2)  # 最近两年
btc = yf.download("BTC-USD", start=start_date, end=end_date, progress=False)

# 准备数据
close_df = pd.DataFrame({
    "time": btc.index,
    "close": btc["Close"].values
})
position_df = pd.DataFrame({
    "time": btc.index,
    "position": [1.0] * len(btc)  # 买入持有
})

# 创建回测器实例
backtester = PositionBacktester(
    close_df=close_df,
    commission=0.001,  # 0.1% 交易成本
    annual_trading_days=365,  # 加密货币全年交易
    indicators="all"
)

# 运行回测
results = backtester.run(position_df)

# 打印主要指标
print(f"年化收益率: {results['annual_return']:.2%}")
print(f"夏普比率: {results['sharpe_ratio']:.2f}")
print(f"最大回撤: {results['max_drawdown']:.2%}")
print(f"最大回撤持续期: {results['max_drawdown_duration']:.0f}天")
print(f"年化波动率: {results['volatility']:.2%}")
print(f"胜率: {results['win_rate']:.2%}")

# 生成HTML报告
from pypostester import BacktestVisualizer
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
- 支持Pandas和Polars数据框
- 灵活的时间频率（秒、分钟、小时、天）
- 自动的时间对齐验证

## API参考

### PositionBacktester

```python
PositionBacktester(
    close_df: Union[pl.DataFrame, pd.DataFrame],  # 包含time和close列的数据框
    commission: float = 0.0,                      # 交易成本
    annual_trading_days: int = 252,               # 年化交易日数
    indicators: Union[str, List[str]] = "all"     # 需计算的指标
)
```

必需的数据框列：
- close_df: ["time", "close"]
- position_df: ["time", "position"]

### 自定义指标

```python
from pypostester import BaseIndicator

class MyIndicator(BaseIndicator):
    @property
    def name(self) -> str:
        return "my_indicator"
    
    @property
    def requires(self) -> set:
        return set()  # 依赖的其他指标集合
    
    def calculate(self, cache: Dict) -> float:
        # 从缓存中获取数据
        curve_df = cache["curve_df"]
        returns = cache["returns"]
        # 您的计算逻辑
        return result

# 注册指标
backtester.add_indicator(MyIndicator())
```

## 注意事项
1. 持仓值范围应在[-1, 1]之间
2. 交易成本以小数形式输入（如0.001表示0.1%）
3. 时间列必须为datetime类型
4. 数据将自动按时间排序
5. 收盘价和持仓数据必须具有相同的时间戳

## 开发计划
- [ ] 新增更多内置指标
- [ ] 支持多资产回测
- [ ] 添加投资组合优化工具
- [ ] 提供更多可视化选项