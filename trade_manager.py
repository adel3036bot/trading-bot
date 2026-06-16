# ==================================================
# TRADE MANAGER
# ==================================================

from datetime import datetime
import random


def update_trade(trade, current_price):

    entry = trade["entry"]

    profit = round(
        ((current_price - entry) / entry) * 100,
        2
    )

    trade["profit"] = profit

    trade["current_price"] = round(
        current_price,
        2
    )

    trade["last_update"] = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    
    # ==========================================
    # مدة الصفقة
    # ==========================================
    if "created_at" in trade:

        try:

            start_time = datetime.strptime(
                trade["created_at"],
                "%Y-%m-%d %H:%M:%S"
            )

            duration = datetime.now() - start_time

            trade["duration"] = str(duration).split(".")[0]

        except:

            trade["duration"] = "Unknown"

    # ==========================================
    # STOP LOSS
    # ==========================================
    if current_price <= trade["sl"] and trade["stage"] >= 0:

        trade["stage"] = -1
        trade["status"] = "STOP LOSS"

        return trade

    # ==========================================
    # TP1
    # ==========================================
    if current_price >= trade["tp1"] and trade["stage"] == 0:

        trade["stage"] = 1
        trade["status"] = "TP1 HIT"

        # حماية رأس المال
        trade["sl"] = entry

        return trade

    # ==========================================
    # TP2
    # ==========================================
    if current_price >= trade["tp2"] and trade["stage"] == 1:

        trade["stage"] = 2
        trade["status"] = "TP2 HIT"

        # حماية أرباح TP1
        trade["sl"] = trade["tp1"]

        return trade

    # ==========================================
    # TP3
    # ==========================================
    if current_price >= trade["tp3"] and trade["stage"] == 2:

        trade["stage"] = 3
        trade["status"] = "TARGET ACHIEVED"

        # حماية أرباح TP2
        trade["sl"] = trade["tp2"]

        return trade

    # ==========================================
    # MOON SHOT
    # ==========================================
    if profit >= 200 and trade["stage"] == 3:

        trade["stage"] = 4
        trade["status"] = "MOON SHOT"

        trade["sl"] = trade["tp3"]

        return trade

    # ==========================================
    # LEGENDARY TRADE
    # ==========================================
    if profit >= 1000 and trade["stage"] == 4:

        trade["stage"] = 5
        trade["status"] = "LEGENDARY TRADE"

        return trade

    trade["status"] = "UPDATE"

    return trade


# ==================================================
# TRADE STORY ENGINE
# ==================================================

def get_trade_story(trade):

    stage = trade.get("stage", 0)

    duration = trade.get("duration", "Unknown")

    stories = {

        -1:
        "🛑 انتهت الصفقة عند وقف الخسارة.",

        0:
        "🚀 الصفقة ما زالت في بدايتها.",

        1:
        f"🎯 تم تحقيق الهدف الأول.\n⏳ مدة الصفقة: {duration}",

        2:
        f"🚀 تم تحقيق الهدف الثاني.\n⏳ مدة الصفقة: {duration}",

        3:
        f"🏆 تم تحقيق الهدف الثالث.\n⏳ مدة الصفقة: {duration}",

        4:
        f"🌙 MOON SHOT\n⏳ مدة الرحلة: {duration}",

        5:
        (
            f"👑 LEGENDARY TRADE\n"
            f"⏳ مدة الرحلة: {duration}\n"
            "لا نرسل إشارة ثم ننساها، بل نرافق المتداول في رحلة الصفقة من البداية حتى النهاية."
        )

    }

    return stories.get(stage, "📊 UPDATE")


# ==================================================
# WISDOM ENGINE
# ==================================================

def get_wisdom():

    wisdom_list = [

        "💡 الانضباط يهزم الطمع.",

        "💡 دع الأرباح تركض، واقطع الخسائر بسرعة.",

        "💡 ليست كل فرصة تستحق الدخول.",

        "💡 المحافظة على رأس المال أهم من تحقيق الأرباح.",

        "💡 الأسواق تكافئ المنضبطين.",

        "💡 الصبر جزء من النجاح.",

        "💡 النجاح في التداول رحلة وليس صفقة واحدة.",

        "💡 الجودة أهم من كثرة الصفقات.",

        "💡 الالتزام بالخطة يهزم التردد.",

        "💡 السوق لا يكافئ الطمع."

    ]

    return random.choice(wisdom_list)


# ==================================================
# STOP LOSS WISDOM
# ==================================================

def get_stop_loss_wisdom():

    wisdom_list = [

        "🛡 المحافظة على رأس المال أهم من تحقيق الأرباح.",

        "💡 الخسارة الصغيرة اليوم قد تمنحك فرصة الغد.",

        "💡 وقف الخسارة ليس فشلاً، بل جزء من إدارة المخاطر.",

        "💡 قطع الخسائر بسرعة هو سر البقاء في السوق.",

        "💡 الأسواق مليئة بالفرص."

    ]

    return random.choice(wisdom_list)


# ==================================================
# TARGET WISDOM
# ==================================================

def get_target_wisdom():

    wisdom_list = [

        "🎯 الالتزام بالخطة يهزم التردد.",

        "💡 المحافظة على الأرباح لا تقل أهمية عن تحقيقها.",

        "💡 النجاح يأتي من التراكم وليس من صفقة واحدة.",

        "💡 دع الأرباح تركض، واقطع الخسائر بسرعة."

    ]

    return random.choice(wisdom_list)


# ==================================================
# MOON SHOT WISDOM
# ==================================================

def get_moonshot_wisdom():

    wisdom_list = [

        "🚀 دع الأرباح تركض، واقطع الخسائر بسرعة.",

        "🌙 الصفقات الكبيرة تحتاج إلى الصبر.",

        "🏆 الانضباط يصنع الفرص الاستثنائية."

    ]

    return random.choice(wisdom_list)


# ==================================================
# LEGENDARY TRADE WISDOM
# ==================================================

def get_legendary_wisdom():

    wisdom_list = [

        "👑 الصفقات الأسطورية لا تأتي كل يوم.",

        "🏆 الصبر والانضباط يصنعان النتائج الاستثنائية.",

        "💎 دع الأرباح تركض، واقطع الخسائر بسرعة.",

        "👑 لا نرسل إشارة ثم ننساها، بل نرافق المتداول في رحلة الصفقة من البداية حتى النهاية."

    ]

    return random.choice(wisdom_list)


