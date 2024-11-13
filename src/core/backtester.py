from typing import Union, Dict, List
import polars as pl
import pandas as pd
import numpy as np
from indicators.registry import registry
from indicators.base import BaseIndicator
from utils.validation import validate_and_convert_input, ValidationError


class PositionBacktester:
    def __init__(
        self,
        close: Union[pl.Series, pd.Series],
        position: Union[pl.Series, pd.Series],
        commission: float = 0.0,
        annual_trading_days: int = 252,
        indicators: Union[str, List[str]] = "all",
    ) -> None:
        try:
            # 验证并转换输入数据
            self.df, self.commission, self.annual_trading_days = (
                validate_and_convert_input(
                    close, position, commission, annual_trading_days
                )
            )
        except ValidationError as e:
            raise ValueError(f"Invalid input: {str(e)}")

        self.indicators = indicators

    def _calculate_funding_curve(self) -> pl.DataFrame:
        """
        计算资金曲线

        Returns:
            pl.DataFrame: 包含时间戳和资金曲线的数据框
        """
        # 计算收益率
        returns = self.df["close"].pct_change().fill_null(0)

        # 计算持仓收益
        position_returns = returns * self.df["position"].shift(1).fill_null(0)

        # 计算换仓成本
        position_changes = self.df["position"].diff().abs().fill_null(0)
        transaction_costs = position_changes * self.commission

        # 计算净收益
        net_returns = position_returns - transaction_costs

        # 计算资金曲线 (使用 Polars 的 cumulative_eval 方法)
        funding_curve = (1 + net_returns).cum_prod()

        # 创建结果DataFrame
        result = pl.DataFrame(
            {
                "timestamp": self.df["timestamp"],
                "funding_curve": funding_curve,
                "returns": net_returns,
            }
        )

        return result

    def add_indicator(self, indicator: BaseIndicator) -> None:
        """添加自定义指标"""
        registry.register(indicator)

    def run(self) -> Dict:
        """执行回测并返回结果"""
        # 计算资金曲线
        funding_curve = self._calculate_funding_curve()
        curve_series = funding_curve.select("funding_curve").get_column("funding_curve")

        # 准备缓存
        cache = self._prepare_cache(funding_curve)

        # 获取需要计算的指标
        indicators_to_calculate = self._get_indicators_to_calculate()

        # 按依赖关系排序并计算指标
        sorted_indicators = self._sort_indicators_by_dependency(indicators_to_calculate)
        results = self._calculate_indicators(sorted_indicators, curve_series, cache)

        return {"funding_curve": funding_curve, **results}

    def _prepare_cache(self, funding_curve: pl.DataFrame) -> Dict:
        """准备计算缓存"""
        timestamps = funding_curve.get_column("timestamp")
        total_days = max((timestamps[-1] - timestamps[0]).days, 1)

        return {
            "annual_trading_days": self.annual_trading_days,
            "funding_curve": funding_curve,
            "total_days": total_days,
            "returns": funding_curve.get_column("returns"),
        }

    def _get_indicators_to_calculate(self) -> List[str]:
        """获取需要计算的指标列表"""
        available_indicators = registry.available_indicators

        if self.indicators == "all":
            return available_indicators

        # 验证指标名称
        invalid_indicators = [
            name for name in self.indicators if name not in available_indicators
        ]
        if invalid_indicators:
            raise ValueError(
                f"Invalid indicator names: {invalid_indicators}. "
                f"Available indicators: {available_indicators}"
            )

        return self.indicators

    def _sort_indicators_by_dependency(self, indicators: List[str]) -> List[str]:
        """根据依赖关系排序指标"""
        # 简单的拓扑排序实现
        sorted_indicators = []
        visited = set()

        def visit(name):
            if name in visited:
                return
            visited.add(name)
            indicator = registry.get_indicator(name)
            for dep in indicator.requires:
                visit(dep)
            sorted_indicators.append(name)

        for name in indicators:
            visit(name)

        return sorted_indicators

    def _calculate_indicators(
        self, sorted_indicators: List[str], curve: pl.Series, cache: Dict
    ) -> Dict:
        """计算指标"""
        return {
            name: registry.get_indicator(name).calculate(curve, cache)
            for name in sorted_indicators
        }
