from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont


class ImageEngine:

    def __init__(self):
        self.watermark = "ADEL SMART BOT"

# ==================================================
    # SIGNAL IMAGE
    # ==================================================

    def create_signal_image(self, signal):

        img = Image.new(
            "RGB",
            (1600, 900),
            (10, 15, 30)
        )

        draw = ImageDraw.Draw(
            img
        )

        font = ImageFont.load_default()

        draw.text(
            (620, 40),
            "ADEL SMART BOT",
            fill=(0, 180, 255),
            font=font
        )

        draw.text(
            (100, 120),
            f"COMPANY : {signal['symbol']}",
            fill=(255, 255, 255),
            font=font
        )

        draw.text(
            (100, 180),
            f"CONTRACT : {signal['contract']}",
            fill=(255, 255, 255),
            font=font
        )

        draw.text(
            (100, 240),
            f"SCORE : {signal['score']}",
            fill=(255, 215, 0),
            font=font
        )

        draw.text(
            (100, 300),
            f"TYPE : {signal['grade']}",
            fill=(0, 180, 255),
            font=font
        )

        draw.text(
            (100, 360),
            f"ENTRY : {signal['entry']}",
            fill=(255, 255, 255),
            font=font
        )

        draw.text(
            (100, 420),
            f"EXPIRY : {signal['expiry']}",
            fill=(255, 255, 255),
            font=font
        )

        draw.text(
            (100, 520),
            f"TP1 : {signal['tp1']}",
            fill=(0, 180, 255),
            font=font
        )

        draw.text(
            (100, 580),
            f"TP2 : {signal['tp2']}",
            fill=(255, 215, 0),
            font=font
        )

        draw.text(
            (100, 640),
            f"TP3 : {signal['tp3']}",
            fill=(0, 255, 0),
            font=font
        )

        draw.text(
            (100, 740),
            f"STOP LOSS : {signal['sl']}",
            fill=(255, 0, 0),
            font=font
        )

        draw.text(
            (580, 830),
            self.watermark,
            fill=(40, 40, 40),
            font=font
        )

        img.save(
            "signal_image.png"
        )

        print(
            "Signal Image Created"
        )

        return True

        # ==================================================
    # UPDATE IMAGE
    # ==================================================

    def create_update_image(self, signal):

        return True

        # ==================================================
    # TP1 IMAGE
    # ==================================================

    def create_tp1_image(self, trade):

        return True

        # ==================================================
    # TP2 IMAGE
    # ==================================================

    def create_tp2_image(self, trade):

        return True

        # ==================================================
    # TP3 IMAGE
    # ==================================================

    def create_tp3_image(self, trade):

        return True

        # ==================================================
    # STOP LOSS IMAGE
    # ==================================================

    def create_stop_loss_image(self, trade):

        return True


        # ==================================================
    # MOON SHOT IMAGE
    # ==================================================

    def create_moon_shot_image(self, trade):

        return True


        # ==================================================
    # LEGENDARY TRADE IMAGE
    # ==================================================

    def create_legendary_trade_image(self, trade):

        return True


# ==================================================
# TEST
# ==================================================

if __name__ == "__main__":

    image_engine = ImageEngine()

    test_signal = {

        "symbol": "NVDA",

        "contract": "NVDA 180 CALL",

        "score": "A+ (96/100)",

        "grade": "ELITE",

        "entry": "5.49$",

        "expiry": "2026-06-06",

        "tp1": "7.14$",

        "tp2": "8.78$",

        "tp3": "10.98$",

        "sl": "3.84$"

    }

    image_engine.create_signal_image(
        test_signal
    )


    
    