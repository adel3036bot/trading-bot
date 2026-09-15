# ==================================================
# AUTO UPDATE ENGINE (EVENT-BASED)
# ==================================================

import time
from typing import Any

from trade_manager import update_trade
from core.events import TradeEvent, EventType


class AutoUpdateEngine:
    """
    هذا المحرك مسؤول فقط عن:
        - تحديث الصفقة
        - اكتشاف الأحداث
        - إرجاع قائمة بالأحداث المكتشفة

    لا يرسل رسائل
    لا يبني صور
    لا يعرف أي قناة
    """

    def __init__(self):
        pass

    # ==================================================
    # CHECK TRADE → RETURNS (UPDATED_TRADE, EVENTS)
    # ==================================================

    def check_trade(
        self,
        trade: dict[str, Any],
        current_price: float
    ) -> tuple[dict[str, Any], list[TradeEvent]]:

        events: list[TradeEvent] = []

        old_stage = trade["stage"]

        # تحديث حالة الصفقة
        trade = update_trade(trade, current_price)

        new_stage = trade["stage"]

        # ==================================================
        # لا يوجد تغير بالمرحلة
        # ==================================================
        if new_stage == old_stage:

            # رسالة تقدم الصفقة
            if should_send_progress_message(trade):
                events.append(
                    TradeEvent.create(
                        EventType.PROGRESS_UPDATE,
                        trade,
                        {"profit": trade["profit"], "stage": trade["stage"]}
                    )
                )

            # وضع الربح المفتوح
            if should_send_open_profit_update(trade):
                events.append(
                    TradeEvent.create(
                        EventType.OPEN_PROFIT,
                        trade,
                        {"profit": trade["profit"], "stage": trade["stage"]}
                    )
                )

            # MOONSHOT
            if should_send_moonshot_update(trade):
                events.append(
                    TradeEvent.create(
                        EventType.MOONSHOT,
                        trade,
                        {"profit": trade["profit"]}
                    )
                )

            # LEGENDARY
            if should_send_legendary_update(trade):
                events.append(
                    TradeEvent.create(
                        EventType.LEGENDARY,
                        trade,
                        {"profit": trade["profit"]}
                    )
                )

            # GOD MODE
            if should_send_god_mode_update(trade):
                events.append(
                    TradeEvent.create(
                        EventType.GOD_MODE,
                        trade,
                        {"profit": trade["profit"]}
                    )
                )

            return trade, events

        # ==================================================
        # حدث تغيير في المرحلة → نحدد نوع الحدث الأساسي
        # ==================================================

        # STOP LOSS
        if new_stage == -1:
            events.append(
                TradeEvent.create(
                    EventType.STOP_LOSS,
                    trade,
                    {
                        "profit": trade["profit"],
                        "stage": new_stage
                    }
                )
            )

        # TP1
        elif new_stage == 1:
            events.append(
                TradeEvent.create(
                    EventType.TP1,
                    trade,
                    {
                        "profit": trade["profit"],
                        "stage": new_stage
                    }
                )
            )

        # TP2
        elif new_stage == 2:
            events.append(
                TradeEvent.create(
                    EventType.TP2,
                    trade,
                    {
                        "profit": trade["profit"],
                        "stage": new_stage
                    }
                )
            )

        # TP3
        elif new_stage == 3:
            events.append(
                TradeEvent.create(
                    EventType.TP3,
                    trade,
                    {
                        "profit": trade["profit"],
                        "stage": new_stage
                    }
                )
            )

        # MOONSHOT (مرحلة خاصة)
        elif new_stage == 4:
            events.append(
                TradeEvent.create(
                    EventType.MOONSHOT,
                    trade,
                    {
                        "profit": trade["profit"],
                        "stage": new_stage
                    }
                )
            )

        # LEGENDARY (مرحلة خاصة)
        elif new_stage == 5:
            events.append(
                TradeEvent.create(
                    EventType.LEGENDARY,
                    trade,
                    {
                        "profit": trade["profit"],
                        "stage": new_stage
                    }
                )
            )

        # GOD MODE (مرحلة خاصة)
        elif new_stage == 6:
            events.append(
                TradeEvent.create(
                    EventType.GOD_MODE,
                    trade,
                    {
                        "profit": trade["profit"],
                        "stage": new_stage
                    }
                )
            )

        # ==================================================
        # أحداث إضافية مبنية على الربح (حتى مع تغيير المرحلة)
        # ==================================================

        if should_send_moonshot_update(trade):
            events.append(
                TradeEvent.create(
                    EventType.MOONSHOT,
                    trade,
                    {"profit": trade["profit"]}
                )
            )

        if should_send_legendary_update(trade):
            events.append(
                TradeEvent.create(
                    EventType.LEGENDARY,
                    trade,
                    {"profit": trade["profit"]}
                )
            )

        if should_send_god_mode_update(trade):
            events.append(
                TradeEvent.create(
                    EventType.GOD_MODE,
                    trade,
                    {"profit": trade["profit"]}
                )
            )

        if should_send_open_profit_update(trade):
            events.append(
                TradeEvent.create(
                    EventType.OPEN_PROFIT,
                    trade,
                    {"profit": trade["profit"], "stage": trade["stage"]}
                )
            )

        return trade, events


# ==================================================
# TRADE PROGRESS ENGINE
# ==================================================

def should_send_progress_message(trade):
    profit = trade["profit"]
    stage = trade["stage"]

    if stage == 0:
        return profit >= 20

    if stage >= 1:
        return True

    return False


# ==================================================
# MOON SHOT UPDATE ENGINE
# ==================================================

def should_send_moonshot_update(trade):
    return trade["profit"] >= 200


# ==================================================
# LEGENDARY UPDATE ENGINE
# ==================================================

def should_send_legendary_update(trade):
    return trade["profit"] >= 500


# ==================================================
# GOD MODE ENGINE
# ==================================================

def should_send_god_mode_update(trade):
    return trade["profit"] >= 1000


# ==================================================
# PERIODIC MESSAGE ENGINE
# ==================================================

def should_send_risk_message():
    current_hour = time.localtime().tm_hour
    return current_hour in [10, 14, 18]


def should_send_index_message():
    current_hour = time.localtime().tm_hour
    return current_hour in [16, 20]


def should_send_disclaimer_message():
    current_hour = time.localtime().tm_hour
    return current_hour == 15


# ==================================================
# CLOSE TRADE ENGINE
# ==================================================

def close_trade(trade):
    trade["is_closed"] = True
    return trade


# ==================================================
# OPEN PROFIT UPDATE ENGINE
# ==================================================

OPEN_PROFIT_STEP = 10.0


def should_send_open_profit_update(trade):
    """
    يبدأ OPEN_PROFIT بعد انتهاء جميع المراحل الخاصة،
    ثم يرسل تحديثًا جديدًا كلما زاد الربح
    بمقدار OPEN_PROFIT_STEP عن آخر تحديث.
    """

    # لا يبدأ إلا بعد GOD MODE
    if trade["profit"] < 1000:
        return False

    current_profit = float(trade["profit"])

    last_profit = trade.get("last_open_profit_update")

    # أول تحديث
    if last_profit is None:
        trade["last_open_profit_update"] = current_profit
        return True

    # تحديث جديد كل +10%
    if current_profit >= last_profit + OPEN_PROFIT_STEP:
        trade["last_open_profit_update"] = current_profit
        return True

    return False


# ==================================================
# TEST
# ==================================================

if __name__ == "__main__":
    print("🚀 AUTO UPDATE ENGINE (EVENT-BASED) READY")
