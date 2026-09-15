# ============================================
# TEST – استخراج رقم المجموعة (يدعم async)
# ============================================

import asyncio
from telegram import Bot

BOT_TOKEN = "8603423824:AAGS2MJhU6ilzTuNgGfin00scoRzAQ7aeoo"

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
