from pypostester import (
    BaseFigure,
    figure_registry,
    PositionBacktester,
    BacktestVisualizer,
)
from utils import read_test_data
import plotly.graph_objects as go


class DrawdownFigure(BaseFigure):
    """Drawdown visualization figure"""

    name = "drawdown"  # Unique identifier for the figure
    title = "Strategy Drawdown"  # Display title for the figure

    def create(self) -> go.Figure:
        """Create drawdown figure

        Returns:
            Plotly figure object containing drawdown visualization
        """
        # Calculate cumulative maximum of funding curve
        cummax = self.funding_curve.get_column("funding_curve").cum_max()

        # Calculate drawdown as percentage from peak
        drawdown = (self.funding_curve.get_column("funding_curve") - cummax) / cummax

        # Add drawdown trace to figure
        self._fig.add_trace(
            go.Scatter(
                x=self.funding_curve.get_column("time"),
                y=drawdown,
                fill="tozeroy",  # Fill area from line to zero
                name="drawdown",
                line=dict(color="red"),
            )
        )

        # Update layout with percentage formatting
        self._fig.update_layout(
            yaxis=dict(
                tickformat=".1%",  # Format y-axis ticks as percentages
                hoverformat=".2%",  # Format hover text as percentages
            ),
        )
        return self._fig


# Register custom figure
figure_registry.register(DrawdownFigure)

# Print available figures
print(figure_registry.available_figures)

# Read test data
close_df, position_df = read_test_data()

# Initialize backtester
backtester = PositionBacktester(
    close_df=close_df,
    commission=0.0005,  # 0.05% commission rate
    annual_trading_days=365,  # Use 365 trading days per year
    indicators="all",  # Calculate all available indicators
)

# Run backtest
backtest_result = backtester.run(position_df)

# Print results
backtest_result.print()

# Create visualizer and show results in browser
visualizer = BacktestVisualizer(backtest_result, backtester.params)
visualizer.show_in_browser()
