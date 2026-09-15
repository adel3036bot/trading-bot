from abc import ABC, abstractmethod
import pandas as pd


class BaseProvider(ABC):
    """
    Base interface for all market data providers.
    Every provider (Finnhub, FMP, Massive, ...)
    must inherit from this class.
    """

    @abstractmethod
    def health_check(self) -> bool:
        """Check if provider is online."""
        pass

    @abstractmethod
    def fetch_stock_data(self, symbol: str) -> pd.DataFrame:
        """Fetch OHLCV data."""
        pass

    @abstractmethod
    def fetch_option_chain(self, symbol: str):
        """Fetch option chain."""
        pass

    @abstractmethod
    def fetch_vix_data(self) -> pd.DataFrame:
        """Fetch VIX data."""
        pass

    @abstractmethod
    def fetch_gold_data(self) -> pd.DataFrame:
        """Fetch Gold data."""
        pass

    @abstractmethod
    def fetch_crypto_data(self, symbol: str) -> pd.DataFrame:
        """Fetch Crypto data."""
        pass

    @abstractmethod
    def fetch_economic_calendar(self):
        """Fetch economic calendar."""
        pass

    @abstractmethod
    def close(self):
        """Release resources."""
        pass

        