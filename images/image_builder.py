# ==================================================
# IMAGE BUILDER
# ==================================================

from datetime import datetime
from images.image_engine import ImageEngine

# إنشاء المحرك مرة واحدة فقط
image_engine = ImageEngine()


def build_signal_image(trade):
    """
    Build professional contract image.

    Returns:
        image_path (str | None)
    """

    try:
        data = {
            "company_name": trade.get("symbol", ""),
            "symbol": trade.get("symbol", ""),
            "contract_type": trade.get("signal_type", ""),
            "strike": trade.get("strike", ""),
            "contract_symbol": trade.get("contract_symbol", ""),
            "entry_price": trade.get("entry", ""),
            "expiry_date": trade.get("expiry", ""),
            "signal_time": datetime.now().strftime("%I:%M %p EST"),
            "rating": trade.get("contract_rating", ""),
            "score": trade.get("score", ""),
            "confidence": trade.get("confidence", ""),
            "tp1": trade.get("tp1", ""),
            "tp2": trade.get("tp2", ""),
            "tp3": trade.get("tp3", ""),
            "stop_loss": trade.get("sl", ""),
            "trade_type": trade.get("trade_type", ""),
            "status": trade.get("status", "NEW"),
            "profit_percent": trade.get("profit", 0),
            "approval": trade.get("approval", "")
        }

        image_path = image_engine.build_image(
            "contract",
            data
        )

        return image_path

    except Exception as e:
        print(f"IMAGE BUILD ERROR: {e}")
        return None
