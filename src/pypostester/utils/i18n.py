class I18N:
    """国际化配置"""

    TRANSLATIONS = {
        "zh_CN": {
            # 报告标题
            "backtest_report": "回测报告",
            "generation_time": "生成时间",
            # 回测参数
            "backtest_params": "回测参数",
            "commission_rate": "手续费率",
            "annual_trading_days": "年化交易日",
            "indicators": "计算指标",
            "all_indicators": "全部",
            # 数据信息
            "data_info": "数据信息",
            "start_date": "回测起始日期",
            "end_date": "回测结束日期",
            "total_days": "回测天数",
            "data_points": "数据点数",
            "days_suffix": "天",
            "points_suffix": "个",
            # 指标名称
            "annual_return": "年化收益率",
            "sharpe_ratio": "夏普比率",
            "max_drawdown": "最大回撤",
            "max_drawdown_duration": "最大回撤持续期",
            "calmar_ratio": "卡玛比率",
            "volatility": "年化波动率",
            "sortino_ratio": "索提诺比率",
            "win_rate": "胜率",
            # 图表标题
            "funding_curve": "策略资金曲线",
            "drawdown_curve": "策略回撤",
            "monthly_returns": "月度收益分布",
            # 图表标签
            "time": "时间",
            "nav": "净值",
            "drawdown": "回撤",
            "returns": "收益率",
            "month": "月份",
            "high_point": "高点",
            "low_point": "低点",
            "drawdown_region": "最大回撤区间",
        },
        "en_US": {
            # Report Title
            "backtest_report": "Backtest Report",
            "generation_time": "Generation Time",
            # Backtest Parameters
            "backtest_params": "Backtest Parameters",
            "commission_rate": "Commission Rate",
            "annual_trading_days": "Annual Trading Days",
            "indicators": "Indicators",
            "all_indicators": "All",
            # Data Information
            "data_info": "Data Information",
            "start_date": "Start Date",
            "end_date": "End Date",
            "total_days": "Total Days",
            "data_points": "Data Points",
            "days_suffix": "days",
            "points_suffix": "",
            # Metrics
            "annual_return": "Annual Return",
            "sharpe_ratio": "Sharpe Ratio",
            "max_drawdown": "Maximum Drawdown",
            "max_drawdown_duration": "Max Drawdown Duration",
            "calmar_ratio": "Calmar Ratio",
            "volatility": "Annual Volatility",
            "sortino_ratio": "Sortino Ratio",
            "win_rate": "Win Rate",
            # Chart Titles
            "funding_curve": "Strategy NAV",
            "drawdown_curve": "Strategy Drawdown",
            "monthly_returns": "Monthly Returns Distribution",
            # Chart Labels
            "time": "Time",
            "nav": "NAV",
            "drawdown": "Drawdown",
            "returns": "Returns",
            "month": "Month",
            "high_point": "High",
            "low_point": "Low",
            "drawdown_region": "Maximum Drawdown Region",
        },
    }

    def __init__(self, lang="zh_CN"):
        """
        初始化语言设置

        Args:
            lang: 语言代码，支持 'zh_CN' 和 'en_US'
        """
        if lang not in self.TRANSLATIONS:
            raise ValueError(f"Unsupported language: {lang}")
        self.lang = lang

    def get(self, key: str) -> str:
        """获取翻译文本"""
        return self.TRANSLATIONS[self.lang].get(key, key)
