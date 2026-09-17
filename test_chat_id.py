# ============================================
# TEST – استخراج رقم المجموعة (يدعم async)
# ============================================

import asyncio
import os
from telegram import Bot
from config import BOT_TOKEN as CONFIG_BOT_TOKEN

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", CONFIG_BOT_TOKEN)

async def main():
    bot = Bot(token=BOT_TOKEN)

    print("🔄 أرسل رسالة جديدة داخل المجموعة ثم انتظر...")

    updates = await bot.get_updates()

    found = False

    for u in updates:
        if u.message:
            print("\n==============================")
            print("CHAT ID:", u.message.chat.id)
            print("GROUP TITLE:", u.message.chat.title)
            print("==============================\n")
            found = True

    if not found:
        print("❌ لم يتم العثور على أي رسائل.")
        print("➡️ أرسل كلمة (test) داخل المجموعة ثم شغّل الملف مرة أخرى.")

if __name__ == "__main__":
    asyncio.run(main())
