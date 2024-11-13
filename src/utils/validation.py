from typing import Union, Tuple
import polars as pl
import pandas as pd
import numpy as np
from datetime import datetime


class ValidationError(Exception):
    """验证错误的自定义异常类"""

    pass


def validate_series_input(
    close: Union[pl.Series, pd.Series], position: Union[pl.Series, pd.Series]
) -> None:
    """
    验证输入的价格序列和仓位序列

    Args:
        close: 价格序列
        position: 仓位序列

    Raises:
        ValidationError: 当输入数据不符合要求时
    """
    # 检查数据类型
    valid_types = (pl.Series, pd.Series)
    if not isinstance(close, valid_types):
        raise ValidationError(
            f"close must be either polars.Series or pandas.Series, got {type(close)}"
        )
    if not isinstance(position, valid_types):
        raise ValidationError(
            f"position must be either polars.Series or pandas.Series, got {type(position)}"
        )

    # 检查数据长度
    close_len = len(close)
    position_len = len(position)
    if close_len != position_len:
        raise ValidationError(
            f"close and position must have same length, "
            f"got {close_len} and {position_len}"
        )

    # 检查是否为空
    if close_len == 0:
        raise ValidationError("Input series cannot be empty")

    # 检查是否包含无效值
    if isinstance(close, pd.Series):
        has_invalid_close = close.isna().any()
        has_invalid_position = position.isna().any()
    else:
        has_invalid_close = close.is_null().any()
        has_invalid_position = position.is_null().any()

    if has_invalid_close:
        raise ValidationError("close series contains invalid values")
    if has_invalid_position:
        raise ValidationError("position series contains invalid values")

    # 检查价格是否为正
    if isinstance(close, pd.Series):
        has_negative_close = (close <= 0).any()
    else:
        has_negative_close = (close <= 0).any()

    if has_negative_close:
        raise ValidationError("close series contains non-positive values")


def validate_parameters(commission: float, annual_trading_days: int) -> None:
    """
    验证回测参数

    Args:
        commission: 手续费率
        annual_trading_days: 年度交易日数

    Raises:
        ValidationError: 当参数不符合要求时
    """
    # 验证手续费率
    if not isinstance(commission, (int, float)):
        raise ValidationError(f"commission must be a number, got {type(commission)}")
    if commission < 0:
        raise ValidationError(f"commission cannot be negative, got {commission}")
    if commission >= 1:
        raise ValidationError(
            f"commission cannot be greater than or equal to 1, got {commission}"
        )

    # 验证年度交易日数
    if not isinstance(annual_trading_days, int):
        raise ValidationError(
            f"annual_trading_days must be an integer, got {type(annual_trading_days)}"
        )
    if annual_trading_days <= 0:
        raise ValidationError(
            f"annual_trading_days must be positive, got {annual_trading_days}"
        )


def convert_to_polars(
    close: Union[pl.Series, pd.Series], position: Union[pl.Series, pd.Series]
) -> pl.DataFrame:
    """
    将输入数据转换为 Polars DataFrame

    Args:
        close: 价格序列
        position: 仓位序列

    Returns:
        pl.DataFrame: 包含时间戳、价格和仓位的数据框
    """
    if isinstance(close, pd.Series):
        # 确保索引是时间戳类型
        if not isinstance(close.index, pd.DatetimeIndex):
            raise ValidationError("close series must have datetime index")

        return pl.DataFrame(
            {
                "timestamp": close.index.to_numpy(),
                "close": close.values,
                "position": position.values,
            }
        )
    else:
        # 如果是 Polars Series，确保有正确的索引
        if not hasattr(close, "index"):
            raise ValidationError("close series must have index")

        return pl.DataFrame(
            {"timestamp": close.index, "close": close, "position": position}
        )


def validate_and_convert_input(
    close: Union[pl.Series, pd.Series],
    position: Union[pl.Series, pd.Series],
    commission: float,
    annual_trading_days: int,
) -> Tuple[pl.DataFrame, float, int]:
    """
    验证所有输入并转换数据

    Args:
        close: 价格序列
        position: 仓位序列
        commission: 手续费率
        annual_trading_days: 年度交易日数

    Returns:
        Tuple[pl.DataFrame, float, int]: 转换后的数据框、手续费率和年度交易日数

    Raises:
        ValidationError: 当输入不符合要求时
    """
    # 验证输入序列
    validate_series_input(close, position)

    # 验证参数
    validate_parameters(commission, annual_trading_days)

    # 转换数据
    df = convert_to_polars(close, position)

    return df, commission, annual_trading_days
