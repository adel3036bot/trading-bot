import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from core.events import EventType
from core.signal_schema import AssetClass, DataQuality, Direction, InstrumentType, Signal
from images.image_contract import ImagePayloadError, normalize_trade_payload
from images.image_engine import ImageEngine
from telegram_bot.telegram_engine import TelegramEngine


def option_trade(**changes):
    value = {
        "symbol": "SPY",
        "signal_type": "CALL",
        "entry": 5.0,
        "sl": 3.5,
        "tp1": 6.5,
        "tp2": 8.0,
        "tp3": 10.0,
        "current_price": 5.5,
        "expiry": "2026-10-16",
        "contract_rating": "STRONG",
        "signal_time": "10:30 EST",
        "profit": 10.0,
    }
    value.update(changes)
    return value


class _FakeAPI:
    def __init__(self):
        self.messages = []

    def send_message(self, text):
        self.messages.append(text)
        return True

    def send_photo_with_caption(self, image_path, caption):
        raise AssertionError("A rejected image must use text fallback")


class ImageContractPhase3Tests(unittest.TestCase):
    def test_legacy_option_aliases_map_without_recalculating_targets(self):
        payload = normalize_trade_payload(option_trade())
        self.assertEqual(payload["entry_price"], 5.0)
        self.assertEqual(payload["stop_loss"], 3.5)
        self.assertEqual((payload["tp1"], payload["tp2"], payload["tp3"]), (6.5, 8.0, 10.0))
        self.assertEqual(payload["expiry_date"], "2026-10-16")
        self.assertEqual(payload["rating"], "STRONG")

    def test_signal_schema_payload_is_accepted_for_future_gold_rendering(self):
        now = datetime.now(timezone.utc)
        signal = Signal.create(
            asset_class=AssetClass.GOLD,
            instrument_type=InstrumentType.ETF,
            symbol="GLD",
            direction=Direction.BUY,
            context_timeframe="1H",
            confirmation_timeframe="15m",
            entry_timeframe="2m",
            entry=100.0,
            stop_loss=99.0,
            tp1=101.0,
            tp2=102.0,
            tp3=103.0,
            setup="test",
            signal_timestamp=now,
            source_timestamp=now,
            data_quality=DataQuality.VERIFIED,
        )
        payload = normalize_trade_payload(signal)
        self.assertEqual(payload["entry_price"], 100.0)
        self.assertEqual(payload["stop_loss"], 99.0)
        self.assertEqual(payload["entry_timeframe"], "2m")
        self.assertEqual(payload["contract_type"], Direction.BUY)

    def test_missing_new_trade_values_raise_instead_of_being_invented(self):
        engine = ImageEngine()
        with self.assertRaisesRegex(ImagePayloadError, "incomplete_image_payload"):
            engine.generate(EventType.NEW_TRADE, {"symbol": "SPY", "entry": 5.0})

    def test_event_types_use_the_central_enum_and_all_trade_templates_still_dispatch(self):
        engine = ImageEngine()
        event_types = (
            EventType.NEW_TRADE, EventType.TP1, EventType.TP2, EventType.TP3,
            EventType.STOP_LOSS, EventType.OPEN_PROFIT, EventType.MOONSHOT,
            EventType.LEGENDARY, EventType.GOD_MODE, EventType.PROGRESS_UPDATE,
        )
        with patch.object(engine, "build_template_image", return_value=object()), patch.object(engine, "export", return_value="mock.png"):
            for event_type in event_types:
                self.assertEqual(engine.generate(event_type, option_trade()), "mock.png")

    def test_renderer_resolves_assets_from_the_module_root_not_cwd(self):
        engine = ImageEngine()
        self.assertTrue((engine.project_root / "fonts" / "regular.ttf").is_file())
        with patch.object(engine, "build_template_image", return_value=object()), patch.object(engine, "export", return_value="mock.png"):
            self.assertEqual(engine.generate("NEW_TRADE", option_trade()), "mock.png")

    def test_existing_non_trade_templates_remain_renderable_with_ready_data(self):
        engine = ImageEngine()
        # Small canvas keeps this renderer smoke test fast; layout coordinates
        # are deliberately not redesigned in this phase.
        engine.config["canvas_width"] = 160
        engine.config["canvas_height"] = 160
        templates = {
            "news": {"headline": "headline", "body": "body", "source": "source"},
            "breaking": {"headline": "headline", "body": "body", "source": "source"},
            "analysis": {"title": "title", "summary": "summary", "trend": "up"},
            "performance": {"title": "title", "date": "date", "total_trades": 1},
            "daily_report": {"title": "title", "date": "date", "total_trades": 1},
            "weekly_report": {"title": "title", "week_range": "range", "total_trades": 1},
            "monthly_report": {"title": "title", "month": "month", "total_trades": 1},
        }
        for template, payload in templates.items():
            self.assertEqual(engine.build_template_image(template, payload).size, (160, 160))

    def test_rejected_renderer_payload_preserves_telegram_text_fallback(self):
        api = _FakeAPI()
        engine = TelegramEngine(api=api, images=ImageEngine())
        with patch("telegram_bot.telegram_engine.build_message", return_value="safe text"):
            engine.send_signal({"symbol": "SPY"})
        self.assertEqual(api.messages, ["safe text"])


if __name__ == "__main__":
    unittest.main()
