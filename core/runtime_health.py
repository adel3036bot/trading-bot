"""Small, non-user-facing runtime health registry."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ServiceState(StrEnum):
    READY = "READY"
    WAITING_FOR_DATA_PROVIDER = "WAITING_FOR_DATA_PROVIDER"
    WAITING_FOR_NEWS_VERIFICATION = "WAITING_FOR_NEWS_VERIFICATION"
    CALENDAR_UNAVAILABLE = "CALENDAR_UNAVAILABLE"
    TELEGRAM_UNAVAILABLE = "TELEGRAM_UNAVAILABLE"
    DEGRADED = "DEGRADED"


@dataclass(frozen=True, slots=True)
class ServiceHealth:
    name: str
    state: ServiceState
    reason: str = ""


class RuntimeHealth:
    """Records operational facts without exposing credentials or user data."""

    def __init__(self) -> None:
        self._services: dict[str, ServiceHealth] = {}

    def set(self, name: str, state: ServiceState, reason: str = "") -> None:
        self._services[name] = ServiceHealth(name, state, reason)

    def get(self, name: str) -> ServiceHealth | None:
        return self._services.get(name)

    def snapshot(self) -> dict[str, str]:
        return {name: health.state.value for name, health in self._services.items()}
