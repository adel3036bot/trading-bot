"""Compatibility adapter for presentation-ready trade image data.

It normalizes names only.  It never calculates an entry, stop, target, score,
direction, or any other trading decision.
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Mapping

from core.events import EventType


class ImagePayloadError(ValueError):
    """Raised when an event image lacks data required for safe rendering."""


def _as_mapping(value: Mapping[str, Any] | object) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    if is_dataclass(value):
        return asdict(value)
    raise TypeError("image payload must be a mapping or dataclass")


def _first_present(data: Mapping[str, Any], *names: str) -> Any:
    for name in names:
        if name in data and data[name] is not None:
            return data[name]
    return None


def _target_values(data: Mapping[str, Any]) -> tuple[Any, Any, Any]:
    direct = (
        _first_present(data, "tp1", "TP1", "target1"),
        _first_present(data, "tp2", "TP2", "target2"),
        _first_present(data, "tp3", "TP3", "target3"),
    )
    targets = data.get("targets")
    if isinstance(targets, Mapping):
        return tuple(
            value if value is not None else _first_present(targets, *names)
            for value, names in zip(direct, (("tp1", "TP1", "target1"), ("tp2", "TP2", "target2"), ("tp3", "TP3", "target3")))
        )
    if isinstance(targets, (list, tuple)):
        values = list(targets) + [None, None, None]
        return tuple(value if value is not None else values[index] for index, value in enumerate(direct))
    return direct


def normalize_trade_payload(payload: Mapping[str, Any] | object) -> dict[str, Any]:
    """Map legacy aliases to image names without manufacturing missing values."""
    data = _as_mapping(payload)
    tp1, tp2, tp3 = _target_values(data)
    data.update(
        {
            "entry_price": _first_present(data, "entry_price", "entry"),
            "stop_loss": _first_present(data, "stop_loss", "sl", "stop"),
            "tp1": tp1,
            "tp2": tp2,
            "tp3": tp3,
            "expiry_date": _first_present(data, "expiry_date", "expiry"),
            "contract_type": _first_present(data, "contract_type", "signal_type", "direction"),
            "rating": _first_present(data, "rating", "contract_rating"),
            "signal_time": _first_present(data, "signal_time", "signal_timestamp", "created_at"),
            "profit": _first_present(data, "profit", "profit_percent"),
            "company_name": _first_present(data, "company_name", "symbol"),
        }
    )
    return data


def coerce_event_type(event_type: EventType | str) -> EventType:
    if isinstance(event_type, EventType):
        return event_type
    try:
        return EventType(event_type)
    except ValueError as error:
        raise ImagePayloadError(f"unsupported_event_type:{event_type}") from error


def validate_event_payload(event_type: EventType, data: Mapping[str, Any]) -> None:
    """Reject incomplete trade images instead of silently drawing invented data."""
    common = ("symbol",)
    requirements = {
        EventType.NEW_TRADE: common + ("entry_price", "stop_loss", "tp1", "tp2", "tp3"),
        EventType.TP1: common + ("entry_price", "current_price"),
        EventType.TP2: common + ("entry_price", "current_price"),
        EventType.TP3: common + ("entry_price", "current_price"),
        EventType.STOP_LOSS: common + ("entry_price", "current_price", "stop_loss"),
        EventType.OPEN_PROFIT: common + ("current_price",),
        EventType.MOONSHOT: common + ("entry_price",),
        EventType.LEGENDARY: common + ("entry_price", "current_price"),
        EventType.GOD_MODE: common + ("entry_price", "current_price"),
    }
    missing = [field for field in requirements.get(event_type, common) if data.get(field) is None]
    if missing:
        raise ImagePayloadError(f"incomplete_image_payload:{','.join(missing)}")
