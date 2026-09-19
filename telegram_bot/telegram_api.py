# ==========================================================
# TELEGRAM API (FOR EVENT ENGINE)
# ==========================================================
# متوافق بالكامل مع python-telegram-bot v22.7 (ASYNC ONLY)
# يعمل مع DailyScheduler و TelegramEngine بدون أي تعديل إضافي
# ==========================================================

import asyncio
import threading
import logging
from telegram import Bot


class TelegramAPI:
    """
    قناة تيليجرام الخاصة بمحرك الأحداث.
    ترسل الرسائل والصور للقناة فقط.
    """

    def __init__(self, token: str, channel_id: str):
        self.bot = Bot(token=token)
        self.channel_id = channel_id

        # ======================================================
        # إنشاء Loop مستقل داخل Thread منفصل (مع ربط صحيح)
        # ======================================================
        self.loop = asyncio.new_event_loop()

        def _run_loop():
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()

        self.thread = threading.Thread(
            target=_run_loop,
            daemon=True
        )
        self.thread.start()

    # ======================================================
    # SEND TEXT MESSAGE (SAFE & SYNC-FRIENDLY)
    # ======================================================
    def send_message(self, text: str, *, destination=None, parse_mode=None) -> bool:
        """
        إرسال رسالة نصية للقناة.
        يعمل مع python-telegram-bot 22.7 بدون مشاكل.
        """

        if not text:
            logging.warning("TelegramAPI Warning: محاولة إرسال نص فارغ.")
            return False

        try:
            future = asyncio.run_coroutine_threadsafe(
                self.bot.send_message(
                    chat_id=destination if destination is not None else self.channel_id,
                    text=text,
                    disable_web_page_preview=True,
                    parse_mode=parse_mode,
                ),
                self.loop
            )

            future.result()
            return True

        except Exception as e:
            logging.error(f"TelegramAPI Error (send_message): {e}")
            return False

    # ======================================================
    # SEND PHOTO WITH CAPTION (SAFE & SYNC-FRIENDLY)
    # ======================================================
    def send_photo_with_caption(self, image_path: str, caption: str, *, destination=None) -> bool:
        """
        إرسال صورة + نص للقناة.
        يعمل مع python-telegram-bot 22.7 بدون مشاكل.
        """

        try:
            with open(image_path, "rb") as photo:
                future = asyncio.run_coroutine_threadsafe(
                    self.bot.send_photo(
                        chat_id=destination if destination is not None else self.channel_id,
                        photo=photo,
                        caption=caption
                    ),
                    self.loop
                )

                future.result()
                return True

        except Exception as e:
            logging.error(f"TelegramAPI Error (send_photo): {e}")
            return False

    # ======================================================
    # OPTIONAL CLEAN SHUTDOWN (مستقبلي)
    # ======================================================
    def shutdown(self) -> None:
        """
        إغلاق الـ loop والـ thread بشكل نظيف (اختياري).
        لا يُستخدم الآن، لكنه مفيد مستقبلًا عند إيقاف النظام.
        """
        try:
            if self.loop.is_running():
                self.loop.call_soon_threadsafe(self.loop.stop)
                self.thread.join(timeout=1)
                logging.info("TelegramAPI loop shutdown completed.")
        except Exception as e:
            logging.error(f"TelegramAPI shutdown error: {e}")
