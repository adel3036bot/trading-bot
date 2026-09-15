# ==================================================
# ADEL SMART BOT V3
# MASSIVE PROVIDER
# PRODUCTION READY
# ==================================================

"""
==================================================

ADEL SMART BOT

Massive Provider

Responsibilities

- Connect to Massive API
- Download Market Data
- Download OHLCV
- Return Standard DataFrame
- Handle Symbol Conversion
- Handle Timeframe Conversion
- No Analysis
- No Indicators
- No Signals

Only Data

==================================================
"""

# ==================================================
# IMPORTS
# ==================================================

import logging
import requests
import pandas as pd

from datetime import datetime

# ==================================================
# CONFIG
# ==================================================

from config import (

    MASSIVE_API_KEY,

    MIN_HISTORY_ROWS

)

# ==================================================
# LOGGER
# ==================================================

logger = logging.getLogger("MassiveProvider")

# ==================================================
# CLASS
# ==================================================

class MassiveProvider:
    """
    Massive (Polygon) Market Data Provider

    Responsibilities
    ----------------
    - Download OHLCV market data
    - Normalize symbols
    - Convert timeframe
    - Return standardized DataFrame
    - No analysis
    - No indicators
    - No signals
    """

    def __init__(self):

        # Provider Information
        self.provider_name = "MASSIVE"
        self.name = self.provider_name

        # Authentication
        self.api_key = MASSIVE_API_KEY

        # API Configuration
        self.base_url = "https://api.polygon.io"
        self.timeout = 20

        # Runtime Status
        self.connected = False
        self.last_error = None

        # Provider Features
        self.supports_realtime = True
        self.supports_history = True
        self.supports_indices = True
        self.supports_etf = True
        self.supports_crypto = True
        self.supports_options = True

        logger.info(
            f"{self.provider_name} Provider Initialized"
        )

        # ==================================================
# CONNECTION FUNCTIONS
# ==================================================

    def health_check(self) -> bool:
        """
        Check Massive API availability.
        Does not download market data.
        """

        self.connected = False
        self.last_error = None

        try:

            response = requests.get(

                f"{self.base_url}/v3/reference/tickers",

                params={

                    "limit": 1,
                    "apiKey": self.api_key

                },

                timeout=self.timeout

            )

            if response.status_code == 200:

                self.connected = True

                return True

            self.last_error = (

                f"HTTP {response.status_code}"

            )

            return False

        except Exception as error:

            self.last_error = str(error)

            logger.error(

                f"[{self.provider_name}] {error}"

            )

            return False


    def is_connected(self) -> bool:

        return self.connected


    def last_exception(self):

        return self.last_error

       # ==================================================
# SYMBOL FUNCTIONS
# ==================================================

    SYMBOL_MAP = {

        # =========================
        # US INDEXES
        # =========================

        "SPX": "I:SPX",
        "^GSPC": "I:SPX",

        "NASDAQ": "I:COMP",
        "^IXIC": "I:COMP",

        "VIX": "I:VIX",
        "^VIX": "I:VIX",

        # =========================
        # ETFs
        # =========================

        "SPY": "SPY",
        "QQQ": "QQQ",
        "GLD": "GLD",

        # =========================
        # CRYPTO
        # =========================

        "BTC": "X:BTCUSD",
        "BTCUSD": "X:BTCUSD",
        "BTC-USD": "X:BTCUSD",

        "ETH": "X:ETHUSD",
        "ETHUSD": "X:ETHUSD",
        "ETH-USD": "X:ETHUSD"

    }


    def normalize_symbol(

        self,

        symbol: str

    ) -> str:

        if symbol is None:

            return ""

        symbol = symbol.strip().upper()

        return self.SYMBOL_MAP.get(

            symbol,

            symbol

        )

         # ==================================================
# TIMEFRAME FUNCTIONS
# ==================================================

    TIMEFRAME_MAP = {

        # Minutes
        "1M": (1, "minute"),
        "5M": (5, "minute"),
        "15M": (15, "minute"),
        "30M": (30, "minute"),

        # Hours
        "1H": (1, "hour"),
        "2H": (2, "hour"),
        "4H": (4, "hour"),

        # Daily / Weekly / Monthly
        "1D": (1, "day"),
        "1W": (1, "week"),
        "1MO": (1, "month")

    }


    def _convert_timeframe(

        self,

        timeframe: str

    ):

        if timeframe is None:

            timeframe = "1D"

        timeframe = timeframe.strip().upper()

        if timeframe not in self.TIMEFRAME_MAP:

            logger.warning(

                f"[{self.provider_name}] "
                f"Unsupported timeframe: {timeframe}"

            )

            timeframe = "1D"

        return self.TIMEFRAME_MAP[timeframe]
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

            multiplier, timespan = self._convert_timeframe(

                timeframe

            )

            end_date = datetime.utcnow().strftime(

                "%Y-%m-%d"

            )

            start_date = "2023-01-01"

            endpoint = (

                f"/v2/aggs/ticker/"
                f"{symbol}/range/"
                f"{multiplier}/{timespan}/"
                f"{start_date}/{end_date}"

            )

            response = requests.get(

                f"{self.base_url}{endpoint}",

                params={

                    "adjusted": "true",

                    "sort": "asc",

                    "limit": candles,

                    "apiKey": self.api_key

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

            results = payload.get(

                "results",

                []

            )

            if not results:

                self.connected = False

                logger.warning(

                    f"[{self.provider_name}] "

                    "No Results"

                )

                return None

            dataframe = self._build_dataframe(

                results

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
# DATAFRAME FUNCTIONS
# ==================================================

    def _build_dataframe(

        self,

        payload

    ):

        dataframe = pd.DataFrame(payload)

        if dataframe.empty:

            return None

        dataframe = dataframe.rename(

            columns={

                "t": "Datetime",
                "o": "Open",
                "h": "High",
                "l": "Low",
                "c": "Close",
                "v": "Volume"

            }

        )

        required_columns = [

            "Datetime",
            "Open",
            "High",
            "Low",
            "Close"

        ]

        for column in required_columns:

            if column not in dataframe.columns:

                logger.error(

                    f"[{self.provider_name}] Missing column: {column}"

                )

                return None

        if "Volume" not in dataframe.columns:

            dataframe["Volume"] = 0

        dataframe["Datetime"] = pd.to_datetime(

            dataframe["Datetime"],

            unit="ms"

        )

        dataframe = dataframe[

            [

                "Datetime",
                "Open",
                "High",
                "Low",
                "Close",
                "Volume"

            ]

        ]

        dataframe = dataframe.sort_values(

            "Datetime"

        )

        dataframe = dataframe.reset_index(

            drop=True

        )

        return dataframe

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

        symbol: str = "BTC-USD",
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
# UTILITY FUNCTIONS
# ==================================================

    def provider_info(self):

        return {

            "name": self.provider_name,

            "connected": self.connected,

            "supports_realtime": self.supports_realtime,

            "supports_history": self.supports_history,

            "supports_indices": self.supports_indices,

            "supports_etf": self.supports_etf,

            "supports_crypto": self.supports_crypto,

            "supports_options": self.supports_options

        }


    def reset_status(self):

        self.connected = False

        self.last_error = None


    def close(self):

        self.reset_status()

        logger.info(

            f"{self.provider_name} Provider Closed"

        )


    def __repr__(self):

        return (

            f"<MassiveProvider "

            f"connected={self.connected}>"

        )

         # ==================================================
# TEST
# ==================================================

if __name__ == "__main__":

    provider = MassiveProvider()

    print("=" * 50)

    print("ADEL SMART BOT")

    print("Massive Provider Test")

    print("=" * 50)

    print(

        "Health Check:",

        provider.health_check()

    )

    data = provider.get_market_data(

        symbol="SPY",

        timeframe="1D",

        candles=5

    )

    if data is None:

        print(

            "No Data Returned"

        )

    else:

        print(

            data.tail()

        )

    provider.close()

