# =====================================
# ADEL SMART BOT V1 CONFIGURATION
# =====================================

BOT_NAME = "ADEL SMART BOT"
VERSION = "1.0"

# =====================================
# MARKET INDEXES
# =====================================

MARKET_INDEXES = [
    "SPX",
    "NASDAQ",
    "SPY",
    "QQQ"
]

# =====================================
# FEAR & GREED
# =====================================

USE_FEAR_GREED = True

# =====================================
# VIX
# =====================================

USE_VIX = True

# =====================================
# GOLD LAYER
# =====================================

GOLD_SYMBOLS = [
    "XAUUSD",
    "GLD"
]

# =====================================
# BITCOIN LAYER
# =====================================

BITCOIN_SYMBOLS = [
    "BTC-USD"
]

# =====================================
# SCORING SYSTEM
# =====================================

MARKET_WEIGHT = 35
STRUCTURE_WEIGHT = 30
SMART_MONEY_WEIGHT = 20
MOMENTUM_WEIGHT = 10
PATTERN_WEIGHT = 5

# =====================================
# SIGNAL GRADES
# =====================================

GRADE_A_PLUS = 90
GRADE_A = 85
GRADE_B_PLUS = 80

MIN_SIGNAL_SCORE = 80

# =====================================
# TARGETS
# =====================================

TP1_PERCENT = 30
TP2_PERCENT = 60
TP3_PERCENT = 100

STOP_LOSS_PERCENT = 30

# =====================================
# MARKET SCAN
# =====================================

SCAN_INTERVAL_SECONDS = 60

# =====================================
# REPORTS
# =====================================

ENABLE_DAILY_REPORT = True
ENABLE_WEEKLY_REPORT = True
ENABLE_MONTHLY_REPORT = True

# =====================================
# HOT SIGNAL
# =====================================

HOT_SIGNAL_SCORE = 95

# =====================================
# ELITE SIGNAL
# =====================================

ELITE_SIGNAL_SCORE = 95

# =====================================
# WATCHLIST
# =====================================

WATCHLIST = {

    "INDICES": [
        "SPX",
        "NASDAQ"
    ],

    "ETFS": [
        "SPY",
        "QQQ"
    ],

    "STOCKS": [

        # TIER 1
        "NVDA",
        "AAPL",
        "MSFT",
        "META",
        "AMZN",
        "GOOGL",
        "AVGO",
        "TSLA",

        # TIER 2
        "NFLX",
        "AMD",
        "CRWD",
        "PLTR",
        "COST",
        "SHOP",
        "COIN",
        "BABA",

        # TIER 3
        "ARM",
        "PANW",
        "MU",
        "TSM",
        "AMAT",
        "MSTR",

        # EXPANDED TIER
        "ANET",
        "SNOW",
        "MDB",
        "DDOG",
        "NET",

        # SEMICONDUCTORS
        "QCOM",
        "ASML",

        # CYBER SECURITY
        "ZS",

        # CONSUMER
        "WMT",
        "HD",

        # FINANCIAL
        "JPM",
        "GS",
        "V",
        "MA",

        # HEALTHCARE
        "LLY",
        "UNH",
        "ABBV"

    ],

    "ENERGY": [
        "XOM",
        "CVX"
    ],

    "GOLD": [
        "GLD"
    ],

    "BITCOIN": [
        "BTC-USD"
    ]
}


# =====================================
# TELEGRAM
# =====================================

BOT_TOKEN = "8603423824:AAGS2MJhU6ilzTuNgGfin00scoRzAQ7aeoo"

CHAT_ID = -1003988538131

# =====================================
# ELITE SETTINGS
# =====================================

MOON_SHOT_PERCENT = 200

LEGENDARY_TRADE_PERCENT = 1000

MAX_RISK_PER_TRADE = 5

NO_REALTIME_DATA_NO_TRADE = True

# =====================================
# DATA SOURCES
# =====================================

PRIMARY_DATA_SOURCE = "POLYGON"

SECONDARY_DATA_SOURCE = "ALPACA"

THIRD_DATA_SOURCE = "TRADIER"

FOURTH_DATA_SOURCE = "IBKR"

# =====================================
# API KEYS
# =====================================

POLYGON_API_KEY = ""

ALPACA_API_KEY = ""

ALPACA_SECRET_KEY = ""

TRADIER_API_KEY = ""

IBKR_HOST = "127.0.0.1"

IBKR_PORT = 7497


