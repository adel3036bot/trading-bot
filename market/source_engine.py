# ==================================================
# ADEL SMART BOT V3 - SOURCE ENGINE
# PRODUCTION READY
# ==================================================

"""
==================================================
ADEL SMART BOT
Source Engine

Main Responsibilities:
- Shared Cache
- Smart Fallback
- Provider Management
- Symbol Normalization
- Data Validation
- Health Monitoring
- Source Statistics

Core Philosophy

NO DATA = NO SIGNAL

If the primary provider fails,
automatically switch to the next provider
without stopping the bot.

==================================================
"""

# ==================================================
# IMPORTS
# ==================================================

import time
import logging

from datetime import datetime

import pandas as pd

# ==================================================
# PROVIDER IMPORTS
# ==================================================

from market.sources.massive_provider import MassiveProvider
from market.sources.finnhub_provider import FinnhubProvider
from market.sources.fmp_provider import FMPProvider
from market.sources.alphavantage_provider import AlphaVantageProvider

# ==================================================
# CONFIG
# ==================================================

from config import (

    USE_MASSIVE,
    USE_FINNHUB,
    USE_FMP,
    USE_ALPHA_VANTAGE,

    ENABLE_SOURCE_FALLBACK,

    PRIMARY_DATA_SOURCE,
    SECONDARY_DATA_SOURCE,
    THIRD_DATA_SOURCE,
    FOURTH_DATA_SOURCE,

    MIN_HISTORY_ROWS

)

# ==================================================
# LOGGER
# ==================================================

logger = logging.getLogger("SourceEngine")

# ==================================================
# SHARED CACHE
# ==================================================

CACHE = {}

CACHE_TIMEOUT = 30

# ==================================================
# PROVIDER HEALTH
# ==================================================

PROVIDER_STATUS = {

    "MASSIVE": True,
    "FINNHUB": True,
    "FMP": True,
    "ALPHA_VANTAGE": True

}

# ==================================================
# PROVIDER STATISTICS
# ==================================================

PROVIDER_STATS = {

    "MASSIVE": {

        "requests": 0,

        "success": 0,

        "failed": 0,

        "response_time": 0.0

    },

    "FINNHUB": {

        "requests": 0,

        "success": 0,

        "failed": 0,

        "response_time": 0.0

    },

    "FMP": {

        "requests": 0,

        "success": 0,

        "failed": 0,

        "response_time": 0.0

    },

    "ALPHA_VANTAGE": {

        "requests": 0,

        "success": 0,

        "failed": 0,

        "response_time": 0.0

    }

}

# ==================================================
# PROVIDERS
# ==================================================

PROVIDERS = {}

if USE_MASSIVE:
    PROVIDERS["MASSIVE"] = MassiveProvider()

if USE_FINNHUB:
    PROVIDERS["FINNHUB"] = FinnhubProvider()

if USE_FMP:
    PROVIDERS["FMP"] = FMPProvider()

if USE_ALPHA_VANTAGE:
    PROVIDERS["ALPHA_VANTAGE"] = AlphaVantageProvider()

# ==================================================
# PROVIDER PRIORITY
# ==================================================

SOURCE_PRIORITY = [

    PRIMARY_DATA_SOURCE,
    SECONDARY_DATA_SOURCE,
    THIRD_DATA_SOURCE,
    FOURTH_DATA_SOURCE

]

# ==================================================
# AUTO SOURCE POLICY
# ==================================================

def active_provider_order():

    providers = []

    for provider_name in SOURCE_PRIORITY:

        provider = PROVIDERS.get(

            provider_name

        )

        if provider is None:

            continue

        if not provider.health_check():

            continue

        providers.append(

            provider_name

        )

    return providers

# ==================================================
# SYMBOL NORMALIZATION
# ==================================================

SYMBOL_MAP = {

    "SPX": "SPX",
    "SPY": "SPY",
    "QQQ": "QQQ",
    "NASDAQ": "NASDAQ",
    "VIX": "VIX",
    "GLD": "GLD",
    "XAUUSD": "XAUUSD",
    "BTC": "BTC-USD",
    "BTCUSD": "BTC-USD",
    "BTC-USD": "BTC-USD"

}

# ==================================================
# CACHE FUNCTIONS
# ==================================================

def _cache_key(symbol: str, timeframe: str) -> str:

    return f"{symbol.upper()}_{timeframe.upper()}"


def cache_exists(symbol: str, timeframe: str) -> bool:

    key = _cache_key(symbol, timeframe)

    if key not in CACHE:
        return False

    cache_time = CACHE[key]["timestamp"]

    if (time.time() - cache_time) > CACHE_TIMEOUT:

        del CACHE[key]

        return False

    return True


def get_cache(symbol: str, timeframe: str):

    key = _cache_key(symbol, timeframe)

    if not cache_exists(symbol, timeframe):
        return None

    return CACHE[key]["data"]


def save_cache(
    symbol: str,
    timeframe: str,
    source: str,
    data
):

    key = _cache_key(symbol, timeframe)

    CACHE[key] = {

        "symbol": symbol,

        "timeframe": timeframe,

        "source": source,

        "timestamp": time.time(),

        "datetime": datetime.now(),

        "data": data

    }


def clear_cache():

    CACHE.clear()


def cache_size():

    return len(CACHE)

    # ==================================================
# PROVIDER HEALTH FUNCTIONS
# ==================================================

def provider_enabled(provider_name: str) -> bool:

    return PROVIDER_STATUS.get(provider_name, False)


def provider_online(provider_name: str):

    if provider_name in PROVIDER_STATUS:

        PROVIDER_STATUS[provider_name] = True


def provider_offline(provider_name: str):

    if provider_name in PROVIDER_STATUS:

        PROVIDER_STATUS[provider_name] = False


def increase_success(provider_name: str):

    if provider_name not in PROVIDER_STATS:
        return

    PROVIDER_STATS[provider_name]["requests"] += 1
    PROVIDER_STATS[provider_name]["success"] += 1

    provider_online(provider_name)


def increase_failed(provider_name: str):

    if provider_name not in PROVIDER_STATS:
        return

    PROVIDER_STATS[provider_name]["requests"] += 1
    PROVIDER_STATS[provider_name]["failed"] += 1


def provider_success_rate(provider_name: str):

    if provider_name not in PROVIDER_STATS:
        return 0

    requests = PROVIDER_STATS[provider_name]["requests"]

    if requests == 0:
        return 100

    success = PROVIDER_STATS[provider_name]["success"]

    return round((success / requests) * 100, 2)


def provider_failed_rate(provider_name: str):

    if provider_name not in PROVIDER_STATS:
        return 0

    requests = PROVIDER_STATS[provider_name]["requests"]

    if requests == 0:
        return 0

    failed = PROVIDER_STATS[provider_name]["failed"]

    return round((failed / requests) * 100, 2)


def provider_statistics():

    return PROVIDER_STATS


def provider_health():

    return PROVIDER_STATUS

    # ==================================================
# DATA VALIDATION FUNCTIONS
# ==================================================

def normalize_dataframe(df):

    if df is None:
        return None

    if df.empty:
        return None

    column_map = {

        "o": "Open",
        "h": "High",
        "l": "Low",
        "c": "Close",
        "v": "Volume",
        "t": "Datetime",

        "open": "Open",
        "high": "High",
        "low": "Low",
        "close": "Close",
        "volume": "Volume",
        "date": "Datetime",
        "datetime": "Datetime",
        "timestamp": "Datetime"

    }

    df = df.rename(columns=column_map)

    return df


def required_columns():

    return [

        "Datetime",
        "Open",
        "High",
        "Low",
        "Close",
        "Volume"

    ]


def validate_columns(df):

    if df is None:
        return False

    for column in required_columns():

        if column not in df.columns:
            return False

    return True


def validate_history(df):

    if df is None:
        return False

    return len(df) >= MIN_HISTORY_ROWS


def clean_dataframe(df):

    if df is None:
        return None

    df = df.dropna()

    df = df.drop_duplicates()

    df = df.sort_values("Datetime")

    df = df.reset_index(drop=True)

    return df


def validate_prices(df):

    if df is None:
        return False

    if (df["Open"] <= 0).any():
        return False

    if (df["High"] <= 0).any():
        return False

    if (df["Low"] <= 0).any():
        return False

    if (df["Close"] <= 0).any():
        return False

    return True


def validate_volume(df):

    if df is None:
        return False

    if "Volume" not in df.columns:
        return False

    if df["Volume"].isnull().any():
        return False

    return True

# ==================================================
# PROVIDER FUNCTIONS
# ==================================================

def provider_exists(provider_name: str) -> bool:

    return provider_name in PROVIDERS


def get_provider(provider_name: str):

    if not provider_exists(provider_name):
        return None

    if not provider_enabled(provider_name):
        return None

    return PROVIDERS[provider_name]


def provider_order():

    order = []

    for provider in SOURCE_PRIORITY:

        if provider_exists(provider):

            order.append(provider)

    return order


def available_providers():

    return provider_order()


def first_provider():

    providers = provider_order()

    if len(providers) == 0:
        return None

    return providers[0]


def next_provider(current_provider: str):

    providers = provider_order()

    if current_provider not in providers:
        return None

    index = providers.index(current_provider)

    index += 1

    if index >= len(providers):
        return None

    return providers[index]


def reset_provider_status():

    for provider in PROVIDER_STATUS:

        PROVIDER_STATUS[provider] = True


def enabled_provider_count():

    count = 0

    for provider in PROVIDER_STATUS:

        if PROVIDER_STATUS[provider]:

            count += 1

    return count


def disable_provider(provider_name: str):

    provider_offline(provider_name)


def enable_provider(provider_name: str):

    provider_online(provider_name)
    
# ==================================================
# DATA REQUEST ENGINE
# ==================================================

def request_market_data(

    symbol: str,
    timeframe: str = "1D",
    candles: int = MIN_HISTORY_ROWS

):

    symbol = SYMBOL_MAP.get(

        symbol.upper(),

        symbol.upper()

    )

    if cache_exists(

        symbol,

        timeframe

    ):

        logger.info(

            f"[CACHE] {symbol} ({timeframe})"

        )

        return get_cache(

            symbol,

            timeframe

        )

    for provider_name in provider_order():

        provider = get_provider(

            provider_name

        )

        if provider is None:

            continue

        try:

            start_time = time.time()

            logger.info(

                f"[SOURCE] {provider_name} -> {symbol}"

            )

            data = provider.get_market_data(

                symbol=symbol,

                timeframe=timeframe,

                candles=candles

            )

            if data is None:

                increase_failed(

                    provider_name

                )

                continue

            data = normalize_dataframe(

                data

            )

            if data is None:

                increase_failed(

                    provider_name

                )

                continue

            data = clean_dataframe(

                data

            )

            if not validate_columns(

                data

            ):

                increase_failed(

                    provider_name

                )

                continue

            if not validate_history(

                data

            ):

                increase_failed(

                    provider_name

                )

                continue

            if not validate_prices(

                data

            ):

                increase_failed(

                    provider_name

                )

                continue

            if not validate_volume(

                data

            ):

                increase_failed(

                    provider_name

                )

                continue

            save_cache(

                symbol=symbol,

                timeframe=timeframe,

                source=provider_name,

                data=data

            )

            response_time = round(

                time.time() - start_time,

                3

            )

            PROVIDER_STATS[

                provider_name

            ][

                "response_time"

            ] = response_time

            increase_success(

                provider_name

            )

            logger.info(

                f"[SUCCESS] "

                f"{provider_name} "

                f"({response_time}s) "

                f"-> {symbol}"

            )

            return data

        except Exception as error:

            logger.error(

                f"[FAILED] {provider_name}: {error}"

            )

            increase_failed(

                provider_name

            )

            continue

    logger.warning(

        f"[NO DATA] {symbol}"

    )

    return None

    # ==================================================
# PUBLIC DATA FUNCTIONS
# ==================================================

def get_stock_data(

    symbol: str,
    timeframe: str = "1D",
    candles: int = MIN_HISTORY_ROWS

):

    return request_market_data(

        symbol=symbol,

        timeframe=timeframe,

        candles=candles

    )


def get_index_data(

    symbol: str,
    timeframe: str = "1D",
    candles: int = MIN_HISTORY_ROWS

):

    return request_market_data(

        symbol=symbol,

        timeframe=timeframe,

        candles=candles

    )


def get_etf_data(

    symbol: str,
    timeframe: str = "1D",
    candles: int = MIN_HISTORY_ROWS

):

    return request_market_data(

        symbol=symbol,

        timeframe=timeframe,

        candles=candles

    )


def get_vix_data(

    timeframe: str = "1D",
    candles: int = MIN_HISTORY_ROWS

):

    return request_market_data(

        symbol="VIX",

        timeframe=timeframe,

        candles=candles

    )


def get_gold_data(

    timeframe: str = "1D",
    candles: int = MIN_HISTORY_ROWS

):

    return request_market_data(

        symbol="GLD",

        timeframe=timeframe,

        candles=candles

    )


def get_crypto_data(

    symbol: str = "BTC-USD",
    timeframe: str = "1D",
    candles: int = MIN_HISTORY_ROWS

):

    return request_market_data(

        symbol=symbol,

        timeframe=timeframe,

        candles=candles

    )


def get_option_data(

    symbol: str,
    timeframe: str = "1D",
    candles: int = MIN_HISTORY_ROWS

):

    return request_market_data(

        symbol=symbol,

        timeframe=timeframe,

        candles=candles

    )

    # ==================================================
# SOURCE HEALTH CHECK
# ==================================================

def check_source_health():

    report = {}

    for provider_name in provider_order():

        provider = get_provider(provider_name)

        if provider is None:

            report[provider_name] = False

            continue

        try:

            status = provider.health_check()

            if status:

                provider_online(provider_name)

            else:

                provider_offline(provider_name)

            report[provider_name] = status

        except Exception as error:

            logger.error(

                f"[HEALTH] {provider_name}: {error}"

            )

            provider_offline(provider_name)

            report[provider_name] = False

    return report


def available_source_count():

    return sum(

        1

        for status in PROVIDER_STATUS.values()

        if status

    )


def all_sources_online():

    return available_source_count() == len(PROVIDER_STATUS)


def source_summary():

    return {

        "available": available_source_count(),

        "total": len(PROVIDER_STATUS),

        "status": PROVIDER_STATUS,

        "statistics": PROVIDER_STATS

    }

    # ==================================================
# TEST
# ==================================================

if __name__ == "__main__":

    print("=" * 50)
    print("ADEL SMART BOT - SOURCE ENGINE")
    print("=" * 50)

    print("\nProvider Order:")

    for provider in provider_order():

        print(f" • {provider}")

    print("\nChecking Sources...")

    health = check_source_health()

    for provider, status in health.items():

        icon = "🟢" if status else "🔴"

        print(f"{icon} {provider}")

    print("\nSource Summary")

    print(source_summary())

    print("\nSource Engine Ready.")

    