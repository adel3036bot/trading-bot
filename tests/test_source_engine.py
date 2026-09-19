"""Safe tests for the current module-based SourceEngine."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import unittest

import pandas as pd

from market import source_engine


class _Provider:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = 0

    def get_market_data(self, **_kwargs):
        self.calls += 1
        if self.error:
            raise self.error
        return self.response


def _frame(rows=250):
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return pd.DataFrame({
        "Datetime": [base + timedelta(minutes=index) for index in range(rows)],
        "Open": [100.0] * rows,
        "High": [101.0] * rows,
        "Low": [99.0] * rows,
        "Close": [100.5] * rows,
        "Volume": [1000] * rows,
    })


class SourceEngineTests(unittest.TestCase):
    def setUp(self):
        self.providers = dict(source_engine.PROVIDERS)
        self.priority = list(source_engine.SOURCE_PRIORITY)
        self.status = dict(source_engine.PROVIDER_STATUS)
        self.cache = dict(source_engine.CACHE)
        source_engine.PROVIDERS.clear()
        source_engine.SOURCE_PRIORITY[:] = ["MASSIVE", "FINNHUB"]
        source_engine.PROVIDER_STATUS["MASSIVE"] = True
        source_engine.PROVIDER_STATUS["FINNHUB"] = True
        source_engine.clear_cache()

    def tearDown(self):
        source_engine.PROVIDERS.clear()
        source_engine.PROVIDERS.update(self.providers)
        source_engine.SOURCE_PRIORITY[:] = self.priority
        source_engine.PROVIDER_STATUS.clear()
        source_engine.PROVIDER_STATUS.update(self.status)
        source_engine.clear_cache()
        source_engine.CACHE.update(self.cache)

    def test_current_source_engine_falls_back_after_provider_failure(self):
        failed = _Provider(error=RuntimeError("provider unavailable"))
        working = _Provider(response=_frame())
        source_engine.PROVIDERS.update({"MASSIVE": failed, "FINNHUB": working})

        result = source_engine.get_stock_data("AAPL", candles=200)

        self.assertIsNotNone(result)
        self.assertEqual(failed.calls, 1)
        self.assertEqual(working.calls, 1)
        self.assertEqual(list(result.columns), ["Datetime", "Open", "High", "Low", "Close", "Volume"])

    def test_current_source_engine_caches_validated_market_data(self):
        provider = _Provider(response=_frame())
        source_engine.PROVIDERS.update({"MASSIVE": provider})
        source_engine.SOURCE_PRIORITY[:] = ["MASSIVE"]

        first = source_engine.get_stock_data("NVDA", candles=200)
        second = source_engine.get_stock_data("NVDA", candles=200)

        self.assertIsNotNone(first)
        self.assertIsNotNone(second)
        self.assertEqual(provider.calls, 1)


if __name__ == "__main__":
    unittest.main()
