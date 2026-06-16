# ==================================================
# AUTO UPDATE ENGINE
# ==================================================

import time

from trade_manager import update_trade
from telegram_bot.telegram_engine import TelegramEngine


class AutoUpdateEngine:

    def __init__(self):

        self.telegram = TelegramEngine()

    # ==========================================
    # CHECK TRADE
    # ==========================================

    def check_trade(self, trade, current_price):

        old_stage = trade["stage"]

        trade = update_trade(
            trade,
            current_price
        )

        new_stage = trade["stage"]

        if new_stage == old_stage:

            self.telegram.send_update(
                trade
            )

            return trade

        # STOP LOSS
        if new_stage == -1:

            self.telegram.send_stop_loss(
                trade
            )

        # TP1
        elif new_stage == 1:

            self.telegram.send_tp1(
                trade
            )

        # TP2
        elif new_stage == 2:

            self.telegram.send_tp2(
                trade
            )

        # TP3
        elif new_stage == 3:

            self.telegram.send_tp3(
                trade
            )

        # MOON SHOT
        elif new_stage == 4:

            self.telegram.send_moon_shot(
                trade
            )

        # LEGENDARY TRADE
        elif new_stage == 5:

            self.telegram.send_legendary_trade(
                trade
            )

        return trade


# ==================================================
# TEST
# ==================================================

if __name__ == "__main__":

    print("🚀 AUTO UPDATE ENGINE READY")

    