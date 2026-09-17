"""Instrument-aware risk calculations for already-approved trade setups."""

from __future__ import annotations

from dataclasses import dataclass

from core.signal_schema import Direction, InstrumentType, Signal


@dataclass(frozen=True, slots=True)
class RiskPlan:
    instrument_type: InstrumentType
    risk_per_unit: float
    reward_to_tp1: float
    reward_to_tp2: float
    reward_to_tp3: float


class RiskManager:
    """Does not invent stops or contract sizing; it validates supplied risk geometry."""

    SUPPORTED_GOLD_INSTRUMENTS = frozenset(
        (InstrumentType.ETF, InstrumentType.SPOT, InstrumentType.FUTURE)
    )

    def plan_for(self, signal: Signal) -> RiskPlan:
        if signal.asset_class.value == "GOLD" and signal.instrument_type not in self.SUPPORTED_GOLD_INSTRUMENTS:
            raise ValueError("unsupported_gold_instrument_type")

        risk = abs(signal.entry - signal.stop_loss)
        if risk <= 0:
            raise ValueError("risk_must_be_positive")

        def reward(target: float) -> float:
            if signal.direction in (Direction.BUY, Direction.CALL):
                return (target - signal.entry) / risk
            return (signal.entry - target) / risk

        ratios = (reward(signal.tp1), reward(signal.tp2), reward(signal.tp3))
        if min(ratios) <= 0:
            raise ValueError("target_must_be_on_profit_side")
        return RiskPlan(signal.instrument_type, risk, *ratios)
