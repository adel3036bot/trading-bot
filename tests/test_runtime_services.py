import unittest
from unittest.mock import patch

from core.runtime_health import RuntimeHealth
from core.runtime_services import build_runtime_services


class RuntimeServicesTests(unittest.TestCase):
    @patch("core.runtime_services.TelegramApp")
    @patch("core.runtime_services.DailyScheduler")
    @patch("core.runtime_services.NewsEngine")
    @patch("core.runtime_services.TelegramEngine")
    @patch("core.runtime_services.DataEngine")
    @patch("core.runtime_services.DatabaseManager")
    def test_composition_uses_one_shared_database_and_registers_delivery_channel(
        self, database, data_engine, telegram_engine, news_engine, scheduler, telegram_app,
    ):
        health = RuntimeHealth()
        services = build_runtime_services(
            token="test-token", channel_url="https://t.me/ADELSmartSignals", admin_id=1, health=health,
        )

        self.assertIs(services.database, database.return_value)
        telegram_engine.assert_called_once_with(journal=database.return_value)
        news_engine.assert_called_once_with(journal=database.return_value)
        self.assertIs(services.scheduler, scheduler.return_value)
        self.assertIn(services.telegram, services.event_router.channels)
        telegram_app.assert_called_once_with(
            token="test-token", channel_url="https://t.me/ADELSmartSignals", admin_id=1, db=database.return_value,
        )


if __name__ == "__main__":
    unittest.main()
