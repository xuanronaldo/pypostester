from typing import Union, Dict, List
import polars as pl
import pandas as pd
import numpy as np
from pypostester.indicators.registry import registry
from pypostester.indicators.base import BaseIndicator
from pypostester.utils.validation import (
    validate_and_convert_input,
    ValidationError,
    validate_time_alignment,
    validate_commission,
    validate_annual_trading_days,
    validate_indicators,
)


class PositionBacktester:
    def __init__(
        self,
        close_df: Union[pl.DataFrame, pd.DataFrame],
        commission: float = 0.0,
        annual_trading_days: int = 252,
        indicators: Union[str, List[str]] = "all",
    ) -> None:
        try:
            # 验证参数
            validate_commission(commission)
            validate_annual_trading_days(annual_trading_days)
            validate_indicators(indicators, registry.available_indicators)

            # 验证并转换输入数据
            self.close_df = validate_and_convert_input(close_df, data_type="close")
            self.commission = commission
            self.annual_trading_days = annual_trading_days
            self.indicators = indicators

        except ValidationError as e:
            raise ValueError(f"Invalid input: {str(e)}")

    def _calculate_funding_curve(self) -> pl.DataFrame:
        """计算资金曲线"""
        # 计算收益率
        returns = self.df["close"].pct_change().fill_null(0)

        # 计算持仓收益
        position_returns = returns * self.df["position"].shift(1).fill_null(0)

        # 计算换仓成本
        position_changes = self.df["position"].diff().abs().fill_null(0)
        transaction_costs = position_changes * self.commission

        # 计算净收益
        net_returns = position_returns - transaction_costs

        # 计算资金曲线
        funding_curve = (1 + net_returns).cum_prod()

        # 创建结果DataFrame
        result = pl.DataFrame(
            {
                "time": self.df["time"],
                "funding_curve": funding_curve,
                "returns": net_returns,
            }
        )

        return result

    def add_indicator(self, indicator: BaseIndicator) -> None:
        """添加自定义指标"""
        registry.register(indicator)

    def run(self, position_df: Union[pl.DataFrame, pd.DataFrame]) -> Dict:
        """执行回测并返回结果"""
        try:
            # 验证并转换position数据
            position_df = validate_and_convert_input(position_df, data_type="position")

            # 验证时间对齐
            validate_time_alignment(self.close_df, position_df)

            # 合并数据
            self.df = self.close_df.join(
                position_df.select(["time", "position"]), on="time", how="inner"
            ).sort("time")

        except ValidationError as e:
            raise ValueError(f"Invalid position input: {str(e)}")

        # 计算资金曲线
        funding_curve = self._calculate_funding_curve()

        # 准备缓存
        cache = self._prepare_cache(funding_curve)

        # 获取需要计算的指标
        indicators_to_calculate = self._get_indicators_to_calculate()

        # 按依赖关系排序并计算指标
        sorted_indicators = self._sort_indicators_by_dependency(indicators_to_calculate)
        results = self._calculate_indicators(sorted_indicators, cache)

        return {"funding_curve": funding_curve, **results}

    def _prepare_cache(self, funding_curve: pl.DataFrame) -> Dict:
        """准备计算缓存

        Args:
            funding_curve: 包含 time、funding_curve 和 returns 列的 DataFrame

        Returns:
            Dict: 包含计算所需缓存数据的字典
        """
        times = funding_curve.get_column("time")

        # 计算总天数
        total_days = (times[-1] - times[0]).total_seconds() / (24 * 3600)
        total_days = max(total_days, 1)  # 确保至少为1天

        # 计算数据频率（以天为单位）
        time_diffs = times.diff().drop_nulls()
        avg_interval = float(time_diffs.mean().total_seconds()) / (
            24 * 3600
        )  # 转换为天

        # 计算每天的周期数
        periods_per_day = 1 / avg_interval if avg_interval > 0 else 1

        return {
            "curve_df": funding_curve,
            "annual_trading_days": self.annual_trading_days,
            "total_days": total_days,
            "returns": funding_curve.get_column("returns"),
            "periods_per_day": periods_per_day,  # 每天的周期数
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

    def _calculate_indicators(self, sorted_indicators: List[str], cache: Dict) -> Dict:
        """计算指标

        Args:
            sorted_indicators: 按依赖关系排序的指标列表
            cache: 计算缓存

        Returns:
            Dict: 计算结果字典
        """
        return {
            name: registry.get_indicator(name).calculate(cache)
            for name in sorted_indicators
        }

    def get_params(self) -> Dict:
        """获取回测器参数

        Returns:
            Dict: 包含回测器参数的字典，包括：
                - commission: 手续费率
                - annual_trading_days: 年化交易天数
                - indicators: 计算的指标列表
        """
        return {
            "commission": self.commission,
            "annual_trading_days": self.annual_trading_days,
            "indicators": (
                "all" if self.indicators == "all" else list(self.indicators)
            ),
        }
