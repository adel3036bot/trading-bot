"""Validation gate enforcing: no reliable data means no signal."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from core.signal_schema import AssetClass, DataQuality, Direction, Signal


@dataclass(frozen=True, slots=True)
class ValidationResult:
    accepted: bool
    reasons: tuple[str, ...] = ()


class SignalValidator:
    """Generic contract checks; strategy-specific rules stay in the strategy."""

    def __init__(self, *, max_data_age: timedelta = timedelta(minutes=5)) -> None:
        self.max_data_age = max_data_age

    def validate(self, signal: Signal, *, now: datetime | None = None) -> ValidationResult:
        now = now or datetime.now(timezone.utc)
        reasons: list[str] = []

        if signal.data_quality is not DataQuality.VERIFIED:
            reasons.append("data_quality_not_verified")
        if not signal.symbol.strip() or not signal.setup.strip() or not signal.signal_id.strip():
            reasons.append("required_identity_field_missing")
        if not all((signal.context_timeframe, signal.confirmation_timeframe, signal.entry_timeframe)):
            reasons.append("timeframe_missing")
        if signal.source_timestamp.tzinfo is None:
            reasons.append("source_timestamp_not_timezone_aware")
        else:
            age = now - signal.source_timestamp.astimezone(timezone.utc)
            if age > self.max_data_age:
                reasons.append("source_data_stale")
            if age < timedelta(minutes=-1):
                reasons.append("source_timestamp_in_future")

        if min(signal.entry, signal.stop_loss, signal.tp1, signal.tp2, signal.tp3) <= 0:
            reasons.append("non_positive_price")
        elif signal.direction in (Direction.BUY, Direction.CALL):
            if not signal.stop_loss < signal.entry < signal.tp1 < signal.tp2 < signal.tp3:
                reasons.append("invalid_long_risk_geometry")
        elif signal.direction in (Direction.SELL, Direction.PUT):
            if not signal.stop_loss > signal.entry > signal.tp1 > signal.tp2 > signal.tp3:
                reasons.append("invalid_short_risk_geometry")

        if signal.asset_class is AssetClass.GOLD and signal.direction not in (Direction.BUY, Direction.SELL):
            reasons.append("gold_direction_must_be_buy_or_sell")

        return ValidationResult(accepted=not reasons, reasons=tuple(reasons))
