# ==================================================
# ADEL SMART BOT V3
# ALPHA VANTAGE PROVIDER
# PRODUCTION READY
# ==================================================

"""
==================================================
ADEL SMART BOT

Alpha Vantage Provider

Responsibilities

- Connect to Alpha Vantage API
- Download Market Data
- Download OHLCV
- Return Standard DataFrame
- No Analysis
- No Signals
- No Indicators

Only Data

==================================================
"""

# ==================================================
# IMPORTS
# ==================================================

import requests
import pandas as pd

from datetime import datetime

import logging

# ==================================================
# CONFIG
# ==================================================

from config import (

    ALPHA_VANTAGE_API_KEY,

    MIN_HISTORY_ROWS

)

# ==================================================
# LOGGER
# ==================================================

logger = logging.getLogger("AlphaVantageProvider")

# ==================================================
# CLASS
# ==================================================

class AlphaVantageProvider:

    """
    Alpha Vantage Market Data Provider

    This provider downloads only
    market data.

    No analysis.

    No indicators.

    No scoring.

    No signals.
    """

    def __init__(self):

        self.api_key = ALPHA_VANTAGE_API_KEY

        self.base_url = "https://www.alphavantage.co/query"

        self.timeout = 20

        self.name = "ALPHA_VANTAGE"

        self.connected = False

        self.last_error = None

        # ==================================================
# CONNECTION FUNCTIONS
# ==================================================

    def health_check(self):

        try:

            response = requests.get(

                self.base_url,

                params={

                    "function": "GLOBAL_QUOTE",

                    "symbol": "AAPL",

                    "apikey": self.api_key

                },

                timeout=self.timeout

            )

            self.connected = response.status_code == 200

            return self.connected

        except Exception as error:

            self.connected = False

            self.last_error = str(error)

            logger.error(

                f"[{self.name}] {error}"

            )

            return False


    def is_connected(self):

        return self.connected


    def last_exception(self):

        return self.last_error


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

            "NASDAQ": "^IXIC",

            "VIX": "^VIX",

            "SPY": "SPY",

            "QQQ": "QQQ",

            "GLD": "GLD",

            "BTC-USD": "BTCUSD"

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

            function = self._convert_timeframe(timeframe)

            response = requests.get(

                self.base_url,

                params={

                    "function": function,

                    "symbol": symbol,

                    "outputsize": "full",

                    "apikey": self.api_key

                },

                timeout=self.timeout

            )

            if response.status_code != 200:

                logger.error(

                    f"[{self.name}] HTTP {response.status_code}"

                )

                return None

            payload = response.json()

            dataframe = self._build_dataframe(

                payload,

                candles

            )

            return dataframe

        except Exception as error:

            self.last_error = str(error)

            logger.exception(

                f"[{self.name}] {error}"

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

            "1M": "TIME_SERIES_INTRADAY",
            "5M": "TIME_SERIES_INTRADAY",
            "15M": "TIME_SERIES_INTRADAY",
            "30M": "TIME_SERIES_INTRADAY",

            "1H": "TIME_SERIES_INTRADAY",
            "2H": "TIME_SERIES_INTRADAY",
            "4H": "TIME_SERIES_INTRADAY",

            "1D": "TIME_SERIES_DAILY",
            "1W": "TIME_SERIES_WEEKLY",
            "1MO": "TIME_SERIES_MONTHLY"

        }

        return mapping.get(

            timeframe,

            "TIME_SERIES_DAILY"

        )


# ==================================================
# DATAFRAME FUNCTIONS
# ==================================================

    def _build_dataframe(

        self,

        payload,

        candles

    ):

        history = None

        for key, value in payload.items():

            if "Time Series" in key:

                history = value

                break

        if history is None:

            return None

        dataframe = pd.DataFrame.from_dict(

            history,

            orient="index"

        )

        dataframe = dataframe.rename(

            columns={

                "1. open": "Open",
                "2. high": "High",
                "3. low": "Low",
                "4. close": "Close",
                "5. volume": "Volume"

            }

        )

        dataframe.index.name = "Datetime"

        dataframe = dataframe.reset_index()

        dataframe["Datetime"] = pd.to_datetime(

            dataframe["Datetime"]

        )

        dataframe = dataframe.sort_values(

            "Datetime"

        )

        dataframe = dataframe.tail(

            candles

        )

        dataframe = dataframe.reset_index(

            drop=True

        )

        return dataframe

        # ==================================================
# OPTION DATA FUNCTIONS
# ==================================================

    def get_option_chain_data(

        self,

        symbol: str

    ):

        logger.warning(

            f"[{self.name}] Option Chain Not Implemented"

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


    def get_spx_data(

        self,

        timeframe: str = "1D",

        candles: int = MIN_HISTORY_ROWS

    ):

        return self.get_market_data(

            symbol="SPX",

            timeframe=timeframe,

            candles=candles

        )


    def get_spy_data(

        self,

        timeframe: str = "1D",

        candles: int = MIN_HISTORY_ROWS

    ):

        return self.get_market_data(

            symbol="SPY",

            timeframe=timeframe,

            candles=candles

        )


    def get_qqq_data(

        self,

        timeframe: str = "1D",

        candles: int = MIN_HISTORY_ROWS

    ):

        return self.get_market_data(

            symbol="QQQ",

            timeframe=timeframe,

            candles=candles

        )


    def get_nasdaq_data(

        self,

        timeframe: str = "1D",

        candles: int = MIN_HISTORY_ROWS

    ):

        return self.get_market_data(

            symbol="NASDAQ",

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

        symbol: str = "BTC-USD",

        timeframe: str = "1D",

        candles: int = MIN_HISTORY_ROWS

    ):

        return self.get_market_data(

            symbol=symbol,

            timeframe=timeframe,

            candles=candles

        )


# ==================================================
# UTILITY FUNCTIONS
# ==================================================

    def get_provider_name(self):

        return self.name


    def provider_information(self):

        return {

            "name": self.name,

            "connected": self.connected,

            "base_url": self.base_url,

            "timeout": self.timeout,

            "last_error": self.last_error

        }


    def reset_connection(self):

        self.connected = False

        self.last_error = None


    def ping(self):

        return self.health_check()


# ==================================================
# TEST
# ==================================================

if __name__ == "__main__":

    provider = AlphaVantageProvider()

    print("=" * 60)
    print("ADEL SMART BOT - ALPHA VANTAGE PROVIDER")
    print("=" * 60)

    print("\nChecking Connection...")

    if provider.health_check():

        print("🟢 Connected")

    else:

        print("🔴 Connection Failed")

    print("\nProvider Information")

    print(provider.provider_information())

    