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
    def calculate(self, cache: Dict) -> Union[float, str, pl.DataFrame]:
        """计算指标值"""
        pass
