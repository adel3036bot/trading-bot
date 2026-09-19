"""One explicit composition root for services that share process state."""

from __future__ import annotations

from dataclasses import dataclass

from auto_update_engine import AutoUpdateEngine
from core.event_router import EventRouter
from core.runtime_health import RuntimeHealth
from core.trade_lifecycle import TradeLifecycle
from database.database import DatabaseManager
from daily_scheduler import DailyScheduler
from market.data_engine import DataEngine
from news.news_engine import NewsEngine
from telegram_bot.telegram_app import TelegramApp
from telegram_bot.telegram_engine import TelegramEngine


@dataclass(slots=True)
class RuntimeServices:
    database: DatabaseManager
    data: DataEngine
    event_router: EventRouter
    lifecycle: TradeLifecycle
    telegram: TelegramEngine
    news: NewsEngine
    scheduler: DailyScheduler
    interface: TelegramApp
    health: RuntimeHealth


def build_runtime_services(*, token: str, channel_url: str, admin_id: int, health: RuntimeHealth) -> RuntimeServices:
    """Compose shared instances once; it does not activate any trading strategy."""
    database = DatabaseManager()
    data = DataEngine()
    event_router = EventRouter()
    telegram = TelegramEngine(journal=database)
    event_router.register_channel(telegram)
    lifecycle = TradeLifecycle(database, router=event_router, updates=AutoUpdateEngine())
    news = NewsEngine(journal=database)
    scheduler = DailyScheduler(telegram=telegram, news_engine=news)
    interface = TelegramApp(token=token, channel_url=channel_url, admin_id=admin_id, db=database)
    return RuntimeServices(database, data, event_router, lifecycle, telegram, news, scheduler, interface, health)
