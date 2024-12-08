from typing import Union, Dict, List
import polars as pl
import pandas as pd
from pypostester.indicators.registry import registry
from pypostester.indicators.base import BaseIndicator
from pypostester.utils.validation import (
    validate_and_convert_input,
    ValidationError,
    validate_time_alignment,
    validate_commission,
    validate_annual_trading_days,
    validate_indicators,
    validate_data_type,
)
from pypostester.models.models import BacktestResult


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
            self.sorted_indicators = validate_indicators(indicators)

            # 验证并转换输入数据
            self.close_df = validate_and_convert_input(close_df, data_type="close")
            self.commission = commission
            self.annual_trading_days = annual_trading_days
            self.indicators = indicators

        except ValidationError as e:
            raise ValueError(f"Invalid input: {str(e)}")

    def _calculate_funding_curve(self, merged_df: pl.DataFrame) -> pl.DataFrame:
        """计算资金曲线"""
        # 计算收益率
        returns = merged_df["close"].pct_change().fill_null(0)

        # 计算持仓收益
        position_returns = returns * merged_df["position"].shift(1).fill_null(0)

        # 计算换仓成本
        position_changes = merged_df["position"].diff().abs().fill_null(0)
        transaction_costs = position_changes * self.commission

        # 计算净收益
        net_returns = position_returns - transaction_costs

        # 计算资金曲线
        funding_curve = (1 + net_returns).cum_prod()

        # 创建结果DataFrame
        result = pl.DataFrame(
            {
                "time": merged_df["time"],
                "funding_curve": funding_curve,
                "returns": net_returns,
            }
        )

        return result

    def add_indicator(self, indicator: BaseIndicator) -> None:
        """添加自定义指标"""
        registry.register(indicator)

    def run(self, position_df: Union[pl.DataFrame, pd.DataFrame]) -> BacktestResult:
        """执行回测并返回结果

        Args:
            position_df: 包含仓位数据的DataFrame

        Returns:
            BacktestResult: 回测结果对象
        """
        try:
            # 验证并转换position数据
            position_df = validate_and_convert_input(position_df, data_type="position")

            # 验证时间对齐
            validate_time_alignment(self.close_df, position_df)

            # 合并数据并作为局部变量
            merged_df = self.close_df.join(
                position_df.select(["time", "position"]), on="time", how="inner"
            ).sort("time")

        except ValidationError as e:
            raise ValueError(f"Invalid position input: {str(e)}")

        # 计算资金曲线
        funding_curve = self._calculate_funding_curve(merged_df)

        # 准备缓存
        cache = self._prepare_cache(funding_curve)

        # 计算指标
        results = self._calculate_indicators(cache)

        # 将results分成两个字典
        dataframes = {k: v[k] for k, v in results["dataframes"].items()}
        indicators = {k: v["value"] for k, v in results["indicators"].items()}
        formatted_indicators = {
            k: v["formatted_value"] for k, v in results["indicators"].items()
        }

        # 创建并返回BacktestResult对象
        return BacktestResult(
            dataframes={"funding_curve": funding_curve, **dataframes},
            indicator_values=indicators,
            formatted_indicator_values=formatted_indicators,
        )

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

    def _calculate_indicators(self, cache: Dict) -> Dict:
        """计算指标

        Args:
            sorted_indicators: 按依赖关系排的指标列表
            cache: 计算缓存

        Returns:
            Dict: 计算结果字典
        """
        result = dict()
        result["dataframes"] = dict()
        result["indicators"] = dict()
        for indicator in self.sorted_indicators:
            value = validate_data_type(
                registry.get_indicator(indicator).calculate(cache)
            )
            if isinstance(value, pl.DataFrame):
                result["dataframes"][indicator] = value
            else:
                formatted_value = registry.get_indicator(indicator).format(value)
                result["indicators"][indicator] = {
                    "value": value,
                    "formatted_value": formatted_value,
                }
        return result

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
                "all" if self.indicators == "all" else list(self.sorted_indicators)
            ),
        }
