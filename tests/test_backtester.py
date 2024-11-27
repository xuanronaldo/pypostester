import unittest
import polars as pl
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import sys
import warnings
import numpy as np

# 忽略特定的废弃警告
warnings.filterwarnings(
    "ignore", category=DeprecationWarning, message="np.find_common_type is deprecated"
)

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from pypostester.core.backtester import PositionBacktester
from pypostester.utils.visualization import BacktestVisualizer


class TestBacktester(unittest.TestCase):
    """回测系统测试类"""

    @classmethod
    def setUpClass(cls):
        """测试类初始化，加载BTC数据"""
        # 加载BTC数据
        cls.load_btc_data()

        # 设置输出路径
        cls.output_dir = Path(__file__).parent / "output"
        cls.output_dir.mkdir(exist_ok=True)

    @classmethod
    def load_btc_data(cls):
        """从HDF文件加载BTC数据"""
        try:
            # 读取HDF文件
            data_path = project_root / "data" / "BTCUSDT-SWAP_1h.hdf"
            df = pd.read_hdf(data_path)

            # 准备收盘价数据
            cls.close_df = pl.DataFrame(
                {
                    "time": df.index.to_numpy("datetime64[ms]"),
                    "close": df["close"].to_numpy("float64"),
                }
            )

            # 准备买入持有的仓位数据
            cls.position_df = pl.DataFrame(
                {
                    "time": df.index.to_numpy("datetime64[ms]"),
                    "position": np.full(len(df), 1.0, dtype="float64"),  # 买入持有
                }
            )

        except Exception as e:
            raise RuntimeError(f"Failed to load BTC data: {str(e)}")

    def test_basic_backtest(self):
        """测试基本回测功能"""
        try:
            # 创建回测器实例
            backtester = PositionBacktester(
                close_df=self.close_df,
                commission=0.001,  # 0.1% 手续费
                annual_trading_days=365,  # 加密货币全年交易
                indicators="all",
            )

            # 运行回测
            results = backtester.run(self.position_df)

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
        # 测试缺失必需列
        invalid_df = pl.DataFrame({"time": self.close_df["time"]})  # 缺少 close 列
        with self.assertRaises(ValueError):
            PositionBacktester(close_df=invalid_df)

        # 测试时间不对齐
        misaligned_position = self.position_df.slice(
            0, len(self.position_df) - 1
        )  # 删除最后一行
        backtester = PositionBacktester(close_df=self.close_df)
        with self.assertRaises(ValueError):
            backtester.run(misaligned_position)

        # 测试无效的持仓值
        invalid_position = self.position_df.with_columns(
            pl.col("position").map_elements(
                lambda x: 2.0, return_dtype=pl.Float64  # 明确指定返回类型
            )
        )
        with self.assertRaises(ValueError):
            backtester.run(invalid_position)


if __name__ == "__main__":
    unittest.main(verbosity=2)
