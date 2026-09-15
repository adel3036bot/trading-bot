# ============================================================
# ADEL SMART BOT
# SCHEDULER + TELEGRAM DIAGNOSTIC TEST
# ============================================================
# هذا الملف للاختبار فقط
# لا يعدّل أي ملف من ملفات المشروع
# لا يرسل تقريرًا حقيقيًا
# يرسل رسالة Telegram اختبارية واحدة فقط
# ============================================================

import daily_scheduler
from datetime import datetime as RealDateTime
from daily_scheduler import DailyScheduler


# ============================================================
# FAKE DATETIME
# ============================================================

class FakeDateTime(RealDateTime):

    current_time = None

    @classmethod
    def now(cls, tz=None):
        return cls.current_time


# ============================================================
# TEST SCHEDULER TIME LOGIC
# ============================================================

def test_scheduler_time_logic():

    print("\n" + "=" * 65)
    print("ADEL SMART BOT - SCHEDULER TIME DIAGNOSTIC TEST")
    print("=" * 65)

    # استبدال datetime داخل daily_scheduler فقط أثناء الاختبار
    original_datetime = daily_scheduler.datetime
    daily_scheduler.datetime = FakeDateTime

    test_times = [
        "2026-09-08 22:59:00",
        "2026-09-08 23:00:00",
        "2026-09-08 23:12:00",
        "2026-09-09 00:29:00",
        "2026-09-09 00:30:00",
    ]

    try:

        scheduler = DailyScheduler()

        # منع أي عمليات حقيقية أثناء اختبار run()
        scheduler.collect_sleep_data = lambda: print(
            "   [TEST] collect_sleep_data()"
        )

        scheduler.send_morning_report = lambda: print(
            "   [TEST] send_morning_report()"
        )

        scheduler.send_full_pre_market_report = lambda: print(
            "   [TEST] send_full_pre_market_report()"
        )

        scheduler.send_morning_news = lambda: print(
            "   [TEST] send_morning_news()"
        )

        scheduler.send_market_open_news = lambda: print(
            "   [TEST] send_market_open_news()"
        )

        scheduler.send_evening_report = lambda: print(
            "   [TEST] send_evening_report()"
        )

        print("\n⏱️ TESTING REAL SCHEDULER LOGIC\n")

        for value in test_times:

            FakeDateTime.current_time = RealDateTime.strptime(
                value,
                "%Y-%m-%d %H:%M:%S"
            )

            print("-" * 65)
            print(f"TEST TIME: {value}")

            result = scheduler.run()

            print(f"RESULT: {result}")

        print("-" * 65)

    finally:

        # إعادة datetime كما كان تمامًا
        daily_scheduler.datetime = original_datetime

    print("\n" + "=" * 65)
    print("✅ SCHEDULER TIME TEST FINISHED")
    print("=" * 65)


# ============================================================
# TELEGRAM REAL SEND TEST
# ============================================================

def test_telegram_send():

    print("\n" + "=" * 65)
    print("ADEL SMART BOT - TELEGRAM REAL SEND TEST")
    print("=" * 65)

    print("\n📤 سيتم الآن إرسال رسالة اختبار واحدة فقط إلى Telegram.\n")

    try:

        scheduler = DailyScheduler()

        test_message = (
            "🧪 ADEL SMART BOT — TELEGRAM TEST\n\n"
            "✅ اختبار الإرسال الحقيقي\n"
            "هذه رسالة تشخيصية فقط.\n"
            "لا يوجد تقرير أو إشارة تداول في هذه الرسالة."
        )

        result = scheduler.telegram.send_message(test_message)

        print(f"Telegram send result: {result}")

        if result:
            print("\n✅ TELEGRAM SEND FUNCTION = SUCCESS")
            print("📱 تحقق الآن من وصول الرسالة إلى Telegram.")
        else:
            print("\n❌ TELEGRAM SEND FUNCTION = FAILURE")

    except Exception as error:

        print("\n❌ TELEGRAM TEST FAILED")
        print(f"ERROR: {error}")

    print("\n" + "=" * 65)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("\n")
    print("🚀 STARTING DIAGNOSTIC TEST")
    print("⚠️ لا يوجد تعديل على ملفات البوت الأصلية.")
    print("⚠️ لا يوجد إرسال لتقرير حقيقي.")
    print("⚠️ سيتم إرسال رسالة Telegram اختبارية واحدة فقط.")

    # 1 — اختبار منطق Scheduler
    test_scheduler_time_logic()

    # 2 — اختبار Telegram الحقيقي
    test_telegram_send()

    print("\n" + "=" * 65)
    print("🎉 ALL DIAGNOSTIC TESTS FINISHED")
    print("=" * 65)
    