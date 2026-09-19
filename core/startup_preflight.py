"""Safe preflight checks for the ADEL runtime entry point."""

from __future__ import annotations

from dataclasses import dataclass, field
import importlib
import importlib.util
from pathlib import Path

from core.runtime_health import RuntimeHealth, ServiceState
from database.database import DatabaseManager
from market.session_calendar import NyseSessionCalendar


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_IMPORTS = {
    "pandas": "pandas",
    "requests": "requests",
    "telegram": "python-telegram-bot",
    "google.genai": "google-genai",
    "PIL": "Pillow",
    "arabic_reshaper": "arabic-reshaper",
    "bidi": "python-bidi",
    "pandas_market_calendars": "pandas_market_calendars",
}
REQUIRED_CONFIG = ("BOT_TOKEN", "CHAT_ID", "CHANNEL_URL", "ADMIN_ID")


@dataclass(slots=True)
class PreflightReport:
    ok: bool
    fatal: list[str] = field(default_factory=list)
    degraded: list[str] = field(default_factory=list)
    health: RuntimeHealth = field(default_factory=RuntimeHealth)

    def safe_summary(self) -> str:
        lines = ["ADEL startup preflight"]
        lines.extend(f"FATAL: {item}" for item in self.fatal)
        lines.extend(f"DEGRADED: {item}" for item in self.degraded)
        return "\n".join(lines)


def run_preflight() -> PreflightReport:
    """Check local prerequisites only; never make network calls or print secrets."""
    report = PreflightReport(ok=True)
    missing = [package for module, package in REQUIRED_IMPORTS.items() if importlib.util.find_spec(module) is None]
    if missing:
        report.ok = False
        report.fatal.append("missing_runtime_dependencies:" + ",".join(missing))

    try:
        config = importlib.import_module("config")
    except Exception:
        report.ok = False
        report.fatal.append("config_module_unavailable")
        report.health.set("telegram", ServiceState.TELEGRAM_UNAVAILABLE, "config_module_unavailable")
        return report

    missing_config = [name for name in REQUIRED_CONFIG if not str(getattr(config, name, "")).strip()]
    if missing_config:
        report.ok = False
        report.fatal.append("required_config_missing:" + ",".join(missing_config))
        report.health.set("telegram", ServiceState.TELEGRAM_UNAVAILABLE, "required_config_missing")
    else:
        report.health.set("telegram", ServiceState.READY)

    try:
        DatabaseManager().connect().close()
        report.health.set("database", ServiceState.READY)
    except Exception:
        report.ok = False
        report.fatal.append("database_unavailable")

    calendar = NyseSessionCalendar()
    if calendar.available:
        report.health.set("nyse_calendar", ServiceState.READY)
    else:
        report.degraded.append("nyse_calendar_unavailable")
        report.health.set("nyse_calendar", ServiceState.CALENDAR_UNAVAILABLE)

    missing_assets = [str(path.relative_to(PROJECT_ROOT)) for path in (PROJECT_ROOT / "fonts" / "regular.ttf", PROJECT_ROOT / "fonts" / "bold.ttf") if not path.is_file()]
    if missing_assets:
        report.degraded.append("image_assets_missing:" + ",".join(missing_assets))
        report.health.set("images", ServiceState.DEGRADED, "assets_missing")
    else:
        report.health.set("images", ServiceState.READY)

    report.health.set("market_data", ServiceState.WAITING_FOR_DATA_PROVIDER)
    report.health.set("news", ServiceState.WAITING_FOR_NEWS_VERIFICATION)
    return report
