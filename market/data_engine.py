# ==================================================
# ADEL SMART BOT V3
# DATA ENGINE
# PRODUCTION READY
# ==================================================

"""
==================================================

ADEL SMART BOT

DATA ENGINE

Responsibilities

- Central Data Layer
- Receive Requests
- Request Data From Source Engine
- Return Standard Data
- Keep Compatibility With AdelSmartBot

No Analysis

No Indicators

No Signals

Only Data Management

==================================================
"""

# ==================================================
# IMPORTS
# ==================================================

import logging

# ==================================================
# SOURCE ENGINE
# ==================================================

from market.source_engine import (

    get_stock_data as source_get_stock_data,

    get_index_data as source_get_index_data,

    get_etf_data as source_get_etf_data,

    get_vix_data as source_get_vix_data,

    get_gold_data as source_get_gold_data,

    get_crypto_data as source_get_crypto_data,

    get_option_data as source_get_option_data

)

# ==================================================
# LOGGER
# ==================================================

logger = logging.getLogger("DataEngine")

# ==================================================
# DATA ENGINE
# ==================================================

class DataEngine:

    """
    Central Data Manager

    Responsible for requesting data
    from Source Engine.

    This class contains no analysis.

    No indicators.

    No signals.

    Only standardized data requests.
    """

    def __init__(self):

        self.name = "DATA_ENGINE"

        logger.info(

            "Data Engine Initialized"

        )

# ==================================================
# STOCK
# ==================================================

    def get_stock_data(

        self,
        symbol: str,
        timeframe: str = "1D",
        candles: int = 200

    ):

        return source_get_stock_data(

            symbol=symbol,

            timeframe=timeframe,

            candles=candles

        )

# ==================================================
# INDEX
# ==================================================

    def get_index_data(

        self,
        symbol: str,
        timeframe: str = "1D",
        candles: int = 200

    ):

        return source_get_index_data(

            symbol=symbol,

            timeframe=timeframe,

            candles=candles

        )

# ==================================================
# ETF
# ==================================================

    def get_etf_data(

        self,
        symbol: str,
        timeframe: str = "1D",
        candles: int = 200

    ):

        return source_get_etf_data(

            symbol=symbol,

            timeframe=timeframe,

            candles=candles

        )

# ==================================================
# MARKET DATA FUNCTIONS
# ==================================================

    def get_vix_data(

        self,
        timeframe: str = "1D",
        candles: int = 200

    ):

        return source_get_vix_data(

            timeframe=timeframe,

            candles=candles

        )


    def get_gold_data(

        self,
        timeframe: str = "1D",
        candles: int = 200

    ):

        return source_get_gold_data(

            timeframe=timeframe,

            candles=candles

        )


    def get_crypto_data(

        self,
        symbol: str = "BTC-USD",
        timeframe: str = "1D",
        candles: int = 200

    ):

        return source_get_crypto_data(

            symbol=symbol,

            timeframe=timeframe,

            candles=candles

        )


    def get_option_chain_data(

        self,
        symbol: str,
        timeframe: str = "1D",
        candles: int = 200

    ):

        return source_get_option_data(

            symbol=symbol,

            timeframe=timeframe,

            candles=candles

        )
        
# ==================================================
# ENGINE STATUS
# ==================================================

    def engine_name(

        self

    ):

        return self.name


    def engine_information(

        self

    ):

        return {

            "engine": self.name,

            "stock": True,

            "index": True,

            "etf": True,

            "vix": True,

            "gold": True,

            "crypto": True,

            "option_chain": True,

            "source_engine": True,

            "version": "3.0"

        }


    def ping(

        self

    ):

        logger.info(

            "Data Engine Ready"

        )

        return True


# ==================================================
# GLOBAL INSTANCE
# ==================================================

engine = DataEngine()


# ==================================================
# COMPATIBILITY FUNCTIONS
# ==================================================

def get_stock_data(

    symbol,
    timeframe="1D",
    candles=200

):

    return engine.get_stock_data(

        symbol,

        timeframe,

        candles

    )


def get_index_data(

    symbol,
    timeframe="1D",
    candles=200

):

    return engine.get_index_data(

        symbol,

        timeframe,

        candles

    )


def get_etf_data(

    symbol,
    timeframe="1D",
    candles=200

):

    return engine.get_etf_data(

        symbol,

        timeframe,

        candles

    )


def get_vix_data(

    timeframe="1D",
    candles=200

):

    return engine.get_vix_data(

        timeframe,

        candles

    )


def get_gold_data(

    timeframe="1D",
    candles=200

):

    return engine.get_gold_data(

        timeframe,

        candles

    )


def get_crypto_data(

    symbol="BTC-USD",
    timeframe="1D",
    candles=200

):

    return engine.get_crypto_data(

        symbol,

        timeframe,

        candles

    )


def get_option_chain_data(

    symbol,
    timeframe="1D",
    candles=200

):

    return engine.get_option_chain_data(

        symbol,

        timeframe,

        candles

    )
    
# ==================================================
# TEST
# ==================================================

if __name__ == "__main__":

    engine = DataEngine()

    print("=" * 60)
    print("ADEL SMART BOT - DATA ENGINE")
    print("=" * 60)

    print("\nEngine Information")

    print(

        engine.engine_information()

    )

    print("\nData Engine Ready.")

    