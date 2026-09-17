import sys
import unittest
from unittest.mock import patch

# The existing interface logs an emoji during import; make this test portable
# on Windows consoles that otherwise default to cp1256.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import AdelSmartBot as bot


class _NewsEngine:
    def has_high_impact_event_window(self):
        return False


class AdelBootstrapPhase2Tests(unittest.TestCase):
    def test_missing_data_does_not_manufacture_an_option_direction(self):
        with patch.object(bot, "get_stock_data", return_value=None):
            self.assertIsNone(bot.get_trend("NO_DATA"))

    def test_one_symbol_failure_does_not_stop_watchlist_scan(self):
        watchlist = {
            "INDICES": ["BROKEN"],
            "ETFS": ["SAFE"],
            "STOCKS": [],
            "ENERGY": [],
            "GOLD": [],
            "BITCOIN": [],
        }
        market = {"market_score": 80, "market_bias": "BULLISH 📈"}
        with (
            patch.object(bot, "WATCHLIST", watchlist),
            patch.object(bot, "get_cached_market", return_value=market),
            patch.object(bot, "create_trade", side_effect=(RuntimeError("provider failed"), None)),
        ):
            self.assertEqual(bot.scan_watchlist("MARKET_OPEN", _NewsEngine()), [])


if __name__ == "__main__":
    unittest.main()
