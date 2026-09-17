# ==================================================
# EVENTS CORE MODULE
# ==================================================
# هذا الملف هو المرجع الموحد لتعريف الأحداث في النظام.
# يحتوي على:
#   1) EventType  → تعريف ثابت لأنواع الأحداث باستخدام Enum
#   2) TradeEvent → كائن الحدث الموحد
#
# سيتم استخدام هذا الملف من قبل:
#   - AutoUpdateEngine
#   - EventRouter
#   - TelegramEngine
#   - WhatsAppEngine (مستقبلاً)
#   - AppEngine (مستقبلاً)
#   - WebDashboardEngine (مستقبلاً)
#
# ملاحظة:
# هذا الملف يجب أن يبقى بسيطًا وخفيفًا، ووظيفته الوحيدة هي تعريف الأحداث.
# ==================================================

from dataclasses import dataclass
from enum import Enum
from typing import Any
import time


# ==================================================
# EVENT TYPES (Enum)
# ==================================================

class EventType(str, Enum):
    """
    جميع أنواع الأحداث المستخدمة داخل النظام.
    يجب إضافة أي نوع حدث جديد هنا فقط.
    """

    TP1 = "TP1"
    TP2 = "TP2"
    TP3 = "TP3"
    STOP_LOSS = "STOP_LOSS"

    PROGRESS_UPDATE = "PROGRESS_UPDATE"
    OPEN_PROFIT = "OPEN_PROFIT"

    MOONSHOT = "MOONSHOT"
    LEGENDARY = "LEGENDARY"
    GOD_MODE = "GOD_MODE"

    RISK = "RISK"
    INDEX = "INDEX"
    DISCLAIMER = "DISCLAIMER"

    # الحدث الجديد المستخدم عند إرسال إشارة جديدة
    NEW_TRADE = "NEW_TRADE"
    TRADE_CLOSED = "TRADE_CLOSED"

    # يمكن إضافة أنواع جديدة مستقبلًا هنا:
    # APP_NOTIFICATION = "APP_NOTIFICATION"
    # DASHBOARD_UPDATE = "DASHBOARD_UPDATE"
    # WHATSAPP_ALERT = "WHATSAPP_ALERT"


# ==================================================
# TRADE EVENT OBJECT
# ==================================================

@dataclass(frozen=True)
class TradeEvent:
    """
    يمثل حدثًا موحدًا يتم إنشاؤه بواسطة AutoUpdateEngine
    ويتم تمريره إلى EventRouter ثم إلى القنوات المختلفة.
    """

    type: EventType              # نوع الحدث (من EventType)
    trade: dict[str, Any]        # حالة الصفقة بعد التحديث
    timestamp: float             # وقت الحدث (time.time())
    metadata: dict[str, Any]     # معلومات إضافية (ربح، مرحلة، سبب، ...)

    @staticmethod
    def create(event_type: EventType, trade: dict[str, Any], metadata: dict[str, Any] | None = None) -> "TradeEvent":
        """
        دالة مساعدة لإنشاء حدث بشكل نظيف وموحد.
        """
        return TradeEvent(
            type=event_type,
            trade=trade,
            timestamp=time.time(),   # ← تم إصلاح السطر المقطوع
            metadata=metadata or {}
        )
