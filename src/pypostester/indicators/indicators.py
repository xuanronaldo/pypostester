from typing import Dict, Set
import polars as pl
import numpy as np
from pypostester.indicators.base import BaseIndicator


class TotalReturn(BaseIndicator):
    """总收益率指标"""

    @property
    def name(self) -> str:
        return "total_return"

    def calculate(self, cache: Dict) -> float:
        """计算总收益率"""
        if "total_return" not in cache:
            curve = cache["curve_df"].get_column("funding_curve")
            cache["total_return"] = float(curve.tail(1)[0] / curve[0] - 1)
        return cache["total_return"]

    def format(self, value: float) -> str:
        return f"{value:.2%}"


class AnnualReturn(BaseIndicator):
    """年化收益率指标"""

    @property
    def name(self) -> str:
        return "annual_return"

    @property
    def requires(self) -> Set[str]:
        return {"total_return"}

    def calculate(self, cache: Dict) -> float:
        """计算年化收益率"""
        if "annual_return" not in cache:
            # 使用total_return计算年化收益率
            total_return = cache["total_return"]

            # 使用实际的交易天数进行年化
            periods_per_day = cache["periods_per_day"]
            total_periods = len(cache["curve_df"].get_column("funding_curve"))
            actual_days = total_periods / periods_per_day

            cache["annual_return"] = float(
                ((1 + total_return) ** (365 / actual_days)) - 1
            )
        return cache["annual_return"]

    def format(self, value: float) -> str:
        return f"{value:.2%}"


class Volatility(BaseIndicator):
    """波动率指标"""

    @property
    def name(self) -> str:
        return "volatility"

    def calculate(self, cache: Dict) -> float:
        """计算年化波动率"""
        returns = cache["returns"]
        periods_per_day = cache["periods_per_day"]
        annual_periods = periods_per_day * cache["annual_trading_days"]

        volatility = returns.std() * np.sqrt(annual_periods)
        cache["volatility"] = volatility
        return volatility

    def format(self, value: float) -> str:
        return f"{value:.2%}"


class SharpeRatio(BaseIndicator):
    """夏普比率指标"""

    @property
    def name(self) -> str:
        return "sharpe_ratio"

    @property
    def requires(self) -> Set[str]:
        return {"annual_return", "volatility"}

    def calculate(self, cache: Dict) -> float:
        """计算夏普比率"""
        if "sharpe_ratio" not in cache:
            if "volatility" not in cache:
                volatility_indicator = Volatility()
                cache["volatility"] = volatility_indicator.calculate(cache)

            annual_vol = cache["volatility"]
            cache["sharpe_ratio"] = float(
                cache["annual_return"] / annual_vol if annual_vol != 0 else 0
            )
        return cache["sharpe_ratio"]

    def format(self, value: float) -> str:
        return f"{value:.2f}"


class MaxDrawdown(BaseIndicator):
    """最大回撤指标"""

    @property
    def name(self) -> str:
        return "max_drawdown"

    def calculate(self, cache: Dict) -> float:
        """计算最大回撤

        计算方法：
        1. 计算每个时点的历史新高
        2. 计算每个时点相对于历史新高的回撤
        3. 取最大回撤值
        """
        if "max_drawdown" not in cache:
            df = cache["curve_df"]

            # 计算历史新高
            df = df.with_columns(pl.col("funding_curve").cum_max().alias("peak"))

            # 计算回撤
            df = df.with_columns(
                ((pl.col("peak") - pl.col("funding_curve")) / pl.col("peak")).alias(
                    "drawdown"
                )
            )

            # 获取最大回撤
            max_dd = float(df.get_column("drawdown").max())

            cache["max_drawdown"] = max_dd

        return cache["max_drawdown"]

    def format(self, value: float) -> str:
        return f"{value:.2%}"


class MaxDrawdownDuration(BaseIndicator):
    """最大回撤持续期指标"""

    @property
    def name(self) -> str:
        return "max_drawdown_duration"

    @property
    def requires(self) -> Set[str]:
        return {"max_drawdown"}

    def calculate(self, cache: Dict) -> float:
        """计算最大回撤持续期（天）"""
        df = cache["curve_df"]

        # 计算历史新高
        df = df.with_columns(pl.col("funding_curve").cum_max().alias("peak"))

        # 计算回撤
        df = df.with_columns(
            ((pl.col("peak") - pl.col("funding_curve")) / pl.col("peak")).alias(
                "drawdown"
            )
        )

        # 找到最大回撤的结束时间点
        max_drawdown_idx = df.get_column("drawdown").arg_max()
        max_drawdown_end = df.get_column("time")[max_drawdown_idx]

        # 找到该回撤的开始时间点（最近的历史新高点）
        peak_before_max_dd = (
            df.filter(pl.col("time") <= max_drawdown_end)
            .filter(pl.col("funding_curve") == pl.col("peak"))
            .get_column("time")[-1]
        )

        # 计算持续天数
        duration_seconds = (max_drawdown_end - peak_before_max_dd).total_seconds()
        duration_days = duration_seconds / (24 * 3600)

        cache["max_drawdown_duration"] = duration_days
        return duration_days

    def format(self, value: float) -> str:
        return f"{value:.0f} days"


class WinRate(BaseIndicator):
    """胜率指标"""

    @property
    def name(self) -> str:
        return "win_rate"

    def calculate(self, cache: Dict) -> float:
        """计算胜率"""
        returns = cache["returns"]
        total_trades = len(returns)
        if total_trades == 0:
            return 0.0
        winning_trades = (returns > 0).sum()
        win_rate = winning_trades / total_trades
        cache["win_rate"] = win_rate
        return win_rate

    def format(self, value: float) -> str:
        return f"{value:.2%}"


class AvgDrawdown(BaseIndicator):
    """平均回撤指标"""

    @property
    def name(self) -> str:
        return "avg_drawdown"

    def calculate(self, cache: Dict) -> float:
        """计算平均回撤

        计算方法：
        1. 计算每个时点的回撤
        2. 只考虑回撤不为0的时点
        3. 计算这些回撤的平均值
        """
        if "avg_drawdown" not in cache:
            curve = cache["curve_df"].get_column("funding_curve")

            # 计算历史新高
            peak = curve.cum_max()

            # 计算回撤
            drawdown = (peak - curve) / peak

            # 只考虑回撤不为0的时点
            non_zero_drawdown = drawdown.filter(drawdown > 0)

            # 计算平均回撤
            avg_dd = float(
                non_zero_drawdown.mean() if len(non_zero_drawdown) > 0 else 0
            )

            cache["avg_drawdown"] = avg_dd

        return cache["avg_drawdown"]

    def format(self, value: float) -> str:
        return f"{value:.2%}"


class ProfitLossRatio(BaseIndicator):
    """盈亏比指标

    计算方法：平均盈利 / 平均亏损的绝对值
    盈亏比 = |获胜交易的平均收益率| / |亏损交易的平均收益率|
    """

    @property
    def name(self) -> str:
        return "profit_loss_ratio"

    def calculate(self, cache: Dict) -> float:
        """计算盈亏比"""
        if "profit_loss_ratio" not in cache:
            returns = cache["returns"]

            # 分离盈利和亏损交易
            profit_trades = returns.filter(returns > 0)
            loss_trades = returns.filter(returns < 0)

            # 计算平均盈利和平均亏损
            avg_profit = profit_trades.mean() if len(profit_trades) > 0 else 0
            avg_loss = abs(loss_trades.mean()) if len(loss_trades) > 0 else float("inf")

            # 计算盈亏比
            if avg_loss == 0:  # 避免除以0
                ratio = float("inf") if avg_profit > 0 else 0
            else:
                ratio = avg_profit / avg_loss

            cache["profit_loss_ratio"] = float(ratio)

        return cache["profit_loss_ratio"]

    def format(self, value: float) -> str:
        if value == float("inf"):
            return "∞"
        return f"{value:.2f}"
