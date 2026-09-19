"""NYSE session facts for scheduling; no provider or strategy logic lives here."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

try:
    import pandas_market_calendars as mcal
except ImportError:  # Fail closed when a deployment has not installed it yet.
    mcal = None


NEW_YORK = ZoneInfo("America/New_York")
RIYADH = ZoneInfo("Asia/Riyadh")


@dataclass(frozen=True)
class NyseSession:
    trading_day: object
    market_open_ny: datetime
    market_close_ny: datetime
    market_open_ksa: datetime
    market_close_ksa: datetime
    is_early_close: bool


class NyseSessionCalendar:
    """Resolve NYSE sessions from the installed exchange calendar.

    A missing calendar intentionally returns no session. Scheduler callers
    therefore do not mistake a server-local weekday for a tradable day.
    """

    def __init__(self, calendar=None):
        if calendar is not None:
            self._calendar = calendar
        elif mcal is not None:
            self._calendar = mcal.get_calendar("NYSE")
        else:
            self._calendar = None
        self._cache: dict[object, NyseSession | None] = {}

    @property
    def available(self) -> bool:
        return self._calendar is not None

    @staticmethod
    def _as_riyadh(now: datetime | None) -> datetime:
        value = now or datetime.now(RIYADH)
        if value.tzinfo is None:
            return value.replace(tzinfo=RIYADH)
        return value.astimezone(RIYADH)

    def session_for(self, now: datetime | None = None) -> NyseSession | None:
        if self._calendar is None:
            return None

        now_ksa = self._as_riyadh(now)
        ny_date = now_ksa.astimezone(NEW_YORK).date()
        if ny_date in self._cache:
            return self._cache[ny_date]

        schedule = self._calendar.schedule(start_date=ny_date, end_date=ny_date)
        if schedule.empty:
            self._cache[ny_date] = None
            return None

        row = schedule.iloc[0]
        market_open = row["market_open"].to_pydatetime().astimezone(NEW_YORK)
        market_close = row["market_close"].to_pydatetime().astimezone(NEW_YORK)
        session = NyseSession(
            trading_day=ny_date,
            market_open_ny=market_open,
            market_close_ny=market_close,
            market_open_ksa=market_open.astimezone(RIYADH),
            market_close_ksa=market_close.astimezone(RIYADH),
            is_early_close=market_close.timetz().replace(tzinfo=None) < time(16, 0),
        )
        self._cache[ny_date] = session
        return session

    def phase_at(self, now: datetime | None = None) -> str:
        now_ksa = self._as_riyadh(now)
        session = self.session_for(now_ksa)
        if session is None:
            return "CLOSED"
        if session.market_open_ksa <= now_ksa < session.market_close_ksa:
            return "MARKET_OPEN"
        if session.market_close_ksa <= now_ksa < session.market_close_ksa + timedelta(minutes=90):
            return "AFTER_MARKET"
        if session.market_open_ksa - timedelta(hours=1) <= now_ksa < session.market_open_ksa:
            return "PRE_MARKET"
        if session.market_open_ksa - timedelta(hours=2) <= now_ksa < session.market_open_ksa - timedelta(hours=1):
            return "PREPARATION"
        return "SLEEP"
