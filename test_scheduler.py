# ==================================================
# ADEL SMART BOT
# SCHEDULER TEST
# ==================================================

from daily_scheduler import DailyScheduler

# ==================================================
# TEST
# ==================================================

def run_scheduler_test():

    print("\n======================================")
    print("ADEL SMART BOT")
    print("SCHEDULER TEST")
    print("======================================\n")

    scheduler = DailyScheduler()

    try:

        print("✅ Scheduler Loaded")

        print("\n========== PRE MARKET ==========\n")

        scheduler.send_morning_analysis()

        scheduler.send_morning_news()

        print("✅ PRE MARKET PASS")

        print("\n========== AFTER MARKET ==========\n")

        scheduler.send_evening_report()

        print("✅ AFTER MARKET PASS")

        print("\n======================================")
        print("🎉 SCHEDULER READY")
        print("======================================")

    except Exception as error:

        print("\n======================================")
        print("❌ SCHEDULER FAILED")
        print("======================================")
        print(error)


# ==================================================
# TEST
# ==================================================

if __name__ == "__main__":

    run_scheduler_test()

    