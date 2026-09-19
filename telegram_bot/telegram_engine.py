# ==================================================
# TELEGRAM ENGINE (EVENT-BASED)
# ==================================================
# مسؤول عن:
#   - استقبال الأحداث من EventRouter
#   - تفسير الحدث
#   - توليد الصورة (إذا كان الحدث متعلقًا بالصفقة)
#   - إرسال الرسالة النصية
#   - إرسال الصورة (إن وجدت)
#
# لا يحتوي أي منطق تحليل أو تحديث أو حسابات.
# لا يبني الرسائل بنفسه — الرسائل تأتي من TradeManager.
#
# تمت إضافة:
#   - نظام مرونة (FEATURE_FLAGS) لجعل الصور والنصوص قابلة للتفعيل/الإيقاف
#   - دعم مستقبلي لفلسفة:
#       * شارت السهم
#       * شارت العقد
#       * صورة العقد + النص في رسالة واحدة
#       * صورة التحديث + النص في رسالة واحدة
#       * شارت السهم النهائي + النص
#       * صورة الخبر + النص
#       * صورة التقرير + النص
# ==================================================

import logging
import re
from datetime import datetime, timezone

from core.events import TradeEvent, EventType
from core.signal_schema import AssetClass
from core.telegram_router import TelegramRouter
from database.database import DatabaseManager
from images.image_engine import ImageEngine
from trade_manager import build_message
from telegram_bot.telegram_api import TelegramAPI
from config import BOT_TOKEN, CHAT_ID


# ==================================================
# FEATURE FLAGS
# ==================================================

FEATURE_FLAGS = {
    "send_trade_image": True,
    "send_trade_text": True,
    "send_general_text": True,
    "send_stock_chart_on_new_trade": True,
    "send_option_chart_on_new_trade": True,
    "send_contract_card_on_new_trade": True,
    "send_contract_text_on_new_trade": True,
    "send_final_stock_chart": True,
    "send_news_image": True,
    "send_report_image": True,
}


class TelegramEngine:

    def __init__(self, api=None, images=None, journal=None, router: TelegramRouter | None = None):
        """Create one reusable delivery engine for the process.

        Optional dependencies keep construction testable and let the application
        inject the same engine into the scheduler and signal scanner.
        """
        self.api = api or TelegramAPI(
            token=BOT_TOKEN,
            channel_id=CHAT_ID
        )
        self.images = images or ImageEngine()
        # Persistence is best-effort: a journal failure must never prevent a
        # safe Telegram send.  Tests may inject an isolated database instance.
        self.journal = journal or DatabaseManager()
        self.router = router

    # ==================================================
    # NEW — SEND SIGNAL (NO DUPLICATION)
    # ==================================================

    def send_signal(self, trade: dict, *, extra_text: str | None = None) -> None:
        """
        إرسال إشارة جديدة بصورة + نص باستخدام نفس منطق الأحداث.
        """
        event = TradeEvent.create(
            EventType.NEW_TRADE,
            trade,
            metadata={"extra_text": extra_text} if extra_text else None,
        )
        self._send_trade_event(event)

    # ==================================================
    # HANDLE EVENT
    # ==================================================

    def handle_event(self, event: TradeEvent) -> None:
        event_type = event.type

        if event_type in (
            EventType.NEW_TRADE,
            EventType.TP1,
            EventType.TP2,
            EventType.TP3,
            EventType.STOP_LOSS,
            EventType.MOONSHOT,
            EventType.LEGENDARY,
            EventType.GOD_MODE,
            EventType.PROGRESS_UPDATE,
            EventType.OPEN_PROFIT,
            EventType.TRADE_CLOSED,
        ):
            self._send_trade_event(event)
            return

        if event_type in (
            EventType.RISK,
            EventType.INDEX,
            EventType.DISCLAIMER,
        ):
            self._send_general_message(event)
            return

        logging.warning(f"حدث غير معروف في TelegramEngine: {event_type}")

    # ==================================================
    # SEND TRADE EVENT (IMAGE + TEXT)
    # ==================================================

    def _send_trade_event(self, event: TradeEvent) -> None:
        trade = event.trade
        event_type = event.type

        signal_id, event_id = self._record_journal_event(event)
        destination = self._destination_for(trade)
        if destination is None:
            self._record_delivery(signal_id, event_id, "NO_ROUTE", False, "no_telegram_route_for_asset_class")
            return

        image_path = None
        text = None

        if FEATURE_FLAGS.get("send_trade_image", True):
            try:
                image_path = self.images.generate(event_type, trade)
            except Exception as e:
                logging.error(f"فشل توليد الصورة للحدث {event_type}: {e}")
                image_path = None

        if FEATURE_FLAGS.get("send_trade_text", True):
            try:
                text = build_message(event)
                extra_text = event.metadata.get("extra_text")
                if extra_text:
                    text = f"{text}\n\n{extra_text}" if text else str(extra_text)
            except Exception as e:
                logging.error(f"فشل بناء الرسالة للحدث {event_type}: {e}")
                text = None

        try:
            if image_path and text:
                result = self._send_photo(image_path, text, destination)
                self._record_delivery(signal_id, event_id, "TELEGRAM_PHOTO", result, destination=destination)
            elif image_path and not text:
                result = self._send_photo(image_path, "", destination)
                self._record_delivery(signal_id, event_id, "TELEGRAM_PHOTO", result, destination=destination)
            elif text and not image_path:
                result = self._send_text(text, destination)
                self._record_delivery(signal_id, event_id, "TELEGRAM_TEXT", result, destination=destination)
            else:
                logging.warning(f"لا صورة ولا نص للحدث {event_type}")
                self._record_delivery(signal_id, event_id, "NO_DELIVERY", False, "no_rendered_message_or_image", destination=destination)
        except Exception as error:
            self._record_delivery(signal_id, event_id, "TELEGRAM_EXCEPTION", False, self._safe_failure_reason(error), destination=destination)
            raise

    def _destination_for(self, trade):
        if self.router is None:
            return getattr(self.api, "channel_id", CHAT_ID)
        try:
            return self.router.destination_for_asset_class(AssetClass(str(trade.get("asset_class")).upper()))
        except (LookupError, ValueError, TypeError):
            logging.error("No Telegram route for trade asset class: %s", trade.get("asset_class"))
            return None

    def _send_text(self, text, destination):
        if destination == getattr(self.api, "channel_id", CHAT_ID):
            return self.api.send_message(text)
        return self.api.send_message(text, destination=destination)

    def _send_photo(self, image_path, caption, destination):
        if destination == getattr(self.api, "channel_id", CHAT_ID):
            return self.api.send_photo_with_caption(image_path, caption)
        return self.api.send_photo_with_caption(image_path, caption, destination=destination)

    @staticmethod
    def _safe_failure_reason(error: Exception) -> str:
        """Keep a useful failure reason while redacting token-shaped strings."""
        message = str(error)[:300]
        message = re.sub(r"\b\d{6,}:[A-Za-z0-9_-]+\b", "[REDACTED_TOKEN]", message)
        message = re.sub(r"(?i)(api[_-]?key|token)=\S+", r"\1=[REDACTED]", message)
        return f"{type(error).__name__}:{message}"

    def _record_journal_event(self, event: TradeEvent) -> tuple[str | None, int | None]:
        """Persist identity/event best-effort; no analysis or lifecycle work here."""
        try:
            existing_event_id = event.metadata.get("journal_event_id")
            existing_signal_id = event.trade.get("signal_id")
            if existing_event_id and existing_signal_id:
                return str(existing_signal_id), int(existing_event_id)
            signal_id, _ = self.journal.record_signal(event.trade)
            if isinstance(event.trade, dict):
                event.trade.setdefault("signal_id", signal_id)
            event_time = datetime.fromtimestamp(event.timestamp, timezone.utc).isoformat()
            event_id, _ = self.journal.record_event_once(
                signal_id,
                event.type.value,
                event.type.value,
                event_timestamp=event_time,
                metadata=event.metadata,
            )
            return signal_id, event_id
        except Exception as error:
            logging.error("Signal journal failed for %s: %s", event.type, error)
            return None, None

    def _record_delivery(self, signal_id, event_id, delivery_kind, result, failure_reason=None, destination=None) -> None:
        if not signal_id:
            return
        try:
            success = result is True
            self.journal.record_delivery(
                signal_id,
                destination if destination is not None else getattr(self.api, "channel_id", CHAT_ID),
                event_id=event_id,
                delivery_kind=delivery_kind,
                success=success,
                failure_reason=None if success else (failure_reason or "telegram_api_returned_false"),
            )
        except Exception as error:
            logging.error("Signal delivery journal failed: %s", error)

    # ==================================================
    # SEND GENERAL MESSAGE
    # ==================================================

    def _send_general_message(self, event: TradeEvent) -> None:
        if not FEATURE_FLAGS.get("send_general_text", True):
            return

        try:
            text = build_message(event)
        except Exception as e:
            logging.error(f"فشل بناء الرسالة العامة: {e}")
            return

        self.api.send_message(text)

    # ==================================================
    # FUTURE METHODS (UNCHANGED)
    # ==================================================

    def send_new_trade_bundle(
        self,
        stock_chart_path: str,
        option_chart_path: str,
        contract_image_path: str,
        contract_text: str
    ) -> None:

        if FEATURE_FLAGS.get("send_stock_chart_on_new_trade", True) and stock_chart_path:
            self.api.send_photo_with_caption(stock_chart_path, "")

        if FEATURE_FLAGS.get("send_option_chart_on_new_trade", True) and option_chart_path:
            self.api.send_photo_with_caption(option_chart_path, "")

        if FEATURE_FLAGS.get("send_contract_card_on_new_trade", True) and contract_image_path:
            caption = contract_text if FEATURE_FLAGS.get("send_contract_text_on_new_trade", True) else ""
            self.api.send_photo_with_caption(contract_image_path, caption)

    def send_update_with_image_and_text(self, image_path: str, text: str) -> None:
        if FEATURE_FLAGS.get("send_trade_image", True) and image_path:
            caption = text if FEATURE_FLAGS.get("send_trade_text", True) else ""
            self.api.send_photo_with_caption(image_path, caption)
        elif FEATURE_FLAGS.get("send_trade_text", True) and text:
            self.api.send_message(text)

    def send_final_stock_chart(self, final_chart_path: str, final_text: str) -> None:
        if FEATURE_FLAGS.get("send_final_stock_chart", True) and final_chart_path:
            self.api.send_photo_with_caption(final_chart_path, final_text)
        else:
            if final_text:
                self.api.send_message(final_text)

    def news_destination(self):
        if self.router is not None:
            try:
                return self.router.destination_for_category("NEWS")
            except LookupError:
                logging.error("No explicit Telegram NEWS route; using existing default destination")
        return getattr(self.api, "channel_id", CHAT_ID)

    def send_news_with_image(self, news_image_path: str, news_text: str, *, destination=None) -> bool:
        destination = destination if destination is not None else self.news_destination()
        if FEATURE_FLAGS.get("send_news_image", True) and news_image_path:
            if destination == getattr(self.api, "channel_id", CHAT_ID):
                return bool(self.api.send_photo_with_caption(news_image_path, news_text))
            return bool(self.api.send_photo_with_caption(news_image_path, news_text, destination=destination))
        else:
            if news_text:
                if destination == getattr(self.api, "channel_id", CHAT_ID):
                    return bool(self.api.send_message(news_text, parse_mode="HTML"))
                return bool(self.api.send_message(news_text, destination=destination, parse_mode="HTML"))
        return False

    def send_report_with_image(self, report_image_path: str, report_text: str) -> None:
        if FEATURE_FLAGS.get("send_report_image", True) and report_image_path:
            self.api.send_photo_with_caption(report_image_path, report_text)
        else:
            if report_text:
                self.api.send_message(report_text)

    def send_performance_report(self, report_image_path: str, report_text: str) -> None:
        """
        واجهة واضحة لتقارير الأداء:
        يستقبل صورة جاهزة + نص جاهز من PerformanceEngine/ImageEngine،
        ويرسلها بنفس منطق التقارير.
        """
        self.send_report_with_image(report_image_path, report_text)

    # ==================================================
    # PUBLIC SEND MESSAGE
    # ==================================================

    def send_message(self, text: str, *, destination=None) -> bool:
        if not text:
            logging.warning("محاولة إرسال رسالة فارغة.")
            return False

        try:
            destination = destination if destination is not None else getattr(self.api, "channel_id", CHAT_ID)
            if destination == getattr(self.api, "channel_id", CHAT_ID):
                return bool(self.api.send_message(text))
            return bool(self.api.send_message(text, destination=destination))
        except Exception as e:
            logging.error(f"فشل إرسال رسالة عامة: {e}")
            return False
