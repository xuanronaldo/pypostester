from typing import Dict
import polars as pl
import numpy as np
from pypostester.indicators.base import BaseIndicator


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
        return {"annual_return"}

    def calculate(self, curve: pl.Series, cache: Dict) -> float:
        if "sharpe_ratio" not in cache:
            if "returns" not in cache:
                cache["returns"] = curve.pct_change()

            annualization_factor = np.sqrt(365 / cache["total_days"])
            cache["annual_vol"] = float(cache["returns"].std() * annualization_factor)

            cache["sharpe_ratio"] = float(
                cache["annual_return"] / cache["annual_vol"]
                if cache["annual_vol"] != 0
                else 0
            )
        return cache["sharpe_ratio"]
