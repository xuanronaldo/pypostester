import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import sys
import warnings

# 忽略特定的废弃警告
warnings.filterwarnings(
    "ignore", category=DeprecationWarning, message="np.find_common_type is deprecated"
)

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from core.backtester import PositionBacktester
from utils.visualization import BacktestVisualizer


def get_btc_data(start_date: datetime, end_date: datetime) -> tuple:
    """
    获取BTC历史数据

    Args:
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        tuple: (收盘价序列, 仓位序列)
    """
    try:
        # 使用yfinance获取BTC数据
        btc = yf.download("BTC-USD", start=start_date, end=end_date, progress=False)

        # 提取收盘价
        close = pd.Series(data=btc["Close"].values, index=btc.index, name="close")

        # 生成全1仓位
        position = pd.Series(data=[1.0] * len(close), index=btc.index, name="position")

        return close, position

    except Exception as e:
        raise RuntimeError(f"Failed to download BTC data: {str(e)}")


def run_backtest(
    close: pd.Series,
    position: pd.Series,
    commission: float = 0.001,
    annual_trading_days: int = 365,
    output_dir: str = "output",
    lang: str = "zh_CN",
) -> None:
    """
    运行回测并生成报告

    Args:
        close: 收盘价序列
        position: 仓位序列
        commission: 手续费率
        annual_trading_days: 年化交易日数
        output_dir: 输出目录
        lang: 语言代码，支持 'zh_CN' 和 'en_US'
    """
    try:
        # 创建输出目录
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # 创建回测器实例
        backtester = PositionBacktester(
            close=close,
            position=position,
            commission=commission,
            annual_trading_days=annual_trading_days,
            indicators="all",
        )

        # 运行回测
        results = backtester.run()

        # 打印主要指标
        print("\n=== 回测结果 ===")
        print(f"年化收益率: {results['annual_return']:.2%}")
        print(f"夏普比率: {results['sharpe_ratio']:.2f}")
        print(f"最大回撤: {results['max_drawdown']:.2%}")
        print(f"最大回撤持续期: {results['max_drawdown_duration']:.0f}天")
        print(f"年化波动率: {results['volatility']:.2%}")
        print(f"胜率: {results['win_rate']:.2%}")

        # 生成可视化报告
        visualizer = BacktestVisualizer(results, backtester)
        report_name = f"btc_backtest_report.html"
        report_path = output_path / report_name
        visualizer.generate_html_report(str(report_path))

        print(f"\n报告已生成: {report_path}")

    except Exception as e:
        print(f"回测过程出错: {str(e)}")
        raise


def main():
    """主函数"""
    # 设置回测时间范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * 2)  # 最近两年

    # 获取数据
    close, position = get_btc_data(start_date, end_date)

    # 运行英文回测
    run_backtest(
        close=close,
        position=position,
        commission=0.001,  # 0.1% 手续费
        annual_trading_days=365,  # 加密货币全年交易
        output_dir="examples/output",
    )


if __name__ == "__main__":
    main()
