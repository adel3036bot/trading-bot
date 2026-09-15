# ==================================================
# ADEL SMART BOT V3
# FINNHUB PROVIDER
# PRODUCTION READY
# ==================================================

"""
==================================================
ADEL SMART BOT

FINNHUB PROVIDER

Responsibilities

- Connect to Finnhub API
- Download Market Data
- Download OHLCV Data
- Return Standard DataFrame

No Analysis
No Signals
No Indicators
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

    FINNHUB_API_KEY,

    MIN_HISTORY_ROWS

)


# ==================================================
# LOGGER
# ==================================================

logger = logging.getLogger(

    "FinnhubProvider"

)

# ==================================================
# CLASS
# ==================================================

class FinnhubProvider:

    """
    Finnhub Market Data Provider

    Responsibilities

    - Connect to Finnhub API
    - Download Market Data
    - Return Standard DataFrame

    No Analysis
    No Signals
    No Cache
    No Fallback
    """

    def __init__(self):

        self.api_key = FINNHUB_API_KEY

        self.base_url = "https://finnhub.io/api/v1"

        self.provider_name = "FINNHUB"

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

                f"{self.base_url}/quote",

                params={

                    "symbol": "AAPL",

                    "token": self.api_key

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

            if payload.get(

                "c",

                0

            ) == 0:

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

            "BTC": "BINANCE:BTCUSDT",

            "BTC-USD": "BINANCE:BTCUSDT",

            "ETH": "BINANCE:ETHUSDT",

            "ETH-USD": "BINANCE:ETHUSDT"

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

            resolution = self._convert_timeframe(

                timeframe

            )

            current_time = int(

                datetime.utcnow().timestamp()

            )

            seconds_map = {

                "1": 60,

                "5": 300,

                "15": 900,

                "30": 1800,

                "60": 3600,

                "120": 7200,

                "240": 14400,

                "D": 86400,

                "W": 604800,

                "M": 2592000

            }

            from_time = current_time - (

                candles *

                seconds_map.get(

                    resolution,

                    86400

                )

            )

            response = requests.get(

                f"{self.base_url}/stock/candle",

                params={

                    "symbol": symbol,

                    "resolution": resolution,

                    "from": from_time,

                    "to": current_time,

                    "token": self.api_key

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

            if payload.get(

                "s"

            ) != "ok":

                self.connected = False

                self.last_error = (

                    payload.get(

                        "s",

                        "Unknown Error"

                    )

                )

                logger.warning(

                    f"[{self.provider_name}] "

                    f"{self.last_error}"

                )

                return None

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

            "1M": "1",

            "5M": "5",

            "15M": "15",

            "30M": "30",

            "1H": "60",

            "2H": "120",

            "4H": "240",

            "1D": "D",

            "1W": "W",

            "1MO": "M"

        }

        return mapping.get(

            timeframe,

            "D"

        )

# ==================================================
# DATAFRAME FUNCTIONS
# ==================================================

    def _build_dataframe(

        self,

        payload

    ):

        dataframe = pd.DataFrame({

            "Datetime": payload["t"],

            "Open": payload["o"],

            "High": payload["h"],

            "Low": payload["l"],

            "Close": payload["c"],

            "Volume": payload["v"]

        })

        if dataframe.empty:

            return None

        dataframe["Datetime"] = pd.to_datetime(

            dataframe["Datetime"],

            unit="s"

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

            f"<FinnhubProvider "

            f"connected={self.connected}>"

        )

# ==================================================
# TEST
# ==================================================

if __name__ == "__main__":

    provider = FinnhubProvider()

    print(

        "\n=============================="

    )

    print(

        "ADEL SMART BOT"

    )

    print(

        "FINNHUB PROVIDER TEST"

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
    