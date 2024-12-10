"""PyPostester - A Position-Based Backtesting Framework"""

from pypostester.core.backtester import PositionBacktester
from pypostester.indicators.base import BaseIndicator
from pypostester.visualization.visualizer import BacktestVisualizer
from pypostester.indicators.registry import indicator_registry
from pypostester.models.models import BacktestResult
from pypostester.visualization.registry import figure_registry
from pypostester.visualization.base import BaseFigure

__all__ = [
    "PositionBacktester",
    "BaseIndicator",
    "BacktestVisualizer",
    "indicator_registry",
    "BacktestResult",
    "figure_registry",
    "BaseFigure",
]
