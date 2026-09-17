from datetime import datetime, timedelta, timezone
from pathlib import Path
import os
import uuid
from unittest import TestCase

from database.database import DatabaseManager
from performance_engine import PerformanceEngine


class ReportsPhase8Tests(TestCase):
    def setUp(self):
        root = Path(os.environ.get("ADEL_TEST_RUNTIME_DIR", Path(__file__).parent))
        self.path = root / f"adel_phase8_{uuid.uuid4().hex}.db"
        if self.path.exists(): self.path.unlink()
        self.db = DatabaseManager(str(self.path))

    def tearDown(self):
        if self.path.exists(): self.path.unlink()

    def test_empty_journal_never_invents_performance(self):
        report = PerformanceEngine(journal=self.db).get_journal_report()
        self.assertEqual(report["total_trades"], 0)
        self.assertIsNone(report["win_rate"])
        self.assertIsNone(report["total_profit"])

    def test_real_events_are_counted_without_profit_inference(self):
        signal = {"signal_id": "report-test", "asset_class": "STOCK", "instrument_type": "EQUITY", "symbol": "NVDA", "direction": "BUY", "strategy": "TEST", "entry": 1, "stop_loss": .5, "targets": [2,3,4], "source_timestamp": datetime.now(timezone.utc).isoformat()}
        self.db.record_signal(signal)
        self.db.record_event_once("report-test", "TP1", "TP1")
        self.db.record_event_once("report-test", "STOP_LOSS", "STOP_LOSS")
        report = PerformanceEngine(journal=self.db).get_journal_report()
        self.assertEqual(report["tp1"], 1)
        self.assertEqual(report["stop_loss"], 1)
        self.assertIsNone(report["win_rate"])

    def test_report_dedup_survives_restart(self):
        self.db.record_report("DAILY:2026-09-17", "DAILY", "2026-09-17", "2026-09-18", status="SENT")
        self.assertTrue(DatabaseManager(str(self.path)).report_was_sent("DAILY:2026-09-17"))
