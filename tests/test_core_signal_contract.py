from datetime import datetime, timedelta, timezone
import unittest

from core.risk_manager import RiskManager
from core.signal_schema import AssetClass, DataQuality, Direction, InstrumentType, Signal
from core.signal_validator import SignalValidator
from core.telegram_router import TelegramRouter


def gold_signal(**changes):
    now = datetime.now(timezone.utc)
    values = {
        "asset_class": AssetClass.GOLD,
        "instrument_type": InstrumentType.ETF,
        "symbol": "GLD",
        "direction": Direction.BUY,
        "context_timeframe": "1H",
        "confirmation_timeframe": "15m",
        "entry_timeframe": "2m",
        "entry": 100.0,
        "stop_loss": 99.0,
        "tp1": 101.0,
        "tp2": 102.0,
        "tp3": 103.0,
        "setup": "structure_pullback",
        "signal_timestamp": now,
        "source_timestamp": now,
        "data_quality": DataQuality.VERIFIED,
    }
    values.update(changes)
    return Signal.create(**values)


class CoreSignalContractTests(unittest.TestCase):
    def test_gold_signal_keeps_timeframes_and_has_asset_separated_id(self):
        signal = gold_signal()
        self.assertEqual(signal.direction, Direction.BUY)
        self.assertEqual(signal.entry_timeframe, "2m")
        self.assertTrue(signal.signal_id.startswith("GOLD:"))
        self.assertTrue(SignalValidator().validate(signal).accepted)

    def test_stale_data_is_rejected(self):
        stale = gold_signal(source_timestamp=datetime.now(timezone.utc) - timedelta(minutes=6))
        result = SignalValidator().validate(stale)
        self.assertFalse(result.accepted)
        self.assertIn("source_data_stale", result.reasons)

    def test_gold_rejects_call_put(self):
        invalid = gold_signal(direction=Direction.CALL)
        result = SignalValidator().validate(invalid)
        self.assertFalse(result.accepted)
        self.assertIn("gold_direction_must_be_buy_or_sell", result.reasons)

    def test_risk_is_instrument_aware_without_contract_sizing(self):
        plan = RiskManager().plan_for(gold_signal())
        self.assertEqual(plan.instrument_type, InstrumentType.ETF)
        self.assertEqual(plan.risk_per_unit, 1.0)
        self.assertEqual(plan.reward_to_tp3, 3.0)

    def test_router_does_not_mix_gold_and_options(self):
        router = TelegramRouter({AssetClass.GOLD: "gold-chat", AssetClass.OPTIONS: "options-chat"})
        self.assertEqual(router.destination_for(gold_signal()), "gold-chat")


if __name__ == "__main__":
    unittest.main()
