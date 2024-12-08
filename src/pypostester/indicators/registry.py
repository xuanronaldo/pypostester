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
                self.register(obj(), update_dependency=False)
        self._sort_indicators_by_dependency()

    def _sort_indicators_by_dependency(self) -> None:
        """根据依赖关系对指标进行排序"""
        sorted_indicators = []
        visited = set()

        def visit(indicator_name):
            if indicator_name in visited:
                return
            visited.add(indicator_name)
            indicator_class = self._indicators[indicator_name]
            # 获取依赖关系
            dependencies = indicator_class().requires
            for dep in dependencies:
                if dep in self._indicators:
                    visit(dep)
            sorted_indicators.append(indicator_name)

        for name in self._indicators:
            visit(name)

        # 更新 _indicators 的顺序
        self._sorted_indicators = sorted_indicators

    def register(
        self, indicator: BaseIndicator, update_dependency: bool = True
    ) -> None:
        """注册新指标"""
        self._indicators[indicator.name] = indicator.__class__
        if update_dependency:
            self._sort_indicators_by_dependency()

    def get_indicator(self, name: str) -> BaseIndicator:
        """获取指标实例"""
        if name not in self._indicators:
            raise ValueError(f"Unknown indicator: {name}")
        return self._indicators[name]()

    @property
    def available_indicators(self) -> List[str]:
        """获取所有可用指标名称"""
        return sorted(self._indicators.keys())

    @property
    def sorted_indicators(self) -> Dict[str, Type[BaseIndicator]]:
        """获取所有指标实例，按依赖关系排序"""
        return self._sorted_indicators


# 全局指标注册器实例
registry = IndicatorRegistry()
