from typing import Dict
import polars as pl
import numpy as np
from indicators.base import BaseIndicator


class MaxDrawdown(BaseIndicator):
    @property
    def name(self) -> str:
        return "max_drawdown"

    def calculate(self, curve: pl.Series, cache: Dict) -> float:
        if "max_drawdown" not in cache:
            cummax = curve.cum_max()
            drawdown = (curve - cummax) / cummax
            cache["max_drawdown"] = float(drawdown.min())
        return cache["max_drawdown"]


class MaxDrawdownDuration(BaseIndicator):
    @property
    def name(self) -> str:
        return "max_drawdown_duration"

    @property
    def requires(self) -> set:
        return {"max_drawdown"}

    def calculate(self, curve: pl.Series, cache: Dict) -> float:
        if "max_drawdown_duration" not in cache:
            cummax = curve.cum_max()
            drawdown = (curve - cummax) / cummax

            # 找到最大回撤结束点
            end_idx = drawdown.arg_min()

            # 找到最大回撤开始点
            start_idx = curve[:end_idx].arg_max()

            # 计算持续天数
            timestamps = cache["funding_curve"].get_column("timestamp")
            duration = (timestamps[end_idx] - timestamps[start_idx]).days
            cache["max_drawdown_duration"] = float(duration)

        return cache["max_drawdown_duration"]


class CalmarRatio(BaseIndicator):
    @property
    def name(self) -> str:
        return "calmar_ratio"

    @property
    def requires(self) -> set:
        return {"annual_return", "max_drawdown"}

    def calculate(self, curve: pl.Series, cache: Dict) -> float:
        if "calmar_ratio" not in cache:
            cache["calmar_ratio"] = float(
                cache["annual_return"] / abs(cache["max_drawdown"])
                if cache["max_drawdown"] != 0
                else 0
            )
        return cache["calmar_ratio"]


class Volatility(BaseIndicator):
    @property
    def name(self) -> str:
        return "volatility"

    def calculate(self, curve: pl.Series, cache: Dict) -> float:
        if "volatility" not in cache:
            if "returns" not in cache:
                cache["returns"] = curve.pct_change()

            annualization_factor = np.sqrt(365 / cache["total_days"])
            cache["volatility"] = float(cache["returns"].std() * annualization_factor)
        return cache["volatility"]


class SortinoRatio(BaseIndicator):
    @property
    def name(self) -> str:
        return "sortino_ratio"

    @property
    def requires(self) -> set:
        return {"annual_return"}

    def calculate(self, curve: pl.Series, cache: Dict) -> float:
        if "sortino_ratio" not in cache:
            if "returns" not in cache:
                cache["returns"] = curve.pct_change()

            # 只考虑负收益的波动率
            negative_returns = cache["returns"].filter(cache["returns"] < 0)
            if len(negative_returns) == 0:
                downside_vol = 0
            else:
                annualization_factor = np.sqrt(365 / cache["total_days"])
                downside_vol = float(negative_returns.std() * annualization_factor)

            cache["sortino_ratio"] = float(
                cache["annual_return"] / downside_vol if downside_vol != 0 else 0
            )
        return cache["sortino_ratio"]


class WinRate(BaseIndicator):
    @property
    def name(self) -> str:
        return "win_rate"

    def calculate(self, curve: pl.Series, cache: Dict) -> float:
        if "win_rate" not in cache:
            if "returns" not in cache:
                cache["returns"] = curve.pct_change()

            total_trades = len(cache["returns"])
            winning_trades = (cache["returns"] > 0).sum()
            cache["win_rate"] = float(
                winning_trades / total_trades if total_trades > 0 else 0
            )
        return cache["win_rate"]
