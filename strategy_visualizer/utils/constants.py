# 常量定义

# 支持的时间框架
TIMEFRAMES = ["1m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w"]

# 默认策略参数
DEFAULT_STRATEGY_PARAMS = {
    "minimal_roi": {"0": 0.1},
    "stoploss": -0.1,
    "timeframe": "5m",
    "startup_candle_count": 30
}

# 节点颜色配置
NODE_COLORS = {
    "strategy_implemented": "#4CAF50",  # 绿色
    "strategy_not_implemented": "#FFC107",  # 黄色
    "core_process": "#2196F3",  # 蓝色
    "data_flow": "#9C27B0",  # 紫色
    "risk_management": "#F44336",  # 红色
}

# 支持的交易对
DEFAULT_PAIRS = [
    "BTC/USDT", "ETH/USDT", "BNB/USDT", "ADA/USDT", "DOT/USDT",
    "LINK/USDT", "LTC/USDT", "BCH/USDT", "XRP/USDT", "EOS/USDT"
]

# 文件上传限制
MAX_FILE_SIZE_MB = 10
ALLOWED_FILE_TYPES = ["json"]