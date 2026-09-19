from types import SimpleNamespace
import unittest
from unittest.mock import patch

from core.runtime_health import ServiceState
from core.startup_preflight import run_preflight


class _Connection:
    def close(self):
        return None


class _Database:
    def connect(self):
        return _Connection()


class _Calendar:
    available = True


class StartupPreflightTests(unittest.TestCase):
    def _config(self, **overrides):
        values = {
            "BOT_TOKEN": "configured",
            "CHAT_ID": "configured",
            "CHANNEL_URL": "https://t.me/ADELSmartSignals",
            "ADMIN_ID": 1,
        }
        values.update(overrides)
        return SimpleNamespace(**values)

    @patch("core.startup_preflight.NyseSessionCalendar", return_value=_Calendar())
    @patch("core.startup_preflight.DatabaseManager", return_value=_Database())
    @patch("core.startup_preflight.importlib.import_module")
    def test_preflight_reports_safe_ready_and_external_waiting_states(self, import_config, _db, _calendar):
        import_config.return_value = self._config()
        report = run_preflight()

        self.assertTrue(report.ok)
        self.assertEqual(report.health.get("database").state, ServiceState.READY)
        self.assertEqual(report.health.get("nyse_calendar").state, ServiceState.READY)
        self.assertEqual(report.health.get("market_data").state, ServiceState.WAITING_FOR_DATA_PROVIDER)
        self.assertEqual(report.health.get("news").state, ServiceState.WAITING_FOR_NEWS_VERIFICATION)

    @patch("core.startup_preflight.importlib.import_module")
    def test_missing_required_config_fails_without_echoing_values(self, import_config):
        import_config.return_value = self._config(BOT_TOKEN="")
        report = run_preflight()

        self.assertFalse(report.ok)
        self.assertIn("required_config_missing:BOT_TOKEN", report.fatal)
        self.assertNotIn("configured", report.safe_summary())


if __name__ == "__main__":
    unittest.main()
