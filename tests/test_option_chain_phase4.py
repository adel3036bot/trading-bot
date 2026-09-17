import time
import unittest
import sys
from unittest.mock import patch

import pandas as pd

# Test-only console normalization: the known BotInterface cp1256/emoji debt
# must not prevent an isolated data-contract test from importing the bot.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import AdelSmartBot as bot
from market import source_engine
from market.sources.massive_provider import MassiveProvider


def option_snapshot(contract_type="call", **changes):
    now_ns = int(time.time() * 1_000_000_000)
    raw = {
        "details": {
            "ticker": "O:SPY260619C00100000",
            "contract_type": contract_type,
            "expiration_date": "2026-06-19",
            "strike_price": 100.0,
        },
        "underlying_asset": {"ticker": "SPY"},
        "last_quote": {"bid": 4.9, "ask": 5.1, "last_updated": now_ns, "timeframe": "REAL-TIME"},
        "last_trade": {"price": 5.0, "sip_timestamp": now_ns, "timeframe": "REAL-TIME"},
        "day": {"volume": 150},
        "open_interest": 1200,
        "implied_volatility": 0.25,
    }
    for section, values in changes.items():
        if section in raw and isinstance(values, dict):
            raw[section].update(values)
        else:
            raw[section] = values
    return raw


class _Response:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self):
        return self._payload


class _NoChainProvider:
    def __init__(self):
        self.ohlcv_called = False

    def get_option_chain_data(self, symbol, **kwargs):
        return None

    def get_market_data(self, *args, **kwargs):
        self.ohlcv_called = True
        raise AssertionError("Option Chain must never fall back to underlying OHLCV")


class _DelayedChainProvider(_NoChainProvider):
    def get_option_chain_data(self, symbol, **kwargs):
        return {
            "underlying": symbol,
            "fetchedAt": "2026-09-17T10:00:00+00:00",
            "isRealtime": False,
            "calls": [{"contractSymbol": "not-used"}],
            "puts": [],
        }


def valid_chain():
    return {
        "underlying": "SPY",
        "source": "MASSIVE",
        "fetchedAt": "2026-09-17T10:00:00+00:00",
        "isRealtime": True,
        "expiries": ["2026-06-19"],
        "calls": [{
            "contractSymbol": "O:SPY260619C00105000", "underlying": "SPY", "contractType": "CALL",
            "strike": 105.0, "expiry": "2026-06-19", "bid": 4.9, "ask": 5.1,
            "lastPrice": 5.0, "volume": 150, "openInterest": 1200,
            "impliedVolatility": 0.25, "quoteTimestamp": "2026-09-17T10:00:00+00:00",
            "tradeTimestamp": "2026-09-17T10:00:00+00:00", "quoteTimeframe": "REAL-TIME",
            "tradeTimeframe": "REAL-TIME", "isRealtime": True,
        }],
        "puts": [{
            "contractSymbol": "O:SPY260619P00095000", "underlying": "SPY", "contractType": "PUT",
            "strike": 95.0, "expiry": "2026-06-19", "bid": 4.9, "ask": 5.1,
            "lastPrice": 5.0, "volume": 150, "openInterest": 1200,
            "impliedVolatility": 0.25, "quoteTimestamp": "2026-09-17T10:00:00+00:00",
            "tradeTimestamp": "2026-09-17T10:00:00+00:00", "quoteTimeframe": "REAL-TIME",
            "tradeTimeframe": "REAL-TIME", "isRealtime": True,
        }],
    }


class OptionChainPhase4Tests(unittest.TestCase):
    def setUp(self):
        self.provider = MassiveProvider()

    def test_real_contract_snapshot_normalizes_required_fields(self):
        response = _Response(payload={"results": [option_snapshot()], "next_url": None})
        with patch("market.sources.massive_provider.requests.get", return_value=response):
            chain = self.provider.get_option_chain_data("SPY")
        self.assertEqual(chain["source"], "MASSIVE")
        contract = chain["calls"][0]
        self.assertEqual(contract["contractSymbol"], "O:SPY260619C00100000")
        self.assertEqual(contract["contractType"], "CALL")
        self.assertTrue(contract["isRealtime"])
        self.assertIn("quoteTimestamp", contract)
        self.assertIn("tradeTimestamp", contract)

    def test_empty_missing_and_delayed_contracts_are_rejected(self):
        cases = (
            {"results": [], "next_url": None},
            {"results": [option_snapshot(last_quote={"bid": None})], "next_url": None},
            {"results": [option_snapshot(last_quote={"timeframe": "DELAYED"})], "next_url": None},
            {"results": [option_snapshot(last_trade={"sip_timestamp": int((time.time() - 121) * 1_000_000_000)})], "next_url": None},
        )
        for payload in cases:
            with self.subTest(payload=payload):
                with patch("market.sources.massive_provider.requests.get", return_value=_Response(payload=payload)):
                    self.assertIsNone(self.provider.get_option_chain_data("SPY"))

    def test_provider_failure_returns_no_chain(self):
        with patch("market.sources.massive_provider.requests.get", return_value=_Response(status_code=403)):
            self.assertIsNone(self.provider.get_option_chain_data("QQQ"))

    def test_source_engine_never_falls_back_to_ohlcv(self):
        provider = _NoChainProvider()
        with patch.object(source_engine, "provider_order", return_value=["TEST"]), \
             patch.object(source_engine, "get_provider", return_value=provider):
            self.assertIsNone(source_engine.request_option_chain("SPY"))
        self.assertFalse(provider.ohlcv_called)

    def test_source_engine_rejects_unproven_realtime_chain(self):
        provider = _DelayedChainProvider()
        with patch.object(source_engine, "provider_order", return_value=["TEST"]), \
             patch.object(source_engine, "get_provider", return_value=provider):
            self.assertIsNone(source_engine.request_option_chain("SPY"))
        self.assertFalse(provider.ohlcv_called)

    def test_contract_selection_reads_real_chain_for_call_and_put(self):
        prices = pd.DataFrame({"Close": [100.0]})
        with patch.object(bot, "get_stock_data", return_value=prices), \
             patch.object(bot, "get_option_chain_data", return_value=valid_chain()):
            call = bot.get_best_option("SPY", "CALL")
            put = bot.get_best_option("SPY", "PUT")
        self.assertEqual(call["contract_symbol"], "O:SPY260619C00105000")
        self.assertEqual(put["contract_symbol"], "O:SPY260619P00095000")
        self.assertEqual((call["bid"], call["ask"]), (4.9, 5.1))

    def test_no_expiry_or_no_suitable_strike_means_no_contract(self):
        prices = pd.DataFrame({"Close": [100.0]})
        without_expiry = valid_chain()
        without_expiry["expiries"] = []
        no_strike = valid_chain()
        no_strike["calls"][0]["strike"] = 130.0
        with patch.object(bot, "get_stock_data", return_value=prices), \
             patch.object(bot, "get_option_chain_data", return_value=without_expiry):
            self.assertIsNone(bot.get_best_option("SPY", "CALL"))
        with patch.object(bot, "get_stock_data", return_value=prices), \
             patch.object(bot, "get_option_chain_data", return_value=no_strike):
            self.assertIsNone(bot.get_best_option("SPY", "CALL"))

    def test_option_chain_contract_does_not_change_stock_or_gold_paths(self):
        self.assertIsNot(source_engine.get_option_data, source_engine.request_market_data)
        self.assertTrue(callable(source_engine.get_stock_data))
        self.assertTrue(callable(source_engine.get_gold_data))


if __name__ == "__main__":
    unittest.main()
