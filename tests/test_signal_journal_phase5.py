import sqlite3
import os
import uuid
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from core.events import EventType
from core.signal_schema import AssetClass, DataQuality, Direction, InstrumentType, Signal
from database.database import DatabaseManager
from telegram_bot.telegram_engine import TelegramEngine


def signal(asset_class, instrument_type, direction, symbol="GLD", **changes):
    now = datetime.now(timezone.utc)
    values = {
        "asset_class": asset_class,
        "instrument_type": instrument_type,
        "symbol": symbol,
        "direction": direction,
        "context_timeframe": "1H",
        "confirmation_timeframe": "15m",
        "entry_timeframe": "5m",
        "entry": 100.0,
        "stop_loss": 99.0,
        "tp1": 101.0,
        "tp2": 102.0,
        "tp3": 103.0,
        "setup": "journal_test",
        "signal_timestamp": now,
        "source_timestamp": now,
        "data_quality": DataQuality.VERIFIED,
    }
    values.update(changes)
    return Signal.create(**values)


class _FakeAPI:
    channel_id = "test-options-room"

    def send_message(self, text):
        return True

    def send_photo_with_caption(self, image_path, caption):
        return True


class _NoImage:
    def generate(self, event_type, trade):
        raise RuntimeError("test image unavailable")


class SignalJournalPhase5Tests(unittest.TestCase):
    def setUp(self):
        root = Path(os.environ.get("ADEL_TEST_RUNTIME_DIR", Path(__file__).parent))
        self.path = str(root / f"adel_phase5_{uuid.uuid4().hex}.db")
        Path(self.path).unlink(missing_ok=True)
        self.extra_paths = []
        self.db = DatabaseManager(self.path)

    def tearDown(self):
        Path(self.path).unlink(missing_ok=True)
        for path in self.extra_paths:
            Path(path).unlink(missing_ok=True)

    def _count(self, table):
        conn = sqlite3.connect(self.path)
        try:
            return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        finally:
            conn.close()

    def test_new_signal_is_persistent_and_duplicate_is_rejected_after_restart(self):
        ready = signal(AssetClass.GOLD, InstrumentType.SPOT, Direction.BUY)
        signal_id, inserted = self.db.record_signal(ready)
        self.assertTrue(inserted)
        self.assertEqual(signal_id, ready.signal_id)

        restarted = DatabaseManager(self.path)
        repeated_id, repeated_insert = restarted.record_signal(ready)
        self.assertEqual(repeated_id, signal_id)
        self.assertFalse(repeated_insert)
        self.assertEqual(self._count("signal_journal"), 1)
        self.assertEqual(self._count("trade_journal"), 1)

    def test_asset_separated_schema_identity_does_not_collide(self):
        now = datetime.now(timezone.utc)
        records = (
            signal(AssetClass.STOCK, InstrumentType.EQUITY, Direction.BUY, "NVDA", signal_timestamp=now),
            signal(AssetClass.OPTIONS, InstrumentType.OPTION, Direction.CALL, "NVDA", signal_timestamp=now, metadata={"contract_symbol": "O:NVDA260619C00100000"}),
            signal(AssetClass.GOLD, InstrumentType.ETF, Direction.BUY, "GLD", signal_timestamp=now),
        )
        ids = [self.db.record_signal(item)[0] for item in records]
        self.assertEqual(len(set(ids)), 3)
        self.assertEqual(self._count("signal_journal"), 3)

    def test_events_and_successful_or_failed_deliveries_link_to_original_signal(self):
        ready = signal(AssetClass.OPTIONS, InstrumentType.OPTION, Direction.CALL, "SPY", metadata={"contract_symbol": "O:SPY260619C00100000"})
        signal_id, _ = self.db.record_signal(ready)
        event_id = self.db.record_event(signal_id, EventType.NEW_TRADE.value, metadata={"stage": 0})
        self.db.record_delivery(signal_id, "options-room", event_id=event_id, success=True)
        self.db.record_delivery(signal_id, "options-room", event_id=event_id, success=False, failure_reason="telegram_api_returned_false")

        conn = sqlite3.connect(self.path)
        try:
            event = conn.execute("SELECT signal_id, trade_id, event_type FROM signal_events WHERE id = ?", (event_id,)).fetchone()
            deliveries = conn.execute("SELECT success, failure_reason FROM signal_deliveries ORDER BY id").fetchall()
        finally:
            conn.close()
        self.assertEqual(event[0], signal_id)
        self.assertIsNotNone(event[1])
        self.assertEqual(event[2], "NEW_TRADE")
        self.assertEqual(deliveries, [(1, None), (0, "telegram_api_returned_false")])

    def test_existing_tables_and_rows_are_preserved_by_additive_migration(self):
        legacy = str(Path(self.path).with_name("_phase5_legacy_test.db"))
        Path(legacy).unlink(missing_ok=True)
        self.extra_paths.append(legacy)
        conn = sqlite3.connect(legacy)
        try:
            conn.execute("CREATE TABLE legacy_records (id INTEGER PRIMARY KEY, note TEXT)")
            conn.execute("INSERT INTO legacy_records (note) VALUES ('keep-me')")
            conn.commit()
        finally:
            conn.close()

        DatabaseManager(legacy)
        conn = sqlite3.connect(legacy)
        try:
            self.assertEqual(conn.execute("SELECT note FROM legacy_records").fetchone()[0], "keep-me")
            tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        finally:
            conn.close()
        self.assertTrue({"users", "plans", "subscriptions", "settings", "signal_journal", "trade_journal", "signal_events", "signal_deliveries"}.issubset(tables))

    def test_telegram_delivery_records_ready_legacy_option_signal_without_secrets(self):
        journal = DatabaseManager(self.path)
        trade = {
            "symbol": "SPY", "contract_symbol": "O:SPY260619C00100000", "signal_type": "CALL",
            "approval": "A", "entry": 5.0, "sl": 3.5, "tp1": 6.5, "tp2": 8.0, "tp3": 10.0,
            "created_at": "2026-09-17T10:00:00+03:00", "status": "NEW",
        }
        engine = TelegramEngine(api=_FakeAPI(), images=_NoImage(), journal=journal)
        with patch("telegram_bot.telegram_engine.build_message", return_value="ready text"):
            engine.send_signal(trade)

        self.assertIn("signal_id", trade)
        self.assertEqual(self._count("signal_journal"), 1)
        self.assertEqual(self._count("signal_events"), 1)
        self.assertEqual(self._count("signal_deliveries"), 1)
        conn = sqlite3.connect(self.path)
        try:
            reason = conn.execute("SELECT failure_reason FROM signal_deliveries").fetchone()[0]
        finally:
            conn.close()
        self.assertIsNone(reason)

    def test_metadata_secrets_are_redacted_before_persistence(self):
        ready = signal(
            AssetClass.GOLD,
            InstrumentType.SPOT,
            Direction.BUY,
            metadata={"safe": "kept", "telegram_token": "must-not-persist", "api_key": "must-not-persist"},
        )
        signal_id, _ = self.db.record_signal(ready)
        record = self.db.get_signal_journal(signal_id)
        self.assertIn("[REDACTED]", record["metadata_json"])
        self.assertIn("kept", record["metadata_json"])
        self.assertNotIn("must-not-persist", record["metadata_json"])


if __name__ == "__main__":
    unittest.main()
