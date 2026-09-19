# ==================================================
# ADEL SMART BOT
# SCHEDULER TEST
# ==================================================

import builtins
import sys

from daily_scheduler import DailyScheduler


def _safe_print(*args, **kwargs):
    try:
        builtins.print(*args, **kwargs)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or "utf-8"
        text = " ".join(str(value) for value in args)
        builtins.print(text.encode(encoding, "backslashreplace").decode(encoding, "replace"), **kwargs)


print = _safe_print

# ==================================================
# TEST
# ==================================================

def run_scheduler_diagnostic():

    print("\n======================================")
    print("ADEL SMART BOT")
    print("SCHEDULER TEST")
    print("======================================\n")

    scheduler = DailyScheduler()

    try:

        print("✅ Scheduler Loaded")

        print("\n========== SAFE SCHEDULER DIAGNOSTIC ==========\n")
        print(f"NYSE calendar available: {scheduler.session_calendar.available}")
        print("No Telegram, news fetch, image render, or market-data request is performed.")

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
    run_scheduler_diagnostic()

