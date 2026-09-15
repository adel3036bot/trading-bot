# ==================================================
# ADEL SMART BOT V3
# FMP PROVIDER
# PRODUCTION READY
# ==================================================

"""
==================================================
ADEL SMART BOT

FMP PROVIDER

Responsibilities

- Connect to FMP API
- Download Market Data
- Download OHLCV Data
- Return Standard DataFrame

No Analysis
No Signals
No Cache
No Fallback

Only Data

==================================================
"""

# ==================================================
# IMPORTS
# ==================================================

import logging

from datetime import datetime

import pandas as pd

import requests


# ==================================================
# CONFIG
# ==================================================

from config import (

    FMP_API_KEY,

    MIN_HISTORY_ROWS

)


# ==================================================
# LOGGER
# ==================================================

logger = logging.getLogger(

    "FMPProvider"

)

# ==================================================
# CLASS
# ==================================================

class FMPProvider:

    """
    FMP Market Data Provider

    Responsibilities

    - Connect to FMP API
    - Download Market Data
    - Return Standard DataFrame

    No Analysis
    No Signals
    No Cache
    No Fallback
    """

    def __init__(self):

        self.api_key = FMP_API_KEY

        self.base_url = "https://financialmodelingprep.com/api"

        self.provider_name = "FMP"

        self.name = self.provider_name

        self.timeout = 20

        self.connected = False

        self.last_error = None

        self.supports_realtime = True

        self.supports_history = True

        self.supports_indices = True

        self.supports_etf = True

        self.supports_crypto = True

        self.supports_options = False

# ==================================================
# CONNECTION FUNCTIONS
# ==================================================

    def health_check(self):

        try:

            response = requests.get(

                f"{self.base_url}/v3/quote/AAPL",

                params={

                    "apikey": self.api_key

                },

                timeout=self.timeout

            )

            if response.status_code != 200:

                self.connected = False

                self.last_error = (

                    f"HTTP {response.status_code}"

                )

                return False

            payload = response.json()

            if not payload:

                self.connected = False

                self.last_error = (

                    "No Market Data"

                )

                return False

            self.connected = True

            self.last_error = None

            return True

        except Exception as error:

            self.connected = False

            self.last_error = str(error)

            logger.exception(

                f"[{self.provider_name}] {error}"

            )

            return False


# ==================================================
# SYMBOL FUNCTIONS
# ==================================================

    def normalize_symbol(

        self,

        symbol: str

    ):

        symbol = symbol.upper()

        symbol_map = {

            "SPX": "^GSPC",

            "SPY": "SPY",

            "QQQ": "QQQ",

            "NASDAQ": "^IXIC",

            "VIX": "^VIX",

            "GLD": "GLD",

            "GOLD": "GLD",

            "BTC": "BTCUSD",

            "BTC-USD": "BTCUSD",

            "ETH": "ETHUSD",

            "ETH-USD": "ETHUSD"

        }

        return symbol_map.get(

            symbol,

            symbol

        )

# ==================================================
# MARKET DATA FUNCTIONS
# ==================================================

    def get_market_data(

        self,
        symbol: str,
        timeframe: str = "1D",
        candles: int = MIN_HISTORY_ROWS

    ):

        symbol = self.normalize_symbol(symbol)

        try:

            interval = self._convert_timeframe(

                timeframe

            )

            url = (

                f"{self.base_url}/v3/historical-chart/"
                f"{interval}/{symbol}"

            )

            response = requests.get(

                url,

                params={

                    "apikey": self.api_key

                },

                timeout=self.timeout

            )

            if response.status_code != 200:

                self.connected = False

                self.last_error = (

                    f"HTTP {response.status_code}"

                )

                logger.error(

                    f"[{self.provider_name}] "

                    f"{self.last_error}"

                )

                return None

            payload = response.json()

            if not payload:

                self.connected = False

                self.last_error = (

                    "No Market Data"

                )

                logger.warning(

                    f"[{self.provider_name}] "

                    f"{self.last_error}"

                )

                return None

            payload = payload[:candles]

            dataframe = self._build_dataframe(

                payload

            )

            if dataframe is None:

                self.connected = False

                return None

            self.connected = True

            self.last_error = None

            return dataframe

        except Exception as error:

            self.connected = False

            self.last_error = str(error)

            logger.exception(

                f"[{self.provider_name}] {error}"

            )

            return None

# ==================================================
# TIMEFRAME FUNCTIONS
# ==================================================

    def _convert_timeframe(

        self,

        timeframe: str

    ):

        timeframe = timeframe.upper()

        mapping = {

            "1M": "1min",

            "5M": "5min",

            "15M": "15min",

            "30M": "30min",

            "1H": "1hour",

            "2H": "2hour",

            "4H": "4hour",

            "1D": "1day",

            "1W": "1week",

            "1MO": "1month"

        }

        return mapping.get(

            timeframe,

            "1day"

        )


# ==================================================
# DATAFRAME FUNCTIONS
# ==================================================

    def _build_dataframe(

        self,

        payload

    ):

        dataframe = pd.DataFrame(

            payload

        )

        if dataframe.empty:

            return None

        dataframe = dataframe.rename(

            columns={

                "date": "Datetime",

                "open": "Open",

                "high": "High",

                "low": "Low",

                "close": "Close",

                "volume": "Volume"

            }

        )

        dataframe["Datetime"] = pd.to_datetime(

            dataframe["Datetime"]

        )

        dataframe = dataframe.sort_values(

            "Datetime"

        )

        dataframe = dataframe.reset_index(

            drop=True

        )

        return dataframe

# ==================================================
# OPTION FUNCTIONS
# ==================================================

    def get_option_chain_data(

        self,

        symbol: str

    ):

        logger.warning(

            f"[{self.provider_name}] "

            "Option Chain Not Supported."

        )

        return None


# ==================================================
# INDEX FUNCTIONS
# ==================================================

    def get_vix_data(

        self,

        timeframe: str = "1D",

        candles: int = MIN_HISTORY_ROWS

    ):

        return self.get_market_data(

            symbol="VIX",

            timeframe=timeframe,

            candles=candles

        )


    def get_gold_data(

        self,

        timeframe: str = "1D",

        candles: int = MIN_HISTORY_ROWS

    ):

        return self.get_market_data(

            symbol="GLD",

            timeframe=timeframe,

            candles=candles

        )


    def get_crypto_data(

        self,

        symbol: str = "BTC",

        timeframe: str = "1D",

        candles: int = MIN_HISTORY_ROWS

    ):

        return self.get_market_data(

            symbol=symbol,

            timeframe=timeframe,

            candles=candles

        )


    def get_index_data(

        self,

        symbol: str,

        timeframe: str = "1D",

        candles: int = MIN_HISTORY_ROWS

    ):

        return self.get_market_data(

            symbol=symbol,

            timeframe=timeframe,

            candles=candles

        )


# ==================================================
# PROVIDER FUNCTIONS
# ==================================================

    def is_connected(

        self

    ):

        return self.connected


    def get_last_error(

        self

    ):

        return self.last_error


    def provider_info(

        self

    ):

        return {

            "provider": self.provider_name,

            "base_url": self.base_url,

            "connected": self.connected,

            "supports_realtime": self.supports_realtime,

            "supports_history": self.supports_history,

            "supports_indices": self.supports_indices,

            "supports_etf": self.supports_etf,

            "supports_crypto": self.supports_crypto,

            "supports_options": self.supports_options

        }


# ==================================================
# UTILITY FUNCTIONS
# ==================================================

    def reset_status(

        self

    ):

        self.connected = False

        self.last_error = None


    def close(

        self

    ):

        self.reset_status()


    def __repr__(

        self

    ):

        return (

            f"<FMPProvider "

            f"connected={self.connected}>"

        )


# ==================================================
# TEST
# ==================================================

if __name__ == "__main__":

    provider = FMPProvider()

    print(

        "\n=============================="

    )

    print(

        "ADEL SMART BOT"

    )

    print(

        "FMP PROVIDER TEST"

    )

    print(

        "=============================="

    )

    print(

        "Connection:",

        provider.health_check()

    )

    print(

        "Provider Info:",

        provider.provider_info()

    )

    dataframe = provider.get_market_data(

        symbol="AAPL",

        timeframe="1D",

        candles=10

    )

    if dataframe is not None:

        print(

            "\nLatest Data"

        )

        print(

            dataframe.tail()

        )

    else:

        print(

            "\nNo Data Received."

        )

    provider.close()

    print(

        "\nTest Finished."

    )

    