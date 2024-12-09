from typing import Dict, Optional, Callable, List
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path
import polars as pl
from pypostester.models import BacktestResult


class BacktestVisualizer:
    """回测结果可视化器"""

    def __init__(
        self,
        results: BacktestResult,
        params: Dict,
        template_path: Optional[Path] = None,
    ):
        """初始化可视化器

        Args:
            results: BacktestResult对象，包含回测结果
            params: 回测参数字典
            template_path: HTML模板路径，默认使用内置模板
        """
        self.results = results
        self.params = params
        self.funding_curve = results.funding_curve

        # 获取模板文件路径
        self._template_path = template_path or (
            Path(__file__).parent.parent / "templates" / "report_template.html"
        )

        # 初始化图形创建器字典
        self._figure_creators: Dict[str, Callable[[], go.Figure]] = {
            "funding_curve": self._create_funding_curve_figure,
            "drawdown": self._create_drawdown_figure,
            "monthly_returns": self._create_monthly_returns_figure,
        }

        # 初始化自定义图形列表
        self._custom_figures: List[Dict] = []

    def add_figure(
        self,
        name: str,
        figure_creator: Callable[[], go.Figure],
        position: str = "bottom",
    ) -> None:
        """添加自定义图形

        Args:
            name: 图形名称，用于在HTML中标识
            figure_creator: 创建图形的函数，需要返回plotly Figure对象
            position: 图形位置，可选 "top" 或 "bottom"，默认为 "bottom"
        """
        if position not in ["top", "bottom"]:
            raise ValueError("Position must be either 'top' or 'bottom'")

        self._custom_figures.append(
            {"name": name, "creator": figure_creator, "position": position}
        )

    def _create_base_figure(self, title: str) -> go.Figure:
        """创建基础图形对象

        Args:
            title: 图形标题

        Returns:
            go.Figure: 基础图形对象
        """
        fig = go.Figure()
        fig.update_layout(
            title=title,
            showlegend=True,
            hovermode="x unified",
            plot_bgcolor="white",
            hoverlabel=dict(
                bgcolor="white", font_size=12, font_family="Microsoft YaHei"
            ),
            xaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor="rgba(128,128,128,0.2)",
                rangeslider=dict(visible=False),
            ),
            yaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor="rgba(128,128,128,0.2)",
            ),
        )
        return fig

    def _add_max_drawdown_visualization(
        self, fig: go.Figure, df: pl.DataFrame, cummax: pl.Series, drawdown: pl.Series
    ) -> None:
        """添加最大回撤可视化

        Args:
            fig: 图形对象
            df: 数据框
            cummax: 累计最大值序列
            drawdown: 回撤序列
        """
        # 找到最大回撤的起止点
        max_dd_end_idx = drawdown.arg_min()
        max_dd_start_idx = (
            df.slice(0, max_dd_end_idx + 1).get_column("funding_curve").arg_max()
        )

        # 获取回撤区间数据
        dd_region = df.slice(max_dd_start_idx, max_dd_end_idx - max_dd_start_idx + 1)

        # 添加回撤区域
        fig.add_trace(
            go.Scatter(
                x=dd_region.get_column("time"),
                y=dd_region.get_column("funding_curve"),
                name=f'Max Drawdown Period ({self.results.indicator_values["max_drawdown"]:.1%})',
                line=dict(color="rgba(255,0,0,0.5)"),
                showlegend=True,
            )
        )

        # 添加填充区域
        fig.add_trace(
            go.Scatter(
                x=dd_region.get_column("time"),
                y=cummax.slice(max_dd_start_idx, max_dd_end_idx - max_dd_start_idx + 1),
                fill="tonexty",
                mode="none",
                fillcolor="rgba(255,0,0,0.2)",
                showlegend=False,
                hoverinfo="skip",
            )
        )

        # 添加最大回撤起点和终点的标记
        for idx, name, color, symbol, position in [
            (max_dd_start_idx, "Peak", "green", "triangle-up", "top"),
            (max_dd_end_idx, "Trough", "red", "triangle-down", "bottom"),
        ]:
            point_value = df.row(idx)[1]  # funding_curve value
            fig.add_trace(
                go.Scatter(
                    x=[df.row(idx)[0]],  # time value
                    y=[point_value],
                    mode="markers+text",
                    name=name,
                    marker=dict(color=color, size=10, symbol=symbol),
                    text=[f"{name}: {point_value:.2f}"],
                    textposition=f"{position} center",
                )
            )

    def _create_funding_curve_figure(self) -> go.Figure:
        """创建资金曲线图"""
        fig = self._create_base_figure("Strategy NAV")

        # 添加资金曲线
        fig.add_trace(
            go.Scatter(
                x=self.funding_curve.get_column("time"),
                y=self.funding_curve.get_column("funding_curve"),
                name="NAV",
                line=dict(color="#1f77b4"),
            )
        )

        # 添加最大回撤阴影
        if "max_drawdown" in self.results.indicator_values:
            cummax = self.funding_curve.get_column("funding_curve").cum_max()
            drawdown = (
                self.funding_curve.get_column("funding_curve") - cummax
            ) / cummax
            self._add_max_drawdown_visualization(
                fig, self.funding_curve, cummax, drawdown
            )

        # 更新y轴格式
        fig.update_layout(
            yaxis=dict(
                tickformat=".3f",
            ),
        )

        return fig

    def _create_drawdown_figure(self) -> go.Figure:
        """创建回撤图"""
        fig = self._create_base_figure("Strategy Drawdown")

        cummax = self.funding_curve.get_column("funding_curve").cum_max()
        drawdown = (self.funding_curve.get_column("funding_curve") - cummax) / cummax

        fig.add_trace(
            go.Scatter(
                x=self.funding_curve.get_column("time"),
                y=drawdown,
                fill="tozeroy",
                name="回撤",
                line=dict(color="red"),
            )
        )

        fig.update_layout(
            yaxis=dict(
                tickformat=".1%",
                hoverformat=".2%",
            ),
        )

        return fig

    def _create_monthly_returns_figure(self) -> go.Figure:
        """创建月度收益图"""
        fig = self._create_base_figure("Monthly Returns Distribution")

        # 计算收益率和月度收益
        monthly_returns = (
            self.funding_curve.with_columns(
                [
                    pl.col("funding_curve").pct_change().alias("returns"),
                    pl.col("time").dt.strftime("%Y-%m").alias("month"),
                ]
            )
            .group_by("month")
            .agg(pl.col("returns").sum())
            .sort("month")
        )

        fig.add_trace(
            go.Bar(
                x=monthly_returns.get_column("month"),
                y=monthly_returns.get_column("returns"),
                name="Monthly Returns",
                marker_color=[
                    "red" if x < 0 else "green"
                    for x in monthly_returns.get_column("returns")
                ],
            )
        )

        fig.update_layout(
            yaxis=dict(
                tickformat=".1%",
                hoverformat=".2%",
            ),
        )

        return fig

    def _generate_backtest_params_html(self) -> str:
        """生成回测参数HTML"""
        params = {
            "Commission Rate": f"{self.params['commission']:.3%}",
            "Annual Trading Days": f"{self.params['annual_trading_days']} days",
            "Indicators": (
                "All indicators"
                if self.params["indicators"] == "all"
                else ", ".join(self.params["indicators"])
            ),
        }

        return "\n".join(
            f'<div class="info-item"><span style="color: #666;">{k}:</span> {v}</div>'
            for k, v in params.items()
        )

    def _generate_data_info_html(self) -> str:
        """生成数据信息HTML"""
        df = self.funding_curve
        start_date = df.select(pl.col("time").min()).item().strftime("%Y-%m-%d")
        end_date = df.select(pl.col("time").max()).item().strftime("%Y-%m-%d")
        total_days = (
            df.select(pl.col("time").max()).item()
            - df.select(pl.col("time").min()).item()
        ).days

        # 计算数据频率
        time_diff = df.select(pl.col("time").diff().median()).item()
        minutes = time_diff.total_seconds() / 60

        if minutes < 60:  # 小于1小时
            frequency = f"{minutes:.0f}min"
        elif minutes < 1440:  # 小于1天
            frequency = f"{minutes/60:.1f}h"
        elif minutes < 10080:  # 小于1周
            frequency = f"{minutes/1440:.1f}d"
        elif minutes < 43200:  # 小于1月
            frequency = f"{minutes/10080:.1f}w"
        else:  # 大于等于1月
            frequency = f"{minutes/43200:.1f}m"

        info = {
            "Start Date": start_date,
            "End Date": end_date,
            "Total Days": f"{total_days} days",
            "Data Points": f"{len(df):,}",
            "Data Frequency": frequency,
        }

        return "\n".join(
            f'<div class="info-item"><span style="color: #666;">{k}:</span> {v}</div>'
            for k, v in info.items()
        )

    def _generate_metrics_html(self) -> str:
        """生成指标HTML"""
        metrics_html = ""

        # 从BacktestResult对象获取格式化后的指标值
        for key, value in self.results.formatted_indicator_values.items():
            # 将下划线分隔的键转换为标题形式的显示名称
            display_name = " ".join(word.capitalize() for word in key.split("_"))

            metrics_html += f"""
            <div class="metric-card">
                <div class="metric-value">{value}</div>
                <div class="metric-name">{display_name}</div>
            </div>
            """

        return metrics_html

    def _generate_all_figures(self) -> Dict[str, str]:
        """生成所有图形的HTML代码

        Returns:
            Dict[str, str]: 图形名称到HTML代码的映射
        """
        figures_html = {}

        # 添加顶部自定义图形
        for fig_info in self._custom_figures:
            if fig_info["position"] == "top":
                figures_html[fig_info["name"]] = fig_info["creator"]().to_html(
                    full_html=False, include_plotlyjs=False
                )

        # 添加内置图形
        for name, creator in self._figure_creators.items():
            figures_html[name] = creator().to_html(
                full_html=False, include_plotlyjs=False
            )

        # 添加底部自定义图形
        for fig_info in self._custom_figures:
            if fig_info["position"] == "bottom":
                figures_html[fig_info["name"]] = fig_info["creator"]().to_html(
                    full_html=False, include_plotlyjs=False
                )

        return figures_html

    def generate_html_report(self, output_path: str) -> None:
        """生成HTML回测报告

        Args:
            output_path: 输出文件路径
        """
        # 读取HTML模板
        with open(self._template_path, "r", encoding="utf-8") as f:
            html_template = f.read()

        # 生成所有图形的HTML代码
        figures_html = self._generate_all_figures()

        # 准备基础变量
        template_vars = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "backtest_params_html": self._generate_backtest_params_html(),
            "data_info_html": self._generate_data_info_html(),
            "metrics_html": self._generate_metrics_html(),
        }

        # 添加图形HTML代码
        template_vars.update(
            {f"{name}_div": html for name, html in figures_html.items()}
        )

        # 使用字符串格式化替换变量
        html_content = html_template
        for key, value in template_vars.items():
            placeholder = f"${key}"
            html_content = html_content.replace(placeholder, str(value))

        # 保存HTML文件
        with open(output_path, "w", encoding="utf-8", errors="xmlcharrefreplace") as f:
            f.write(html_content)
