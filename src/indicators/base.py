from abc import ABC, abstractmethod
from typing import Dict
import polars as pl


class BaseIndicator(ABC):
    """指标基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """指标名称"""
        pass

    @abstractmethod
    def calculate(self, curve: pl.Series, cache: Dict) -> float:
        """计算指标值"""
        pass

    @property
    def requires(self) -> set:
        """返回该指标依赖的其他指标名称"""
        return set()
