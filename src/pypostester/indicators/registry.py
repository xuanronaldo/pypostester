from typing import Dict, Type, List
import inspect
from pypostester.indicators.base import BaseIndicator
from pypostester.indicators import indicators


class IndicatorRegistry:
    """指标注册器"""

    def __init__(self):
        self._indicators: Dict[str, Type[BaseIndicator]] = {}
        self._register_builtin_indicators()

    def _register_builtin_indicators(self) -> None:
        """自动注册所有内置指标"""
        # 获取 indicators 模块中的所有成员
        for name, obj in inspect.getmembers(indicators):
            # 检查是否是类且是 BaseIndicator 的子类
            if (
                inspect.isclass(obj)
                and issubclass(obj, BaseIndicator)
                and obj != BaseIndicator
            ):
                self.register(obj())

    def register(self, indicator: BaseIndicator) -> None:
        """注册新指标"""
        self._indicators[indicator.name] = indicator.__class__

    def get_indicator(self, name: str) -> BaseIndicator:
        """获取指标实例"""
        if name not in self._indicators:
            raise ValueError(f"Unknown indicator: {name}")
        return self._indicators[name]()

    @property
    def available_indicators(self) -> List[str]:
        """获取所有可用指标名称"""
        return sorted(self._indicators.keys())


# 全局指标注册器实例
registry = IndicatorRegistry()
