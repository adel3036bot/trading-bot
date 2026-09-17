"""Persistent orchestration around the existing TradeManager and event flow."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone

from auto_update_engine import AutoUpdateEngine, PriceUpdate, close_trade
from core.event_router import EventRouter
from core.events import EventType, TradeEvent
from database.database import DatabaseManager


class TradeLifecycle:
    """Coordinates persisted state; it never calculates strategy levels or prices."""

    def __init__(self, journal: DatabaseManager, router: EventRouter | None = None, updates: AutoUpdateEngine | None = None):
        self.journal = journal
        self.router = router or EventRouter()
        self.updates = updates or AutoUpdateEngine()

    @staticmethod
    def _event_key(event: TradeEvent) -> str:
        if event.type is EventType.PROGRESS_UPDATE:
            return f"{event.type.value}:stage:{event.trade.get('stage')}"
        if event.type is EventType.OPEN_PROFIT:
            return f"{event.type.value}:profit:{event.trade.get('last_open_profit_update')}"
        return event.type.value

    def _persist_and_dispatch(self, signal_id: str, event: TradeEvent) -> bool:
        timestamp = datetime.fromtimestamp(event.timestamp, timezone.utc).isoformat()
        event_id, inserted = self.journal.record_event_once(
            signal_id,
            event.type.value,
            self._event_key(event),
            event_timestamp=timestamp,
            metadata=event.metadata,
        )
        if not inserted:
            return False
        # TradeEvent is frozen, but its supplied metadata dictionary is mutable.
        event.metadata["journal_event_id"] = event_id
        event.trade.setdefault("signal_id", signal_id)
        self.router.dispatch(event)
        return True

    def start_trade(self, payload: Mapping[str, object]):
        """Create the durable base record before emitting NEW_TRADE."""
        signal_id, inserted = self.journal.record_signal(payload)
        persisted = self.journal.get_trade_state(signal_id)
        trade = dict(persisted or payload)
        trade["signal_id"] = signal_id
        trade.setdefault("stage", 0)
        trade.setdefault("status", "ACTIVE")
        trade.setdefault("is_closed", False)
        # Keep original levels in the immutable signal journal; this state can
        # carry the existing trailing-stop mutations made by TradeManager.
        self.journal.persist_trade_state(signal_id, trade, status="ACTIVE")

        event = TradeEvent.create(EventType.NEW_TRADE, trade, {"journal_inserted": inserted})
        self._persist_and_dispatch(signal_id, event)
        return trade

    def process_price(self, signal_id: str, price_update: PriceUpdate):
        """Apply one verified price update to one persisted active trade."""
        trade = self.journal.get_trade_state(signal_id)
        if trade is None or trade.get("is_closed"):
            return None, []

        updated, events = self.updates.check_trade(trade, price_update)
        # Persist first: delivery failure must never roll back a proven state.
        closed = bool(updated.get("is_closed"))
        self.journal.persist_trade_state(
            signal_id,
            updated,
            price_timestamp=price_update.source_timestamp.isoformat(),
            status="CLOSED" if closed else "ACTIVE",
            closed=closed,
        )
        delivered_events = []
        for event in events:
            if self._persist_and_dispatch(signal_id, event):
                delivered_events.append(event)
        return updated, delivered_events

    def close_trade(self, signal_id: str, *, metadata=None):
        """Explicit close path using the existing close-trade presentation text."""
        trade = self.journal.get_trade_state(signal_id)
        if trade is None or trade.get("is_closed"):
            return None, []
        updated = close_trade(trade)
        self.journal.persist_trade_state(signal_id, updated, status="CLOSED", closed=True)
        event = TradeEvent.create(EventType.TRADE_CLOSED, updated, metadata or {})
        return updated, [event] if self._persist_and_dispatch(signal_id, event) else []

    def recover_active_trades(self):
        """Return persisted open states after a process restart; no replay occurs."""
        return self.journal.get_active_trade_states()
