from typing import Dict
import polars as pl
from dataclasses import dataclass


@dataclass
class BacktestResult:
    """Backtest result model class"""

    _dataframes: Dict[str, pl.DataFrame]
    _indicator_values: Dict[str, float]
    _formatted_indicator_values: Dict[str, str]

    @property
    def funding_curve(self) -> pl.DataFrame:
        """Get funding curve DataFrame"""
        return self._dataframes["merged_df"].select(
            pl.col("time"), pl.col("funding_curve")
        )

    @property
    def dataframes(self) -> Dict[str, pl.DataFrame]:
        """Get all DataFrames"""
        return self._dataframes

    @property
    def indicator_values(self) -> Dict[str, float]:
        """Get indicator values"""
        return self._indicator_values

    @property
    def formatted_indicator_values(self) -> Dict[str, str]:
        """Get formatted indicator values"""
        return self._formatted_indicator_values

    def get_dataframe(self, indicator: str) -> pl.DataFrame:
        """Get specific DataFrame by indicator name

        Args:
            indicator: Name of the indicator

        Returns:
            DataFrame for the specified indicator
        """
        return self._dataframes[indicator]

    def get_indicator_value(self, indicator: str) -> float:
        """Get specific indicator value

        Args:
            indicator: Name of the indicator

        Returns:
            Raw value of the specified indicator
        """
        return self._indicator_values[indicator]

    def get_formatted_indicator_value(self, indicator: str) -> str:
        """Get specific formatted indicator value

        Args:
            indicator: Name of the indicator

        Returns:
            Formatted value of the specified indicator
        """
        return self._formatted_indicator_values[indicator]

    def print(self) -> None:
        """Print backtest results in tabular format"""
        indicators_df = pl.DataFrame(
            {
                "indicator": list(self.formatted_indicator_values.keys()),
                "value": list(self.formatted_indicator_values.values()),
            }
        )

        print(indicators_df)
