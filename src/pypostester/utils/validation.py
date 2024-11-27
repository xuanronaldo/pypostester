"""Data validation utilities"""

from typing import Union, Literal, List
import polars as pl
import pandas as pd
from pypostester.core.constants import REQUIRED_COLUMNS


class ValidationError(Exception):
    """数据验证错误"""

    pass


def validate_commission(commission: float) -> None:
    """验证交易成本

    Args:
        commission: 交易成本率

    Raises:
        ValidationError: 当交易成本无效时
    """
    if not isinstance(commission, (int, float)):
        raise ValidationError("Commission must be a number")
    if commission < 0 or commission > 1:
        raise ValidationError("Commission must be between 0 and 1")


def validate_annual_trading_days(days: int) -> None:
    """验证年化交易日数

    Args:
        days: 年化交易日数

    Raises:
        ValidationError: 当交易日数无效时
    """
    if not isinstance(days, int):
        raise ValidationError("Annual trading days must be an integer")
    if days <= 0:
        raise ValidationError("Annual trading days must be positive")
    if days > 365:
        raise ValidationError("Annual trading days cannot exceed 365")


def validate_indicators(
    indicators: Union[str, List[str]], available_indicators: List[str]
) -> None:
    """验证指标参数

    Args:
        indicators: 指标名称或列表
        available_indicators: 可用指标列表

    Raises:
        ValidationError: 当指标参数无效时
    """
    if indicators != "all" and not isinstance(indicators, (list, tuple)):
        raise ValidationError("Indicators must be 'all' or a list of indicator names")

    if isinstance(indicators, (list, tuple)):
        invalid_indicators = [
            name for name in indicators if name not in available_indicators
        ]
        if invalid_indicators:
            raise ValidationError(
                f"Invalid indicator names: {invalid_indicators}. "
                f"Available indicators: {available_indicators}"
            )


def validate_and_convert_input(
    df: Union[pl.DataFrame, pd.DataFrame], data_type: Literal["close", "position"]
) -> pl.DataFrame:
    """验证并转换输入数据

    Args:
        df: 输入数据框
        data_type: 数据类型，'close' 或 'position'

    Returns:
        pl.DataFrame: 验证并转换后的 Polars DataFrame

    Raises:
        ValidationError: 当数据不符合要求时
    """
    try:
        # 转换为 Polars DataFrame
        if isinstance(df, pd.DataFrame):
            df = pl.from_pandas(df)

        # 验证必需列
        required_cols = REQUIRED_COLUMNS[data_type]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValidationError(f"Missing required columns: {missing_cols}")

        # 验证时间列类型
        if not pl.Series(df["time"]).dtype.is_temporal():
            raise ValidationError("Time column must be datetime type")

        # 验证时间排序
        if not pl.Series(df["time"]).is_sorted():
            df = df.sort("time")

        # 验证持仓值范围（如果是持仓数据）
        if data_type == "position":
            position_values = df["position"]
            if (position_values < -1).any() or (position_values > 1).any():
                raise ValidationError("Position values must be between -1 and 1")

        return df

    except Exception as e:
        if not isinstance(e, ValidationError):
            raise ValidationError(f"Data validation failed: {str(e)}")
        raise


def validate_time_alignment(close_df: pl.DataFrame, position_df: pl.DataFrame) -> None:
    """验证时间对齐

    Args:
        close_df: 价格数据
        position_df: 仓位数据

    Raises:
        ValidationError: 当时间戳不对齐时
    """
    close_times = set(close_df["time"])
    position_times = set(position_df["time"])

    if close_times != position_times:
        raise ValidationError("Close and position data must have identical timestamps")
