"""Constants used throughout the package"""

from pathlib import Path

# Paths
PACKAGE_ROOT = Path(__file__).parent.parent
TEMPLATE_PATH = PACKAGE_ROOT / "templates" / "report_template.html"

# Required columns for input data
REQUIRED_COLUMNS = {"close": ["time", "close"], "position": ["time", "position"]}

# Time constants
SECONDS_PER_DAY = 24 * 3600
SECONDS_PER_HOUR = 3600
SECONDS_PER_MINUTE = 60

# Default values
DEFAULT_COMMISSION = 0.0
DEFAULT_ANNUAL_TRADING_DAYS = 252
DEFAULT_LEVERAGE = 1.0
