from typing import Dict, Set
import polars as pl
import numpy as np
from pypostester.indicators.base import BaseIndicator


class AnnualReturn(BaseIndicator):
    """年化收益率指标"""

    @property
    def name(self) -> str:
        return "annual_return"

    def calculate(self, cache: Dict) -> float:
        """计算年化收益率"""
        if "annual_return" not in cache:
            curve = cache["curve_df"].get_column("funding_curve")
            total_return = float(curve.tail(1)[0] / curve[0])

            # 使用实际的交易天数进行年化
            periods_per_day = cache["periods_per_day"]
            total_periods = len(curve)
            actual_days = total_periods / periods_per_day

            cache["annual_return"] = float((total_return ** (365 / actual_days)) - 1)
        return cache["annual_return"]


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


class MaxDrawdown(BaseIndicator):
    """最大回撤指标"""

    @property
    def name(self) -> str:
        return "max_drawdown"

    def calculate(self, cache: Dict) -> float:
        """计算最大回撤"""
        curve = cache["curve_df"].get_column("funding_curve")
        max_dd = (curve.cum_max() - curve).max() / curve.max()
        cache["max_drawdown"] = max_dd
        return max_dd


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


class CalmarRatio(BaseIndicator):
    """卡玛比率指标"""

    @property
    def name(self) -> str:
        return "calmar_ratio"

    @property
    def requires(self) -> Set[str]:
        return {"annual_return", "max_drawdown"}

    def calculate(self, cache: Dict) -> float:
        """计算卡玛比率"""
        if "calmar_ratio" not in cache:
            max_dd = cache["max_drawdown"]
            cache["calmar_ratio"] = float(
                cache["annual_return"] / max_dd if max_dd != 0 else 0
            )
        return cache["calmar_ratio"]


class SortinoRatio(BaseIndicator):
    """索提诺比率指标"""

    @property
    def name(self) -> str:
        return "sortino_ratio"

    @property
    def requires(self) -> Set[str]:
        return {"annual_return"}

    def calculate(self, cache: Dict) -> float:
        """计算索提诺比率"""
        if "sortino_ratio" not in cache:
            returns = cache["returns"]
            periods_per_day = cache["periods_per_day"]

            # 只考虑负收益的波动率
            negative_returns = returns.filter(returns < 0)
            if len(negative_returns) == 0:
                downside_vol = 0
            else:
                # 计算下行波动率
                period_vol = float(negative_returns.std())
                # 转换为日化波动率
                daily_factor = np.sqrt(periods_per_day)
                daily_vol = period_vol * daily_factor
                # 转换为年化波动率
                annualization_factor = np.sqrt(cache["annual_trading_days"])
                downside_vol = daily_vol * annualization_factor

            cache["sortino_ratio"] = float(
                cache["annual_return"] / downside_vol if downside_vol != 0 else 0
            )
        return cache["sortino_ratio"]


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


class MonthlyReturns(BaseIndicator):
    """月度收益率指标"""

    @property
    def name(self) -> str:
        return "monthly_returns"

    def calculate(self, cache: Dict) -> Dict[str, float]:
        """计算月度收益率"""
        if "monthly_returns" not in cache:
            df = cache["curve_df"]

            # 确保数据按时间排序
            df = df.sort("time")

            # 添加月份列
            df = df.with_columns([pl.col("time").dt.strftime("%Y-%m").alias("month")])

            # 获取每月第一个和最后一个时间点的数据
            monthly_data = (
                df.group_by("month")
                .agg(
                    [
                        pl.col("funding_curve").first().alias("first_value"),
                        pl.col("funding_curve").last().alias("last_value"),
                        pl.col("time").first().alias("start_time"),
                        pl.col("time").last().alias("end_time"),
                    ]
                )
                .sort("month")
            )

            # 计算月度收益率和实际天数
            monthly_data = monthly_data.with_columns(
                [
                    ((pl.col("last_value") / pl.col("first_value")) - 1).alias(
                        "return"
                    ),
                    (
                        (pl.col("end_time") - pl.col("start_time"))
                        .cast(pl.Int64)  # 转换为整数（纳秒）
                        .cast(pl.Float64)  # 转换为浮点数
                        / (24 * 3600 * 1e9)
                    ).alias(  # 转换为天数
                        "days_in_month"
                    ),
                ]
            )

            # 转换为字典格式，包含年化的月度收益率
            monthly_returns_dict = {}
            for row in monthly_data.iter_rows(named=True):
                month = row["month"]
                monthly_return = row["return"]
                days = row["days_in_month"]

                # 计算年化月度收益率
                if days > 0:
                    annualized_monthly_return = (1 + monthly_return) ** (30 / days) - 1
                else:
                    annualized_monthly_return = monthly_return

                monthly_returns_dict[month] = float(annualized_monthly_return)

            cache["monthly_returns"] = monthly_returns_dict

        return cache["monthly_returns"]
