"""Canonical, asset-agnostic signal contract.

This module deliberately contains no market analysis, delivery, or persistence.
Strategies produce ready-to-validate signals through this contract.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from hashlib import sha256
from typing import Mapping


class AssetClass(StrEnum):
    STOCK = "STOCK"
    OPTIONS = "OPTIONS"
    GOLD = "GOLD"
    NEWS = "NEWS"


class InstrumentType(StrEnum):
    EQUITY = "EQUITY"
    OPTION = "OPTION"
    ETF = "ETF"
    SPOT = "SPOT"
    FUTURE = "FUTURE"


class Direction(StrEnum):
    BUY = "BUY"
    SELL = "SELL"
    CALL = "CALL"
    PUT = "PUT"


class DataQuality(StrEnum):
    VERIFIED = "VERIFIED"
    DEGRADED = "DEGRADED"
    REJECTED = "REJECTED"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def build_signal_id(
    *,
    asset_class: AssetClass,
    instrument_type: InstrumentType,
    symbol: str,
    direction: Direction,
    setup: str,
    signal_timestamp: datetime,
) -> str:
    """Build a stable, asset-separated id suitable for deduplication."""
    canonical = "|".join(
        (
            asset_class.value,
            instrument_type.value,
            symbol.upper().strip(),
            direction.value,
            setup.strip().upper(),
            signal_timestamp.astimezone(timezone.utc).isoformat(timespec="seconds"),
        )
    )
    return f"{asset_class.value}:{sha256(canonical.encode()).hexdigest()[:20]}"


@dataclass(frozen=True, slots=True)
class Signal:
    """A fully prepared signal; downstream engines must not infer its fields."""

    asset_class: AssetClass
    instrument_type: InstrumentType
    symbol: str
    direction: Direction
    context_timeframe: str
    confirmation_timeframe: str
    entry_timeframe: str
    entry: float
    stop_loss: float
    tp1: float
    tp2: float
    tp3: float
    setup: str
    signal_timestamp: datetime
    source_timestamp: datetime
    data_quality: DataQuality
    signal_id: str
    metadata: Mapping[str, object] = field(default_factory=dict)

    @classmethod
    def create(cls, **kwargs: object) -> "Signal":
        """Create a signal and derive its id when the strategy does not supply one."""
        signal_timestamp = kwargs.get("signal_timestamp") or utc_now()
        if not isinstance(signal_timestamp, datetime):
            raise TypeError("signal_timestamp must be a datetime")
        kwargs["signal_timestamp"] = signal_timestamp
        kwargs.setdefault("source_timestamp", signal_timestamp)
        kwargs.setdefault(
            "signal_id",
            build_signal_id(
                asset_class=AssetClass(kwargs["asset_class"]),
                instrument_type=InstrumentType(kwargs["instrument_type"]),
                symbol=str(kwargs["symbol"]),
                direction=Direction(kwargs["direction"]),
                setup=str(kwargs["setup"]),
                signal_timestamp=signal_timestamp,
            ),
        )
        return cls(**kwargs)  # type: ignore[arg-type]
