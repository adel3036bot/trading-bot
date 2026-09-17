"""Central destination lookup.  It never performs analysis or delivery."""

from __future__ import annotations

from collections.abc import Mapping

from core.signal_schema import AssetClass, Signal


class TelegramRouter:
    def __init__(self, routes: Mapping[AssetClass, int | str]) -> None:
        self._routes = dict(routes)

    def destination_for(self, signal: Signal) -> int | str:
        return self.destination_for_asset_class(signal.asset_class)

    def destination_for_asset_class(self, asset_class: AssetClass) -> int | str:
        try:
            return self._routes[asset_class]
        except KeyError as exc:
            raise LookupError(f"no_telegram_route_for:{asset_class.value}") from exc

    def destination_for_category(self, category: str) -> int | str:
        """Route non-trade payloads without embedding chat IDs in engines."""
        try:
            return self._routes[str(category).upper()]
        except KeyError as exc:
            raise LookupError(f"no_telegram_route_for:{str(category).upper()}") from exc
