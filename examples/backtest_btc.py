import polars as pl
import pandas as pd
import time
from datetime import datetime
from pathlib import Path
from pypostester import PositionBacktester
from pypostester import BacktestVisualizer


def load_btc_data(data_path: Path) -> tuple:
    """
    从HDF文件加载BTC数据

    Args:
        data_path: HDF文件路径

    Returns:
        tuple: (收盘价DataFrame, 仓位DataFrame)
    """
    try:
        # 读取HDF文件
        df = pd.read_hdf(data_path)

        # 创建收盘价DataFrame
        close_df = pl.DataFrame(
            {
                "time": df.index.to_numpy("datetime64[ms]"),
                "close": df["close"].to_numpy("float64"),
            }
        )

        # 创建仓位DataFrame（示例使用全1仓位）
        position_df = pl.DataFrame(
            {
                "time": df.index.to_numpy("datetime64[ms]"),
                "position": pl.Series([1.0] * len(df), dtype=pl.Float64),
            }
        )

        return close_df, position_df

    except Exception as e:
        raise RuntimeError(f"加载BTC数据失败: {str(e)}")


def run_backtest(
    close_df: pl.DataFrame,
    position_df: pl.DataFrame,
    commission: float = 0.001,
    annual_trading_days: int = 365,
    output_dir: str = "output",
) -> None:
    """
    运行回测并生成报告

    Args:
        close_df: 包含time和close列的DataFrame
        position_df: 包含time和position列的DataFrame
        commission: 手续费率
        annual_trading_days: 年化交易日数
        output_dir: 输出目录
    """
    try:
        start_time = time.time()
        # 创建输出目录
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # 创建回测器实例
        backtester = PositionBacktester(
            close_df=close_df,
            commission=commission,
            annual_trading_days=annual_trading_days,
            indicators="all",
        )

        # 运行回测
        results = backtester.run(position_df)

        # 打印主要指标
        print("\n=== 回测结果 ===")
        print(f"年化收益率: {results['annual_return']:.2%}")
        print(f"夏普比率: {results['sharpe_ratio']:.2f}")
        print(f"最大回撤: {results['max_drawdown']:.2%}")
        print(f"最大回撤持续期: {results['max_drawdown_duration']:.0f}天")
        print(f"年化波动率: {results['volatility']:.2%}")
        print(f"胜率: {results['win_rate']:.2%}")

        # 生成可视化报告
        visualizer = BacktestVisualizer(results, backtester.get_params())
        report_name = f"btc_backtest_report.html"
        report_path = output_path / report_name
        visualizer.generate_html_report(str(report_path))

        print(f"\n报告已生成: {report_path}")

        end_time = time.time()  # 记录结束时间
        elapsed_time = end_time - start_time  # 计算运行时间
        print(f"运行时间: {elapsed_time:.2f}秒")  # 打印运行时间

    except Exception as e:
        print(f"回测过程出错: {str(e)}")
        raise


def main():
    """主函数"""
    # 设置数据文件路径
    project_root = Path(__file__).parent.parent
    data_path = project_root / "data" / "BTCUSDT-SWAP_15m.hdf"

    # 加载数据
    close_df, position_df = load_btc_data(data_path)

    # 运行回测
    run_backtest(
        close_df=close_df,
        position_df=position_df,
        commission=0.001,  # 0.1% 手续费
        annual_trading_days=365,  # 加密货币全年交易
        output_dir="examples/output",
    )


if __name__ == "__main__":
    main()
