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
from core.events import TradeEvent, EventType
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

    def __init__(self):
        self.api = TelegramAPI(
            token=BOT_TOKEN,
            channel_id=CHAT_ID
        )
        self.images = ImageEngine()

    # ==================================================
    # NEW — SEND SIGNAL (NO DUPLICATION)
    # ==================================================

    def send_signal(self, trade: dict) -> None:
        """
        إرسال إشارة جديدة بصورة + نص باستخدام نفس منطق الأحداث.
        """
        event = TradeEvent.create(
            EventType.NEW_TRADE,
            trade
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
            except Exception as e:
                logging.error(f"فشل بناء الرسالة للحدث {event_type}: {e}")
                text = None

        if image_path and text:
            self.api.send_photo_with_caption(image_path, text)
        elif image_path and not text:
            self.api.send_photo_with_caption(image_path, "")
        elif text and not image_path:
            self.api.send_message(text)
        else:
            logging.warning(f"لا صورة ولا نص للحدث {event_type}")

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

    def send_news_with_image(self, news_image_path: str, news_text: str) -> None:
        if FEATURE_FLAGS.get("send_news_image", True) and news_image_path:
            self.api.send_photo_with_caption(news_image_path, news_text)
        else:
            if news_text:
                self.api.send_message(news_text)

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

    def send_message(self, text: str) -> bool:
        if not text:
            logging.warning("محاولة إرسال رسالة فارغة.")
            return False

        try:
            self.api.send_message(text)
            return True
        except Exception as e:
            logging.error(f"فشل إرسال رسالة عامة: {e}")
            return False
