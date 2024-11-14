from typing import Dict, Type
import inspect
from pathlib import Path
from importlib import import_module
from pypostester.indicators.base import BaseIndicator


class IndicatorRegistry:
    """指标注册管理器"""

    def __init__(self):
        self._indicators: Dict[str, BaseIndicator] = {}

    def register(self, indicator: BaseIndicator) -> None:
        """注册新指标"""
        self._indicators[indicator.name] = indicator

    def get_indicator(self, name: str) -> BaseIndicator:
        """获取指标实例"""
        if name not in self._indicators:
            raise KeyError(f"Indicator '{name}' not found")
        return self._indicators[name]

    def get_all_indicators(self) -> Dict[str, BaseIndicator]:
        """获取所有注册的指标"""
        return self._indicators.copy()

    @property
    def available_indicators(self) -> list:
        """获取所有可用的指标名称"""
        return list(self._indicators.keys())


# 创建全局注册器实例
registry = IndicatorRegistry()


def register_builtin_indicators():
    """注册内置指标"""

    def is_indicator_class(obj: Type) -> bool:
        return (
            inspect.isclass(obj)
            and issubclass(obj, BaseIndicator)
            and obj != BaseIndicator
        )

    # 手动导入模块
    from pypostester.indicators import returns
    from pypostester.indicators import risks

    # 遍历模块中的所有类
    for module in [returns, risks]:
        for name, obj in inspect.getmembers(module, is_indicator_class):
            registry.register(obj())


# 注册内置指标
register_builtin_indicators()
