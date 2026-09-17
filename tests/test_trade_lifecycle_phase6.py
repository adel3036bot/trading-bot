import sqlite3
import os
import uuid
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from auto_update_engine import PriceUpdate
from core.event_router import EventRouter
from core.events import EventType, TradeEvent
from core.signal_schema import DataQuality, InstrumentType
from core.signal_schema import AssetClass
from core.telegram_router import TelegramRouter
from core.trade_lifecycle import TradeLifecycle
from database.database import DatabaseManager
from telegram_bot.telegram_engine import TelegramEngine
from trade_manager import build_message


class _CaptureChannel:
    def __init__(self):
        self.events = []

    def handle_event(self, event):
        self.events.append(event)


class _FalseAPI:
    channel_id = "options-room"

    def send_message(self, text):
        return False

    def send_photo_with_caption(self, image_path, caption):
        return False


class _RouteAPI:
    channel_id = "default-room"

    def __init__(self):
        self.destinations = []

    def send_message(self, text, *, destination=None):
        self.destinations.append(destination or self.channel_id)
        return True

    def send_photo_with_caption(self, image_path, caption, *, destination=None):
        self.destinations.append(destination or self.channel_id)
        return True


class _NoImage:
    def generate(self, event_type, trade):
        raise RuntimeError("test image unavailable")


def option_trade(**changes):
    values = {
        "asset_class": "OPTIONS",
        "instrument_type": "OPTION",
        "symbol": "SPY",
        "contract_symbol": "O:SPY260619C00100000",
        "direction": "CALL",
        "strategy": "existing_options_strategy",
        "entry": 10.0,
        "sl": 7.0,
        "tp1": 13.0,
        "tp2": 16.0,
        "tp3": 20.0,
        "stage": 0,
        "status": "NEW",
        "created_at": "2026-09-17T10:00:00+03:00",
        "source_timestamp": "2026-09-17T10:00:00+03:00",
        # Existing formatter fields; lifecycle does not derive them.
        "contract_name": "SPY 100 CALL",
        "grade": "A",
        "score": 90,
        "expiry": "2026-06-19",
        "contract_duration": "daily",
        "market_status": "ready",
        "secondary_market_status": "ready",
        "signal_time": "10:00",
        "reason_1": "existing reason 1",
        "reason_2": "existing reason 2",
        "reason_3": "existing reason 3",
    }
    values.update(changes)
    return values


class TradeLifecyclePhase6Tests(unittest.TestCase):
    def setUp(self):
        root = Path(os.environ.get("ADEL_TEST_RUNTIME_DIR", Path(__file__).parent))
        self.path = str(root / f"adel_phase6_{uuid.uuid4().hex}.db")
        Path(self.path).unlink(missing_ok=True)
        self.journal = DatabaseManager(self.path)
        self.capture = _CaptureChannel()
        self.router = EventRouter()
        self.router.register_channel(self.capture)
        self.lifecycle = TradeLifecycle(self.journal, self.router)

    def tearDown(self):
        Path(self.path).unlink(missing_ok=True)

    @staticmethod
    def option_price(price, *, symbol="O:SPY260619C00100000", age_seconds=0, quality=DataQuality.VERIFIED):
        return PriceUpdate(
            symbol=symbol,
            instrument_type=InstrumentType.OPTION,
            price=price,
            source_timestamp=datetime.now(timezone.utc) - timedelta(seconds=age_seconds),
            data_quality=quality,
        )

    def _event_types(self):
        conn = sqlite3.connect(self.path)
        try:
            return [row[0] for row in conn.execute("SELECT event_type FROM signal_events ORDER BY id")]
        finally:
            conn.close()

    def test_new_tp_targets_stop_and_original_levels_are_persistent(self):
        trade = self.lifecycle.start_trade(option_trade())
        signal_id = trade["signal_id"]
        self.assertEqual(self._event_types(), ["NEW_TRADE"])

        updated, events = self.lifecycle.process_price(signal_id, self.option_price(13.0))
        self.assertEqual([event.type for event in events], [EventType.TP1])
        self.assertEqual(updated["sl"], 10.0)  # Existing TP1 rule: move stop to entry.
        stored_signal = self.journal.get_signal_journal(signal_id)
        self.assertEqual(stored_signal["stop_loss"], 7.0)  # Original remains immutable.

        updated, events = self.lifecycle.process_price(signal_id, self.option_price(16.0))
        self.assertEqual([event.type for event in events], [EventType.TP2])
        self.assertEqual(updated["sl"], 13.0)
        updated, events = self.lifecycle.process_price(signal_id, self.option_price(20.0))
        self.assertEqual([event.type for event in events], [EventType.TP3])
        self.assertEqual(updated["sl"], 16.0)

        stopped = self.lifecycle.start_trade(option_trade(contract_symbol="O:SPY260619C00105000", created_at="2026-09-17T10:01:00+03:00"))
        stopped_state, stopped_events = self.lifecycle.process_price(stopped["signal_id"], self.option_price(7.0, symbol="O:SPY260619C00105000"))
        self.assertEqual([event.type for event in stopped_events], [EventType.STOP_LOSS])
        self.assertTrue(stopped_state["is_closed"])

    def test_restart_recovery_and_event_deduplication(self):
        trade = self.lifecycle.start_trade(option_trade())
        signal_id = trade["signal_id"]
        self.lifecycle.process_price(signal_id, self.option_price(13.0))

        restarted = TradeLifecycle(DatabaseManager(self.path), EventRouter())
        recovered = restarted.recover_active_trades()
        self.assertEqual(len(recovered), 1)
        self.assertEqual(recovered[0]["stage"], 1)
        _, events = restarted.process_price(signal_id, self.option_price(13.5))
        self.assertEqual([event.type for event in events], [EventType.PROGRESS_UPDATE])
        _, repeated = restarted.process_price(signal_id, self.option_price(13.5))
        self.assertEqual(repeated, [])
        self.assertEqual(self._event_types().count("TP1"), 1)
        self.assertEqual(self._event_types().count("NEW_TRADE"), 1)

    def test_special_and_open_profit_events_do_not_repeat_on_identical_ticks(self):
        trade = self.lifecycle.start_trade(option_trade())
        signal_id = trade["signal_id"]
        for price in (13.0, 16.0, 20.0, 30.0, 60.0, 110.0):
            self.lifecycle.process_price(signal_id, self.option_price(price))
        _, first_repeat = self.lifecycle.process_price(signal_id, self.option_price(110.0))
        self.assertEqual([event.type for event in first_repeat], [EventType.PROGRESS_UPDATE])
        _, repeated = self.lifecycle.process_price(signal_id, self.option_price(110.0))
        self.assertEqual(repeated, [])
        event_types = self._event_types()
        self.assertEqual(event_types.count("MOONSHOT"), 1)
        self.assertEqual(event_types.count("LEGENDARY"), 1)
        self.assertEqual(event_types.count("GOD_MODE"), 1)
        self.assertEqual(event_types.count("OPEN_PROFIT"), 1)

    def test_lifecycle_never_tracks_a_trade_without_a_reliable_base_record(self):
        with self.assertRaisesRegex(ValueError, "journal_asset_class_required"):
            self.lifecycle.start_trade({"symbol": "SPY"})
        self.assertEqual(self.journal.get_active_trade_states(), [])

    def test_missing_stale_or_underlying_option_price_never_changes_state(self):
        trade = self.lifecycle.start_trade(option_trade())
        signal_id = trade["signal_id"]
        for update in (
            self.option_price(None),
            self.option_price(13.0, age_seconds=121),
            self.option_price(13.0, symbol="SPY"),
            self.option_price(13.0, quality=DataQuality.DEGRADED),
        ):
            state, events = self.lifecycle.process_price(signal_id, update)
            self.assertEqual(state["stage"], 0)
            self.assertEqual(events, [])
        self.assertEqual(self._event_types(), ["NEW_TRADE"])

    def test_stock_options_gold_ids_and_manual_final_close_do_not_collide(self):
        option = self.lifecycle.start_trade(option_trade())
        stock = self.lifecycle.start_trade(option_trade(
            asset_class="STOCK", instrument_type="EQUITY", direction="BUY", contract_symbol=None,
            created_at="2026-09-17T10:02:00+03:00",
        ))
        gold = self.lifecycle.start_trade(option_trade(
            asset_class="GOLD", instrument_type="SPOT", symbol="XAUUSD", contract_symbol=None,
            direction="SELL", entry=100.0, sl=101.0, tp1=99.0, tp2=98.0, tp3=97.0,
            created_at="2026-09-17T10:03:00+03:00",
        ))
        self.assertEqual(len({option["signal_id"], stock["signal_id"], gold["signal_id"]}), 3)
        final_state, events = self.lifecycle.close_trade(option["signal_id"], metadata={"reason": "manual"})
        self.assertTrue(final_state["is_closed"])
        self.assertEqual([event.type for event in events], [EventType.TRADE_CLOSED])
        self.assertNotIn(option["signal_id"], [item["signal_id"] for item in self.lifecycle.recover_active_trades()])

    def test_gold_sell_lifecycle_uses_gold_spot_price_not_option_or_stock_price(self):
        gold = self.lifecycle.start_trade(option_trade(
            asset_class="GOLD", instrument_type="SPOT", symbol="XAUUSD", contract_symbol=None,
            direction="SELL", entry=100.0, sl=101.0, tp1=99.0, tp2=98.0, tp3=97.0,
        ))
        update = PriceUpdate(
            symbol="XAUUSD",
            instrument_type=InstrumentType.SPOT,
            price=99.0,
            source_timestamp=datetime.now(timezone.utc),
        )
        state, events = self.lifecycle.process_price(gold["signal_id"], update)
        self.assertEqual(state["stage"], 1)
        self.assertEqual([event.type for event in events], [EventType.TP1])

    def test_telegram_failure_does_not_rollback_event_or_trade_state(self):
        router = EventRouter()
        engine = TelegramEngine(api=_FalseAPI(), images=_NoImage(), journal=self.journal)
        router.register_channel(engine)
        lifecycle = TradeLifecycle(self.journal, router)
        trade = lifecycle.start_trade(option_trade())
        state, events = lifecycle.process_price(trade["signal_id"], self.option_price(13.0))
        self.assertEqual([event.type for event in events], [EventType.TP1])
        self.assertEqual(state["stage"], 1)
        conn = sqlite3.connect(self.path)
        try:
            success_values = [row[0] for row in conn.execute("SELECT success FROM signal_deliveries ORDER BY id")]
        finally:
            conn.close()
        self.assertEqual(success_values, [0, 0])

    def test_central_router_sends_options_event_only_to_options_destination(self):
        api = _RouteAPI()
        routes = TelegramRouter({
            AssetClass.OPTIONS: "options-room",
            AssetClass.STOCK: "stock-room",
            AssetClass.GOLD: "gold-room",
        })
        router = EventRouter()
        router.register_channel(TelegramEngine(api=api, images=_NoImage(), journal=self.journal, router=routes))
        TradeLifecycle(self.journal, router).start_trade(option_trade())
        self.assertEqual(api.destinations, ["options-room"])

    def test_central_router_keeps_stock_options_and_gold_destinations_separate(self):
        api = _RouteAPI()
        routes = TelegramRouter({
            AssetClass.OPTIONS: "options-room",
            AssetClass.STOCK: "stock-room",
            AssetClass.GOLD: "gold-room",
        })
        router = EventRouter()
        router.register_channel(TelegramEngine(api=api, images=_NoImage(), journal=self.journal, router=routes))
        lifecycle = TradeLifecycle(self.journal, router)
        lifecycle.start_trade(option_trade())
        lifecycle.start_trade(option_trade(asset_class="STOCK", instrument_type="EQUITY", direction="BUY", contract_symbol=None, created_at="2026-09-17T10:02:00+03:00"))
        lifecycle.start_trade(option_trade(asset_class="GOLD", instrument_type="SPOT", direction="BUY", symbol="XAUUSD", contract_symbol=None, created_at="2026-09-17T10:03:00+03:00"))
        self.assertEqual(api.destinations, ["options-room", "stock-room", "gold-room"])

    def test_existing_formatter_functions_are_selected_for_ready_events(self):
        trade = option_trade(current_price=13.0, profit=30.0, duration="00:10")
        with patch("trade_manager.random.choice", side_effect=lambda choices: choices[0]):
            self.assertIn("عقد مقترح", build_message(TradeEvent.create(EventType.NEW_TRADE, trade)))
            self.assertIn("الهدف الأول", build_message(TradeEvent.create(EventType.TP1, trade)))
            self.assertIn("انتهت رحلة", build_message(TradeEvent.create(EventType.TRADE_CLOSED, trade)))


if __name__ == "__main__":
    unittest.main()
