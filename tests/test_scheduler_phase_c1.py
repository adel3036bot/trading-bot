from __future__ import annotations

import sqlite3
from contextlib import redirect_stdout
from datetime import datetime
from io import StringIO
from unittest import TestCase
from unittest.mock import patch

from database.database import DatabaseManager
from daily_scheduler import DailyScheduler
from market.session_calendar import NyseSessionCalendar, RIYADH


class _Telegram:
    class _Api:
        channel_id = "REPORTS_TEST_DESTINATION"

    def __init__(self, success=True):
        self.api = self._Api()
        self.success = success
        self.messages = []

    def send_message(self, text, *, destination=None):
        self.messages.append((text, destination))
        return self.success

    def send_report_with_image(self, _image_path, _text):
        return self.success


class _News:
    def __init__(self, journal, broken=False):
        self.journal = journal
        self.broken = broken

    def morning_news_structured(self):
        if self.broken:
            raise RuntimeError("news unavailable")
        return []


class _SharedMemoryDatabase(DatabaseManager):
    """Diskless journal keeps restart tests independent from Windows temp ACLs."""

    _uri = "file:adel_phase_c1_test?mode=memory&cache=shared"
    _keeper = sqlite3.connect(_uri, uri=True, check_same_thread=False)

    def __init__(self):
        self.db_path = self._uri
        self._init_database()

    def connect(self):
        conn = sqlite3.connect(self.db_path, uri=True, check_same_thread=False)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn


class SchedulerPhaseC1Tests(TestCase):
    @classmethod
    def tearDownClass(cls):
        _SharedMemoryDatabase._keeper.close()

    def setUp(self):
        self.db = _SharedMemoryDatabase()
        conn = self.db.connect()
        conn.execute("DELETE FROM report_deliveries")
        conn.execute("DELETE FROM report_journal")
        conn.commit()
        conn.close()

    def _scheduler(self, telegram=None, news=None):
        with patch("daily_scheduler.ImageEngine", None):
            return DailyScheduler(
                telegram=telegram or _Telegram(),
                news_engine=news or _News(self.db),
            )

    def test_nyse_sessions_cover_dst_winter_weekends_holiday_and_early_close(self):
        calendar = NyseSessionCalendar()
        self.assertTrue(calendar.available)

        summer = calendar.session_for(datetime(2026, 7, 6, 16, 30, tzinfo=RIYADH))
        self.assertEqual((summer.market_open_ksa.hour, summer.market_close_ksa.hour), (16, 23))

        winter = calendar.session_for(datetime(2026, 1, 5, 17, 30, tzinfo=RIYADH))
        self.assertEqual((winter.market_open_ksa.hour, winter.market_close_ksa.hour), (17, 0))
        self.assertEqual(winter.market_close_ksa.date().isoformat(), "2026-01-06")

        self.assertIsNone(calendar.session_for(datetime(2026, 7, 4, 16, 30, tzinfo=RIYADH)))
        self.assertIsNone(calendar.session_for(datetime(2026, 7, 5, 16, 30, tzinfo=RIYADH)))
        self.assertIsNone(calendar.session_for(datetime(2026, 12, 25, 16, 30, tzinfo=RIYADH)))

        early = calendar.session_for(datetime(2026, 11, 27, 19, 0, tzinfo=RIYADH))
        self.assertTrue(early.is_early_close)
        self.assertEqual((early.market_open_ksa.hour, early.market_close_ksa.hour), (17, 21))
        self.assertEqual(calendar.phase_at(datetime(2026, 11, 27, 21, 15, tzinfo=RIYADH)), "AFTER_MARKET")

    def test_scheduler_uses_dynamic_pre_market_market_open_after_market_and_closed_windows(self):
        scheduler = self._scheduler()
        self.assertTrue(scheduler.is_full_pre_market(datetime(2026, 7, 6, 14, 45, tzinfo=RIYADH)))
        self.assertTrue(scheduler.is_pre_market(datetime(2026, 7, 6, 15, 45, tzinfo=RIYADH)))
        self.assertTrue(scheduler.is_market_open(datetime(2026, 7, 6, 16, 30, tzinfo=RIYADH)))
        self.assertTrue(scheduler.is_after_market(datetime(2026, 7, 6, 23, 15, tzinfo=RIYADH)))
        self.assertTrue(scheduler.is_pre_market(datetime(2026, 1, 5, 16, 45, tzinfo=RIYADH)))
        self.assertTrue(scheduler.is_market_open(datetime(2026, 1, 5, 17, 30, tzinfo=RIYADH)))
        self.assertFalse(scheduler.is_market_open(datetime(2026, 7, 4, 16, 30, tzinfo=RIYADH)))

        scheduler.collect_sleep_data = lambda: True
        self.assertEqual(scheduler.run(datetime(2026, 7, 4, 16, 30, tzinfo=RIYADH)), "SLEEP")
        self.assertEqual(scheduler.run(datetime(2026, 7, 5, 16, 30, tzinfo=RIYADH)), "SLEEP")

        evening = []
        scheduler.send_evening_report = lambda: evening.append(True) or True
        self.assertEqual(scheduler.run(datetime(2026, 7, 6, 23, 15, tzinfo=RIYADH)), "AFTER_MARKET")
        self.assertEqual(evening, [True])

    def test_successful_report_delivery_is_persistent_and_restart_safe(self):
        telegram = _Telegram(success=True)
        data = {"template": None, "image_data": None, "text": "safe report"}
        scheduler = self._scheduler(telegram=telegram)
        when = datetime(2026, 7, 6, 10, 5, tzinfo=RIYADH)
        with redirect_stdout(StringIO()):
            self.assertTrue(scheduler.send_report_once(data, report_type="MORNING_REPORT", session="MORNING", now=when))
        report_key = "MORNING_REPORT:MORNING:2026-07-06"
        self.assertTrue(self.db.report_was_sent(report_key))
        self.assertEqual(len(self.db.get_report_deliveries(report_key)), 1)

        restarted = self._scheduler(telegram=telegram)
        with redirect_stdout(StringIO()):
            self.assertTrue(restarted.send_report_once(data, report_type="MORNING_REPORT", session="MORNING", now=when))
        self.assertEqual(len(telegram.messages), 1)
        self.assertEqual(len(self.db.get_report_deliveries(report_key)), 1)

    def test_failed_report_delivery_is_recorded_and_retryable(self):
        data = {"template": None, "image_data": None, "text": "safe report"}
        when = datetime(2026, 7, 6, 23, 15, tzinfo=RIYADH)
        failed = self._scheduler(telegram=_Telegram(success=False))
        with redirect_stdout(StringIO()):
            self.assertFalse(failed.send_report_once(data, report_type="EVENING_PERFORMANCE", session="AFTER_MARKET", now=when))
        report_key = "EVENING_PERFORMANCE:AFTER_MARKET:2026-07-06"
        self.assertFalse(self.db.report_was_sent(report_key))
        self.assertFalse(self.db.get_report_deliveries(report_key)[0]["success"])

        retry = self._scheduler(telegram=_Telegram(success=True))
        with redirect_stdout(StringIO()):
            self.assertTrue(retry.send_report_once(data, report_type="EVENING_PERFORMANCE", session="AFTER_MARKET", now=when))
        deliveries = self.db.get_report_deliveries(report_key)
        self.assertEqual([item["success"] for item in deliveries], [False, True])

    def test_premarket_payload_never_invents_performance_zeroes(self):
        scheduler = self._scheduler()
        scheduler._start_async_task = lambda _name, target: (target() or True)
        scheduler._scan_premarket_opportunities = lambda: {
            "opportunities": [], "candidates": 0, "rejected": 0,
            "analyzed": 0, "available": False, "timed_out": False,
        }
        captured = []
        scheduler.send_report_once = lambda data, **_kwargs: captured.append(data) or True
        with redirect_stdout(StringIO()):
            scheduler.send_morning_news()
        payload = captured[0]["image_data"]
        self.assertIsNone(payload["win_rate"])
        self.assertIsNone(payload["total_profit"])
        self.assertIsNone(payload["total_loss"])

    def test_news_unavailable_does_not_crash_scheduler_path(self):
        scheduler = self._scheduler(news=_News(self.db, broken=True))
        scheduler._start_async_task = lambda _name, target: (target() or True)
        scheduler._scan_premarket_opportunities = lambda: {
            "opportunities": [], "candidates": 0, "rejected": 0,
            "analyzed": 0, "available": False, "timed_out": False,
        }
        with redirect_stdout(StringIO()):
            self.assertTrue(scheduler.send_morning_news())
        self.assertTrue(scheduler.morning_news_sent)

    def test_after_market_news_stays_blocked_until_live_news_is_verified(self):
        scheduler = self._scheduler()
        scheduler.performance.build_evening_structured = lambda: (
            {"template": None, "image_data": None, "text": "journal-backed report"},
            [{"template": None, "text": "must not be sent as news"}],
        )
        scheduler.send_report_once = lambda *_args, **_kwargs: True
        sent = []
        scheduler.send_structured = lambda *args, **kwargs: sent.append((args, kwargs)) or True

        with redirect_stdout(StringIO()):
            self.assertTrue(scheduler._send_evening_report_sync())
        self.assertEqual(sent, [])


if __name__ == "__main__":
    import unittest
    unittest.main()
