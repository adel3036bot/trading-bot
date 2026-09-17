# ==================================================
# IMAGE BUILDER
# ==================================================

from images.image_engine import ImageEngine
from images.image_contract import normalize_trade_payload

# إنشاء المحرك مرة واحدة فقط
image_engine = ImageEngine()


def build_signal_image(trade):
    """
    Build professional contract image.

    Returns:
        image_path (str | None)
    """

    try:
        # Compatibility entry point: adapt aliases only, never calculate or
        # inject market/trade values that were not supplied by the caller.
        data = normalize_trade_payload(trade)

        image_path = image_engine.build_image(
            "contract",
            data
        )

        return image_path

    except Exception as e:
        print(f"IMAGE BUILD ERROR: {e}")
        return None
