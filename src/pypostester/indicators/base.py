from abc import ABC, abstractmethod
from typing import Dict, Set, Union
import polars as pl


class BaseIndicator(ABC):
    """指标基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """指标名称"""
        pass

    @property
    def requires(self) -> Set[str]:
        """依赖的其他指标"""
        return set()

    @abstractmethod
    def calculate(self, cache: Dict) -> Union[float, pl.DataFrame]:
        """计算指标值"""
        pass

    @abstractmethod
    def format(self, value: float) -> str:
        """格式化指标值

        Args:
            value: 需要格式化的指标值

        Returns:
            格式化后的字符串
        """
        pass
