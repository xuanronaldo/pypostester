from typing import Dict
import polars as pl
from dataclasses import dataclass


@dataclass
class BacktestResult:
    """回测结果模型类"""

    dataframes: Dict[str, pl.DataFrame]
    indicator_values: Dict[str, float]
    formatted_indicator_values: Dict[str, str]

    @property
    def funding_curve(self) -> pl.DataFrame:
        """获取资金曲线DataFrame"""
        return self.dataframes["funding_curve"]

    @property
    def get_dataframes(self) -> Dict[str, pl.DataFrame]:
        """获取所有数据框"""
        return self.dataframes

    @property
    def get_dataframe(self, indicator: str) -> pl.DataFrame:
        """获取指定数据框"""
        return self.dataframes[indicator]

    @property
    def get_indicator_values(self) -> Dict[str, float]:
        """获取指标值"""
        return self.indicator_values

    @property
    def get_formatted_indicator_values(self) -> Dict[str, str]:
        """获取格式化指标值"""
        return self.formatted_indicator_values

    @property
    def get_indicator_value(self, indicator: str) -> float:
        """获取指标值"""
        return self.indicator_values[indicator]

    @property
    def get_formatted_indicator_value(self, indicator: str) -> str:
        """获取格式化指标值"""
        return self.formatted_indicator_values[indicator]

    def print(self) -> None:
        """打印回测结果，以表格形式展示指标值"""
        indicators_df = pl.DataFrame(
            {
                "indicator": list(self.formatted_indicator_values.keys()),
                "value": list(self.formatted_indicator_values.values()),
            }
        )

        print(indicators_df)
