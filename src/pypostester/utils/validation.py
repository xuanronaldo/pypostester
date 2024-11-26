"""Data validation utilities"""

from typing import Union, Literal
import polars as pl
import pandas as pd
from pypostester.core.constants import REQUIRED_COLUMNS


class ValidationError(Exception):
    """数据验证错误"""

    pass


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

        # 验证时间列
        if not pl.Series(df["time"]).is_sorted():
            df = df.sort("time")

        return df

    except Exception as e:
        raise ValidationError(f"Data validation failed: {str(e)}")


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
