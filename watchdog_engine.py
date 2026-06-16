# ==================================================
# WATCHDOG ENGINE
# ==================================================

import os
import time


# ==================================================
# STATUS
# ==================================================

WATCHDOG_STATUS = {
    "bot": True,
    "database": True,
    "telegram": True,
    "market": True,
    "polygon": True,
    "alpaca": True,
    "tradier": True
}


# ==================================================
# HEALTH CHECK
# ==================================================

def health_check():

    print()

    if WATCHDOG_STATUS["bot"]:
        print("🟢 BOT STATUS : RUNNING")
    else:
        print("🔴 BOT STATUS : OFFLINE")

    if WATCHDOG_STATUS["database"]:
        print("🟢 DATABASE STATUS : OK")
    else:
        print("🔴 DATABASE STATUS : ERROR")

    if WATCHDOG_STATUS["telegram"]:
        print("🟢 TELEGRAM STATUS : OK")
    else:
        print("🔴 TELEGRAM STATUS : ERROR")

    if WATCHDOG_STATUS["market"]:
        print("🟢 MARKET STATUS : OK")
    else:
        print("🔴 MARKET STATUS : ERROR")

    if WATCHDOG_STATUS["polygon"]:
        print("🟢 POLYGON STATUS : OK")
    else:
        print("🔴 POLYGON STATUS : ERROR")

    if WATCHDOG_STATUS["alpaca"]:
        print("🟢 ALPACA STATUS : OK")
    else:
        print("🔴 ALPACA STATUS : ERROR")

    if WATCHDOG_STATUS["tradier"]:
        print("🟢 TRADIER STATUS : OK")
    else:
        print("🔴 TRADIER STATUS : ERROR")

    print()


# ==================================================
# AUTO RECOVERY
# ==================================================

def auto_recovery():

    if not WATCHDOG_STATUS["bot"]:

        print("🔄 AUTO RECOVERY STARTED")

        os.system(
            "python AdelSmartBot.py"
        )


# ==================================================
# WATCHDOG
# ==================================================

def watchdog():

    print()
    print("👁 WATCHDOG ENGINE ACTIVE")
    print()

    while True:

        health_check()

        auto_recovery()

        time.sleep(60)


        