from typing import Dict
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import polars as pl
from datetime import datetime
import os
from pathlib import Path
from string import Template
from core.backtester import PositionBacktester


class BacktestVisualizer:
    """回测结果可视化器"""

    def __init__(self, results: Dict, backtester: PositionBacktester):
        """
        初始化可视化器

        Args:
            results: 回测结果字典
            backtester: 回测器实例，用于获取回测参数
        """
        self.results = results
        self.backtester = backtester
        self.funding_curve = results["funding_curve"]

        # 获取模板文件路径
        self.template_path = (
            Path(__file__).parent.parent / "templates" / "report_template.html"
        )
        if not self.template_path.exists():
            raise FileNotFoundError(f"Template file not found: {self.template_path}")

    def _generate_backtest_params_html(self) -> str:
        """生成回测参数HTML"""
        params = {
            "手续费率": f"{self.backtester.commission:.3%}",
            "年化交易日": f"{self.backtester.annual_trading_days}天",
            "计算指标": (
                "全部"
                if self.backtester.indicators == "all"
                else ", ".join(self.backtester.indicators)
            ),
        }

        return "\n".join(
            f'<div class="info-item"><span style="color: #666;">{k}:</span> {v}</div>'
            for k, v in params.items()
        )

    def _generate_data_info_html(self) -> str:
        """生成数据信息HTML"""
        df = self.funding_curve.to_pandas()
        start_date = df["timestamp"].min().strftime("%Y-%m-%d")
        end_date = df["timestamp"].max().strftime("%Y-%m-%d")
        total_days = (df["timestamp"].max() - df["timestamp"].min()).days

        info = {
            "回测起始日期": start_date,
            "回测结束日期": end_date,
            "回测天数": f"{total_days}天",
            "数据点数": f"{len(df):,}个",
        }

        return "\n".join(
            f'<div class="info-item"><span style="color: #666;">{k}:</span> {v}</div>'
            for k, v in info.items()
        )

    def create_funding_curve_figure(self) -> go.Figure:
        """创建资金曲线图"""
        df = self.funding_curve.to_pandas()

        fig = go.Figure()

        # 添加资金曲线
        fig.add_trace(
            go.Scatter(
                x=df["timestamp"],
                y=df["funding_curve"],
                name="资金曲线",
                line=dict(color="#1f77b4"),
            )
        )

        # 添加最大回撤阴影
        if "max_drawdown" in self.results:
            # 计算滚动最大值
            cummax = df["funding_curve"].cummax()
            drawdown = (df["funding_curve"] - cummax) / cummax

            # 找到最大回撤结束点（最低点）
            max_dd_end_idx = drawdown.idxmin()

            # 找到最大回撤开始点（之前的最高点）
            max_dd_start_idx = df["funding_curve"][:max_dd_end_idx].idxmax()

            # 创建回撤区间的数据
            dd_region = df[max_dd_start_idx : max_dd_end_idx + 1]

            # 添加回撤区域（使用两条线形成填充区域）
            fig.add_trace(
                go.Scatter(
                    x=dd_region["timestamp"],
                    y=dd_region["funding_curve"],
                    name=f'最大回撤区间 ({self.results["max_drawdown"]:.1%})',
                    line=dict(color="rgba(255,0,0,0.5)"),
                    showlegend=True,
                )
            )

            # 添加填充区域
            fig.add_trace(
                go.Scatter(
                    x=dd_region["timestamp"],
                    y=cummax[max_dd_start_idx : max_dd_end_idx + 1],
                    fill="tonexty",
                    mode="none",  # 不显示线条
                    fillcolor="rgba(255,0,0,0.2)",
                    showlegend=False,
                    hoverinfo="skip",
                )
            )

            # 添加最大回撤起点和终点的标记
            fig.add_trace(
                go.Scatter(
                    x=[df["timestamp"][max_dd_start_idx]],
                    y=[df["funding_curve"][max_dd_start_idx]],
                    mode="markers+text",
                    name="回撤起点",
                    marker=dict(color="green", size=10, symbol="triangle-up"),
                    text=[f'高点: {df["funding_curve"][max_dd_start_idx]:.2f}'],
                    textposition="top center",
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=[df["timestamp"][max_dd_end_idx]],
                    y=[df["funding_curve"][max_dd_end_idx]],
                    mode="markers+text",
                    name="回撤终点",
                    marker=dict(color="red", size=10, symbol="triangle-down"),
                    text=[f'低点: {df["funding_curve"][max_dd_end_idx]:.2f}'],
                    textposition="bottom center",
                )
            )

        # 更新布局
        fig.update_layout(
            title=dict(text="策略资金曲线", x=0.5, y=0.95),
            xaxis_title="时间",
            yaxis_title="净值",
            showlegend=True,
            hovermode="x unified",
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor="rgba(255,255,255,0.8)",
            ),
            # 添加网格线
            xaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor="rgba(128,128,128,0.2)",
                rangeslider=dict(visible=False),  # 可选：添加时间轴滑块
            ),
            yaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor="rgba(128,128,128,0.2)",
                tickformat=".3f",  # 显示三位小数
            ),
            plot_bgcolor="white",  # 设置白色背景
            hoverlabel=dict(
                bgcolor="white", font_size=12, font_family="Microsoft YaHei"
            ),
        )

        return fig

    def create_drawdown_figure(self) -> go.Figure:
        """创建回撤图"""
        df = self.funding_curve.to_pandas()
        cummax = df["funding_curve"].cummax()
        drawdown = (df["funding_curve"] - cummax) / cummax

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=df["timestamp"],
                y=drawdown,
                fill="tozeroy",
                name="回撤",
                line=dict(color="red"),
            )
        )

        fig.update_layout(
            title="策略回撤",
            xaxis_title="时间",
            yaxis_title="回撤",
            showlegend=True,
            hovermode="x unified",
        )

        return fig

    def create_monthly_returns_figure(self) -> go.Figure:
        """创建月度收益图"""
        df = self.funding_curve.to_pandas()
        df["returns"] = df["funding_curve"].pct_change()
        monthly_returns = df.groupby(df["timestamp"].dt.strftime("%Y-%m"))[
            "returns"
        ].sum()

        # 创建颜色列表
        colors = ["red" if x < 0 else "green" for x in monthly_returns.values]

        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                x=monthly_returns.index,
                y=monthly_returns.values,
                name="月度收益",
                marker_color=colors,
            )
        )

        fig.update_layout(
            title="月度收益分布",
            xaxis_title="月份",
            yaxis_title="收益率",
            showlegend=True,
            hovermode="x unified",
            yaxis=dict(
                tickformat=".1%",  # 显示为百分比
                hoverformat=".2%",  # 悬停时显示更精确的百分比
            ),
        )

        return fig

    def generate_html_report(self, output_path: str = "backtest_report.html") -> None:
        """生成HTML报告"""
        # 读取HTML模板
        with open(self.template_path, "r", encoding="utf-8") as f:
            template = Template(f.read())

        # 生成回测参数和数据信息HTML
        backtest_params = self._generate_backtest_params_html()
        data_info = self._generate_data_info_html()

        # 生成指标HTML
        metrics_mapping = {
            "annual_return": "年化收益率",
            "sharpe_ratio": "夏普比率",
            "max_drawdown": "最大回撤",
            "max_drawdown_duration": "最大回撤持续期",
            "calmar_ratio": "卡玛比率",
            "volatility": "年化波动率",
            "sortino_ratio": "索提诺比率",
            "win_rate": "胜率",
        }

        metrics_html = ""
        for key, name in metrics_mapping.items():
            if key in self.results:
                value = self.results[key]
                if key in ["annual_return", "max_drawdown", "volatility", "win_rate"]:
                    formatted_value = f"{value:.2%}"
                elif key == "max_drawdown_duration":
                    formatted_value = f"{value:.0f}天"
                else:
                    formatted_value = f"{value:.2f}"

                metrics_html += f"""
                <div class="metric-card">
                    <div class="metric-value">{formatted_value}</div>
                    <div class="metric-name">{name}</div>
                </div>
                """

        # 生成图表
        funding_curve_fig = self.create_funding_curve_figure()
        drawdown_fig = self.create_drawdown_figure()
        monthly_returns_fig = self.create_monthly_returns_figure()

        # 设置中文字体
        for fig in [funding_curve_fig, drawdown_fig, monthly_returns_fig]:
            fig.update_layout(font=dict(family="Microsoft YaHei"))

        # 生成HTML报告
        html_content = template.substitute(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            backtest_params=backtest_params,
            data_info=data_info,
            metrics_html=metrics_html,
            funding_curve_div=funding_curve_fig.to_html(
                full_html=False, include_plotlyjs=False, config={"locale": "zh-cn"}
            ),
            drawdown_div=drawdown_fig.to_html(
                full_html=False, include_plotlyjs=False, config={"locale": "zh-cn"}
            ),
            monthly_returns_div=monthly_returns_fig.to_html(
                full_html=False, include_plotlyjs=False, config={"locale": "zh-cn"}
            ),
        )

        # 保存HTML文件
        with open(output_path, "w", encoding="utf-8", errors="xmlcharrefreplace") as f:
            f.write(html_content)
