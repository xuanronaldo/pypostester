from pypostester import PositionBacktester
from pypostester import BacktestVisualizer
from examples.utils import read_test_data

# Read test data (close prices and positions)
close_df, position_df = read_test_data()

# Initialize backtester with parameters
backtester = PositionBacktester(
    close_df=close_df,
    commission=0.0005,  # 0.05% commission rate
    annual_trading_days=365,  # Use 365 trading days per year
    indicators="all",  # Calculate all available indicators
)

# Run backtest
backtest_result = backtester.run(position_df)

# Print backtest results in tabular format
backtest_result.print()

# Create visualizer and show results in browser
visualizer = BacktestVisualizer(backtest_result, backtester.params)
visualizer.show_in_browser()
