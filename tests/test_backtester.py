import unittest
import polars as pl
import pandas as pd
import yfinance as yf
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


class TestBacktester(unittest.TestCase):
    """回测系统测试类"""

    @classmethod
    def setUpClass(cls):
        """测试类初始化，获取BTC数据"""
        # 获取BTC数据
        cls.get_btc_data()

        # 设置输出路径
        cls.output_dir = Path(__file__).parent / "output"
        cls.output_dir.mkdir(exist_ok=True)

    @classmethod
    def get_btc_data(cls):
        """获取BTC历史数据"""
        # 获取最近两年的BTC数据
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365 * 2)

        try:
            # 使用yfinance获取BTC数据
            btc = yf.download("BTC-USD", start=start_date, end=end_date, progress=False)

            # 转换为polars.DataFrame
            cls.df = pl.from_pandas(btc)

            # 提取收盘价和时间戳
            cls.close = pd.Series(
                data=btc["Close"].values, index=btc.index, name="close"
            )

            # 生成全1仓位
            cls.position = pd.Series(
                data=[1.0] * len(cls.close), index=btc.index, name="position"
            )

        except Exception as e:
            raise RuntimeError(f"Failed to download BTC data: {str(e)}")

    def test_basic_backtest(self):
        """测试基本回测功能"""
        try:
            # 创建回测器实例
            backtester = PositionBacktester(
                close=self.close,
                position=self.position,
                commission=0.001,
                annual_trading_days=365,
                indicators="all",
            )

            # 运行回测
            results = backtester.run()

            # 基本断言
            self.assertIn("funding_curve", results)
            self.assertIn("annual_return", results)
            self.assertIn("sharpe_ratio", results)
            self.assertIn("max_drawdown", results)

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
            report_path = self.output_dir / "btc_backtest_report.html"
            visualizer.generate_html_report(str(report_path))

            # 确认报告文件已生成
            self.assertTrue(report_path.exists())
            print(f"\n报告已生成: {report_path}")

        except Exception as e:
            self.fail(f"回测过程出错: {str(e)}")

    def test_invalid_inputs(self):
        """测试无效输入"""
        # 测试负的手续费率
        with self.assertRaises(ValueError):
            PositionBacktester(
                close=self.close, position=self.position, commission=-0.001
            )

        # 测试无效的年度交易日数
        with self.assertRaises(ValueError):
            PositionBacktester(
                close=self.close, position=self.position, annual_trading_days=0
            )

        # 测试长度不匹配的输入
        with self.assertRaises(ValueError):
            PositionBacktester(close=self.close, position=self.position[:-1])  # 长度少1


if __name__ == "__main__":
    unittest.main(verbosity=2)
