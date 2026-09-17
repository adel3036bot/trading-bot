"""Adapters between UniverseEngine and SourceEngine/provider layer."""
from market import source_engine

class SourceEngineUniverseReference:
    def iter_us_stocks(self, max_pages=None):
        provider = source_engine.get_provider("MASSIVE")
        if provider is None: return iter(())
        return provider.iter_reference_tickers(max_pages=max_pages)

class ConservativeQuoteAdapter:
    """OHLCV close is not a live quote; expose it as UNKNOWN for live eligibility."""
    def get_quote(self, symbol):
        data = source_engine.get_stock_data(symbol, timeframe="1D", candles=2)
        if data is None or data.empty: return None
        return {"last": float(data.iloc[-1]["Close"]), "data_quality":"UNKNOWN", "realtime":False}
