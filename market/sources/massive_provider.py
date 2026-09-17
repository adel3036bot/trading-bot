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

from datetime import datetime, timezone

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

    # ==================================================
    # OPTION CHAIN SNAPSHOT
    # ==================================================

    @staticmethod
    def _option_timestamp(value):
        """Convert provider epoch timestamps to UTC ISO strings without guessing."""
        if value is None:
            return None
        try:
            timestamp = int(value)
            if timestamp > 10**17:
                timestamp /= 10**9
            elif timestamp > 10**14:
                timestamp /= 10**6
            elif timestamp > 10**11:
                timestamp /= 10**3
            return datetime.fromtimestamp(timestamp, timezone.utc).isoformat()
        except (TypeError, ValueError, OSError, OverflowError):
            return None

    @staticmethod
    def _option_timestamp_is_fresh(value, max_age_seconds):
        """Accept only provider timestamps inside the requested freshness window."""
        if value is None:
            return False

        try:
            timestamp = int(value)
            if timestamp > 10**17: timestamp /= 10**9
            elif timestamp > 10**14: timestamp /= 10**6
            elif timestamp > 10**11: timestamp /= 10**3
            age = datetime.now(timezone.utc).timestamp() - timestamp
            return 0 <= age <= max_age_seconds
        except (TypeError, ValueError, OSError, OverflowError):
            return False

    def iter_reference_tickers(self, *, max_pages=None, limit=1000):
        """Provider-only pagination; UniverseEngine never calls this directly."""
        url = f"{self.base_url}/v3/reference/tickers"
        pages = 0
        while url and (max_pages is None or pages < max_pages):
            response = requests.get(url, params={"market":"stocks","active":"true","limit":limit,"apiKey":self.api_key}, timeout=self.timeout)
            if response.status_code != 200:
                self.last_error = f"HTTP {response.status_code}"; return
            payload = response.json()
            for item in payload.get("results", []): yield item
            url = payload.get("next_url")
            if url and "apiKey=" not in url: url = f"{url}{'&' if '?' in url else '?'}apiKey={self.api_key}"
            pages += 1

    def _normalize_option_contract(self, raw, underlying, require_realtime, max_age_seconds):
        """Normalize a real contract only; underlying OHLCV is never accepted."""
        details = raw.get("details") or {}
        quote = raw.get("last_quote") or {}
        trade = raw.get("last_trade") or {}
        day = raw.get("day") or {}
        quote_timeframe = quote.get("timeframe")
        trade_timeframe = trade.get("timeframe")
        is_realtime = quote_timeframe == "REAL-TIME" and trade_timeframe == "REAL-TIME"
        if require_realtime and not is_realtime:
            return None
        if require_realtime and not (
            self._option_timestamp_is_fresh(quote.get("last_updated"), max_age_seconds)
            and self._option_timestamp_is_fresh(trade.get("sip_timestamp"), max_age_seconds)
        ):
            return None

        contract = {
            "contractSymbol": details.get("ticker"),
            "underlying": (raw.get("underlying_asset") or {}).get("ticker", underlying),
            "contractType": (details.get("contract_type") or "").upper(),
            "strike": details.get("strike_price"),
            "expiry": details.get("expiration_date"),
            "bid": quote.get("bid"),
            "ask": quote.get("ask"),
            "lastPrice": trade.get("price"),
            "volume": day.get("volume"),
            "openInterest": raw.get("open_interest"),
            "impliedVolatility": raw.get("implied_volatility"),
            "quoteTimestamp": self._option_timestamp(quote.get("last_updated")),
            "tradeTimestamp": self._option_timestamp(trade.get("sip_timestamp")),
            "quoteTimeframe": quote_timeframe,
            "tradeTimeframe": trade_timeframe,
            "isRealtime": is_realtime,
        }
        required = ("contractSymbol", "contractType", "strike", "expiry", "bid", "ask", "lastPrice", "volume", "openInterest", "quoteTimestamp", "tradeTimestamp")
        if any(contract[field] is None for field in required):
            return None
        if contract["contractType"] not in ("CALL", "PUT"):
            return None
        if any(float(contract[field]) < 0 for field in ("bid", "ask", "lastPrice", "volume", "openInterest")):
            return None
        return contract

    def get_option_chain_data(
        self,
        symbol: str,
        *,
        require_realtime: bool = True,
        max_age_seconds: int = 120,
    ):
        """Return a real Option Chain snapshot, never underlying OHLCV data."""
        symbol = self.normalize_symbol(symbol)
        url = f"{self.base_url}/v3/snapshot/options/{symbol}"
        params = {"limit": 250, "order": "asc", "sort": "ticker", "apiKey": self.api_key}
        calls, puts = [], []
        fetched_at = datetime.now(timezone.utc).isoformat()
        try:
            while url:
                response = requests.get(url, params=params, timeout=self.timeout)
                params = None
                if response.status_code != 200:
                    self.connected = False
                    self.last_error = f"HTTP {response.status_code}"
                    logger.warning("[%s] Option Chain unavailable for %s: %s", self.provider_name, symbol, self.last_error)
                    return None
                payload = response.json()
                for raw in payload.get("results") or []:
                    contract = self._normalize_option_contract(
                        raw,
                        symbol,
                        require_realtime,
                        max_age_seconds,
                    )
                    if contract is None:
                        continue
                    (calls if contract["contractType"] == "CALL" else puts).append(contract)
                url = payload.get("next_url")
                if url:
                    separator = "&" if "?" in url else "?"
                    url = f"{url}{separator}apiKey={self.api_key}"
            if not calls and not puts:
                self.last_error = "No reliable option contracts"
                return None
            self.connected = True
            self.last_error = None
            return {
                "underlying": symbol,
                "source": self.provider_name,
                "fetchedAt": fetched_at,
                "isRealtime": require_realtime,
                "expiries": sorted({contract["expiry"] for contract in calls + puts}),
                "calls": calls,
                "puts": puts,
            }
        except (requests.RequestException, ValueError, TypeError, AttributeError) as error:
            self.connected = False
            self.last_error = str(error)
            logger.warning("[%s] Option Chain request failed for %s: %s", self.provider_name, symbol, error)
            return None


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

