# ==================================================
# EVENT ROUTER
# ==================================================
# طبقة توجيه عامة تستقبل الأحداث من AutoUpdateEngine
# وتقوم بتمريرها إلى جميع القنوات المسجّلة.
#
# ملاحظة:
# - لا تفسّر الأحداث.
# - لا تعرف أنواع الأحداث.
# - لا تبني رسائل أو صور.
# - لا ترسل أي شيء بنفسها.
#
# مسؤوليتها الوحيدة:
#     event → لكل قناة مسجلة → channel.handle_event(event)
#
# ==================================================

import logging
from typing import List, Protocol
from core.events import TradeEvent


# ==================================================
# EVENT CHANNEL PROTOCOL
# ==================================================

class EventChannel(Protocol):
    """
    أي قناة تريد استقبال الأحداث يجب أن تطبق هذه الواجهة.
    يجب أن تحتوي القناة على:
        def handle_event(self, event: TradeEvent) -> None
    """

    def handle_event(self, event: TradeEvent) -> None:
        ...


# ==================================================
# EVENT ROUTER
# ==================================================

class EventRouter:
    """
    يقوم بتوجيه الأحداث إلى القنوات المسجّلة.
    """

    def __init__(self):
        # قائمة القنوات المسجّلة
        self.channels: List[EventChannel] = []

    # ==================================================
    # REGISTER CHANNEL
    # ==================================================

    def register_channel(self, channel: EventChannel) -> None:
        """
        تسجيل قناة جديدة لاستقبال الأحداث.
        مثال:
            router.register_channel(TelegramEngine())
        """
        self.channels.append(channel)

    # ==================================================
    # DISPATCH EVENT
    # ==================================================

    def dispatch(self, event: TradeEvent) -> None:
        """
        تمرير الحدث إلى جميع القنوات المسجّلة.
        لا يتم تفسير الحدث هنا.
        """
        for channel in self.channels:
            try:
                channel.handle_event(event)
            except Exception:
                # منع توقف النظام إذا فشلت قناة واحدة
                logging.exception(f"⚠️ حدث خطأ داخل قناة {channel}")
