from typing import Dict
import polars as pl
import numpy as np
from pypostester.indicators.base import BaseIndicator
from pypostester.indicators.risks import Volatility


class AnnualReturn(BaseIndicator):
    @property
    def name(self) -> str:
        return "annual_return"

    def calculate(self, curve: pl.Series, cache: Dict) -> float:
        if "annual_return" not in cache:
            total_return = float(curve.tail(1)[0] / curve[0])
            cache["annual_return"] = float(
                (total_return ** (365 / cache["total_days"])) - 1
            )
        return cache["annual_return"]


class SharpeRatio(BaseIndicator):
    @property
    def name(self) -> str:
        return "sharpe_ratio"

    @property
    def requires(self) -> set:
        return {"annual_return", "volatility"}

    def calculate(self, curve: pl.Series, cache: Dict) -> float:
        if "sharpe_ratio" not in cache:
            if "volatility" not in cache:
                volatility_indicator = Volatility()
                cache["volatility"] = volatility_indicator.calculate(curve, cache)

            annual_vol = cache["volatility"]

            cache["sharpe_ratio"] = float(
                cache["annual_return"] / annual_vol if annual_vol != 0 else 0
            )
        return cache["sharpe_ratio"]
