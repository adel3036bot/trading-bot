# ==================================================
# TRADE MANAGER
# ==================================================

from datetime import datetime
import random

from core.events import EventType

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
    if profit >= 500 and trade["stage"] == 4:

        trade["stage"] = 5
        trade["status"] = "LEGENDARY TRADE"

        return trade

    # ==========================================
    # GOD MODE
    # ==========================================
    if profit >= 1000 and trade["stage"] == 5:

        trade["stage"] = 6
        trade["status"] = "GOD MODE"

        return trade

    # ==========================================
    # UPDATE
    # ==========================================
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
        ),

        6:
        (
            f"⚡ GOD MODE\n"
            f"⏳ مدة الرحلة: {duration}\n"
            "إحدى أندر الصفقات التي رصدها ADEL SMART BOT ELITE."
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


# ==================================================
# TRADE MESSAGE ENGINE
# ==================================================


# ==================================================
# TRADE OPEN MESSAGE
# ==================================================

def get_trade_open_message(trade):

    message = (

        "📊 ADEL SMART BOT ELITE\n"
        "👀 عقد مقترح للمراقبة\n"

        f"🏢 الشركة: {trade['symbol']}\n"
        f"📦 العقد: {trade['contract_name']}\n"
        f"⭐ التقييم: {trade['grade']} ({trade['score']}/100)\n"

        f"💰 سعر الدخول: {trade['entry']}$\n"
        f"📅 تاريخ الانتهاء: {trade['expiry']}\n"
        f"⏳ مدة العقد: {trade['contract_duration']}\n"

        f"🎯 الهدف الأول: {trade['tp1']}$ (+30%)\n"
        f"🎯 الهدف الثاني: {trade['tp2']}$ (+60%)\n"
        f"🎯 الهدف الثالث: {trade['tp3']}$ (+100%)\n"
        f"🛑 وقف الخسارة: {trade['sl']}$ (-30%)\n"

        "━━━━━━━━━━━━━━\n"

        "📈 حالة السوق\n"
        f"{trade['market_status']}\n"
        f"{trade['secondary_market_status']}\n"
        f"🕒 وقت الإشارة: {trade['signal_time']}\n"

        "━━━━━━━━━━━━━━\n"

        "🧠 ملاحظات البوت\n"
        "✅ الفرصة اجتازت فلاتر ADEL SMART BOT ELITE\n"

        "📖 سبب الصفقة\n"
        f"• {trade['reason_1']}\n"
        f"• {trade['reason_2']}\n"
        f"• {trade['reason_3']}\n"

        "━━━━━━━━━━━━━━\n"

        "⚠️ قراءة فنية وتحليل خوارزمي لأغراض تعليمية وليست توصية مالية.\n"
        "⚠️ القرار النهائي ومسؤولية التنفيذ تقع على المتداول.\n"

        "💎 لا نرسل عقداً ثم ننساه، بل نرافق المتداول في رحلة الصفقة من البداية حتى النهاية.\n"

        "🤖 ADEL SMART BOT ELITE\n"
        "📈"

    )

    return message


# ==================================================
# TP1 MESSAGE
# ==================================================

def get_tp1_message(trade):

    messages = [

        (
            "🎯 تحقق الهدف الأول\n"
            f"💰 سعر العقد: {trade['current_price']}$\n"
            f"📈 الربح الحالي: +{trade['profit']}%\n"
            "🔒 تم نقل وقف الخسارة إلى نقطة الدخول\n"
            f"{get_target_wisdom()}"
        ),

        (
            "🎯 تحقق الهدف الأول\n"
            f"💰 سعر العقد: {trade['current_price']}$\n"
            f"📈 الربح الحالي: +{trade['profit']}%\n"
            "🛡 تم تأمين رأس المال\n"
            f"{get_target_wisdom()}"
        ),

        (
            "🎯 تحقق الهدف الأول\n"
            f"💰 سعر العقد: {trade['current_price']}$\n"
            f"📈 الربح الحالي: +{trade['profit']}%\n"
            "📈 الصفقة تسير حسب الخطة\n"
            f"{get_target_wisdom()}"
        )

    ]

    return random.choice(messages)


# ==================================================
# TP2 MESSAGE
# ==================================================

def get_tp2_message(trade):

    messages = [

        (
            "🎯 تحقق الهدف الثاني\n"
            f"💰 سعر العقد: {trade['current_price']}$\n"
            f"📈 الربح الحالي: +{trade['profit']}%\n"
            "🔒 تم تأمين جزء كبير من الأرباح\n"
            f"{get_target_wisdom()}"
        ),

        (
            "🎯 تحقق الهدف الثاني\n"
            f"💰 سعر العقد: {trade['current_price']}$\n"
            f"📈 الربح الحالي: +{trade['profit']}%\n"
            "🚀 الصفقة تسير بشكل ممتاز\n"
            f"{get_target_wisdom()}"
        ),

        (
            "🎯 تحقق الهدف الثاني\n"
            f"💰 سعر العقد: {trade['current_price']}$\n"
            f"📈 الربح الحالي: +{trade['profit']}%\n"
            "💎 الأرباح بدأت بالتراكم\n"
            f"{get_target_wisdom()}"
        )

    ]

    return random.choice(messages)


# ==================================================
# TP3 MESSAGE
# ==================================================

def get_tp3_message(trade):

    messages = [

        (
            "🎯 تحقق الهدف الثالث\n"
            f"💰 سعر العقد: {trade['current_price']}$\n"
            f"📈 الربح الحالي: +{trade['profit']}%\n"
            "🌙 الدخول في مرحلة الأرباح المفتوحة\n"
            f"{get_moonshot_wisdom()}"
        ),

        (
            "🎯 تحقق الهدف الثالث\n"
            f"💰 سعر العقد: {trade['current_price']}$\n"
            f"📈 الربح الحالي: +{trade['profit']}%\n"
            "🚀 تم تفعيل وضع MOON SHOT\n"
            f"{get_moonshot_wisdom()}"
        ),

        (
            "🎯 تحقق الهدف الثالث\n"
            f"💰 سعر العقد: {trade['current_price']}$\n"
            f"📈 الربح الحالي: +{trade['profit']}%\n"
            "🏆 الصفقة حققت أهدافها الأساسية\n"
            f"{get_moonshot_wisdom()}"
        )

    ]

    return random.choice(messages)

    # ==================================================
# TRADE UPDATE MESSAGE ENGINE
# ==================================================


# ==================================================
# MOON SHOT MESSAGE
# ==================================================

def get_moonshot_message(trade):

    messages = [

        (
            "🌙 MOON SHOT\n"
            f"💰 سعر العقد: {trade['current_price']}$\n"
            f"📈 الربح الحالي: +{trade['profit']}%\n"
            "🚀 الأرباح ما زالت مفتوحة\n"
            f"{get_moonshot_wisdom()}"
        ),

        (
            "🌙 MOON SHOT\n"
            f"💰 سعر العقد: {trade['current_price']}$\n"
            f"📈 الربح الحالي: +{trade['profit']}%\n"
            "💎 دع الأرباح تركض، واقطع الخسائر بسرعة\n"
            f"{get_moonshot_wisdom()}"
        ),

        (
            "🌙 MOON SHOT\n"
            f"💰 سعر العقد: {trade['current_price']}$\n"
            f"📈 الربح الحالي: +{trade['profit']}%\n"
            "🏆 الصفقات الكبيرة تحتاج إلى الصبر\n"
            f"{get_moonshot_wisdom()}"
        )

    ]

    return random.choice(messages)


# ==================================================
# LEGENDARY TRADE MESSAGE
# ==================================================

def get_legendary_message(trade):

    messages = [

        (
            "👑 LEGENDARY TRADE\n"
            f"💰 سعر العقد: {trade['current_price']}$\n"
            f"📈 الربح الحالي: +{trade['profit']}%\n"
            "🏆 الصفقات الأسطورية لا تأتي كل يوم\n"
            f"{get_legendary_wisdom()}"
        ),

        (
            "👑 LEGENDARY TRADE\n"
            f"💰 سعر العقد: {trade['current_price']}$\n"
            f"📈 الربح الحالي: +{trade['profit']}%\n"
            "💎 دع الأرباح تركض، واقطع الخسائر بسرعة\n"
            f"{get_legendary_wisdom()}"
        ),

        (
            "👑 LEGENDARY TRADE\n"
            f"💰 سعر العقد: {trade['current_price']}$\n"
            f"📈 الربح الحالي: +{trade['profit']}%\n"
            "🚀 واحدة من الصفقات النادرة\n"
            f"{get_legendary_wisdom()}"
        )

    ]

    return random.choice(messages)

# ==================================================
# GOD MODE WISDOM
# ==================================================

def get_god_mode_wisdom():

    wisdom_list = [

        "👑 الصفقات الاستثنائية تبدأ دائماً بالالتزام بالخطة.",

        "⚡ الأرباح الكبيرة لا تأتي بالحظ، بل بالانضباط والصبر.",

        "💎 الوصول إلى GOD MODE ليس هدفاً، بل ثمرة الانضباط وإدارة المخاطر.",

        "🚀 دع الأرباح تعمل لصالحك، ولا تدع العاطفة تقود قراراتك."

    ]

    return random.choice(wisdom_list)

# ==================================================
# GOD MODE MESSAGE
# ==================================================

def get_god_mode_message(trade):

    messages = [

        (
            "⚡ GOD MODE ⚡\n"
            f"💰 سعر العقد: {trade['current_price']}$\n"
            f"📈 الربح الحالي: +{trade['profit']}%\n"
            "👑 إحدى أندر الصفقات التي يرصدها ADEL SMART BOT ELITE.\n"
            f"{get_god_mode_wisdom()}"
        ),

        (
            "🔥 GOD MODE 🔥\n"
            f"💰 سعر العقد: {trade['current_price']}$\n"
            f"📈 الربح الحالي: +{trade['profit']}%\n"
            "💎 الصفقة وصلت إلى مستوى استثنائي في الأداء.\n"
            f"{get_god_mode_wisdom()}"
        ),

        (
            "🌟 GOD MODE 🌟\n"
            f"💰 سعر العقد: {trade['current_price']}$\n"
            f"📈 الربح الحالي: +{trade['profit']}%\n"
            "🚀 رحلة الصفقة تجاوزت جميع المراحل التقليدية.\n"
            f"{get_god_mode_wisdom()}"
        )

    ]

    return random.choice(messages)

# ==================================================
# OPEN PROFIT WISDOM
# ==================================================

def get_open_profit_wisdom():

    wisdom_list = [

        "📈 دع الاتجاه يعمل لصالحك، ولا تتعجل في إغلاق الصفقة.",

        "🛡 الأرباح غير المحمية قد تختفي بسرعة، فاحمِ مركزك.",

        "💎 إدارة الصفقة لا تقل أهمية عن اختيارها.",

        "🚀 المتداول المحترف يعرف متى يصبر، ومتى يؤمن أرباحه."

    ]

    return random.choice(wisdom_list)

    # ==================================================
# OPEN PROFIT MESSAGE
# ==================================================

def get_open_profit_message(trade):

    messages = [

        (
            "📈 OPEN PROFIT\n"
            f"💰 سعر العقد: {trade['current_price']}$\n"
            f"📈 الربح الحالي: +{trade['profit']}%\n"
            "🚀 الصفقة ما زالت تحقق أداءً إيجابياً.\n"
            f"{get_open_profit_wisdom()}"
        ),

        (
            "💰 OPEN PROFIT\n"
            f"💰 سعر العقد: {trade['current_price']}$\n"
            f"📈 الربح الحالي: +{trade['profit']}%\n"
            "📊 الاتجاه ما زال في صالح الصفقة.\n"
            f"{get_open_profit_wisdom()}"
        ),

        (
            "🌟 OPEN PROFIT\n"
            f"💰 سعر العقد: {trade['current_price']}$\n"
            f"📈 الربح الحالي: +{trade['profit']}%\n"
            "👀 راقب الصفقة واستمر في إدارة الأرباح بحكمة.\n"
            f"{get_open_profit_wisdom()}"
        )

    ]

    return random.choice(messages)
    
# ==================================================
# STOP LOSS MESSAGE
# ==================================================

def get_stop_loss_message(trade):

    messages = [

        (
            "🛑 تم تفعيل وقف الخسارة\n"
            f"💰 سعر العقد: {trade['current_price']}$\n"
            f"📉 الخسارة الحالية: {trade['profit']}%\n"
            "🛡 المحافظة على رأس المال أولوية\n"
            f"{get_stop_loss_wisdom()}"
        ),

        (
            "🛑 انتهت الصفقة عند وقف الخسارة\n"
            f"💰 سعر العقد: {trade['current_price']}$\n"
            f"📉 الخسارة الحالية: {trade['profit']}%\n"
            "💡 الأسواق مليئة بالفرص\n"
            f"{get_stop_loss_wisdom()}"
        ),

        (
            "🛑 تم الخروج لحماية رأس المال\n"
            f"💰 سعر العقد: {trade['current_price']}$\n"
            f"📉 الخسارة الحالية: {trade['profit']}%\n"
            "🏆 الانضباط أهم من صفقة واحدة\n"
            f"{get_stop_loss_wisdom()}"
        )

    ]

    return random.choice(messages)


    # ==================================================
# SPECIAL MESSAGE ENGINE
# ==================================================


# ==================================================
# CLOSE TRADE MESSAGE
# ==================================================

def get_close_trade_message(trade):

    messages = [

        (
            "🏁 انتهت رحلة الصفقة\n"
            f"📈 النتيجة النهائية: {trade['profit']}%\n"
            "💎 شكراً لثقتكم بـ ADEL SMART BOT ELITE\n"
            "🏆 لا نرسل عقداً ثم ننساه، بل نرافق المتداول في رحلة الصفقة من البداية حتى النهاية."
        ),

        (
            "📊 تم إغلاق الصفقة\n"
            f"📈 المحصلة النهائية: {trade['profit']}%\n"
            "💡 النجاح في التداول رحلة وليس صفقة واحدة."
        ),

        (
            "🏁 اكتملت رحلة الصفقة\n"
            f"📈 النتيجة النهائية: {trade['profit']}%\n"
            "👑 الأسواق تكافئ المنضبطين."
        )

    ]

    return random.choice(messages)


# ==================================================
# DAILY WISDOM MESSAGE
# ==================================================

def get_daily_wisdom_message():

    messages = [

        get_wisdom(),

        get_wisdom(),

        get_wisdom()

    ]

    return random.choice(messages)


# ==================================================
# RISK MANAGEMENT MESSAGE
# ==================================================

def get_risk_management_message():

    messages = [

        "🛡 لا تخاطر بأكثر من 1%-5% من رأس المال في الصفقة الواحدة.",

        "💡 المحافظة على رأس المال أهم من تحقيق الأرباح.",

        "⚠️ عقود الأوبشن عالية التذبذب وقد تتحرك بعنف خلال دقائق.",

        "🏆 البقاء في السوق أهم من الفوز في صفقة واحدة.",

        "💎 إدارة المخاطر أهم من البحث عن الفرص."

    ]

    return random.choice(messages)


# ==================================================
# INDEX WARNING MESSAGE
# ==================================================

def get_index_warning_message():

    messages = [

        "⚠️ ارتفاع مؤشر VIX قد يعني زيادة التذبذب في السوق.",

        "📉 ضعف SPX و QQQ قد يؤثر على أغلب الأسهم.",

        "🟡 مراقبة الذهب مهمة أثناء فترات الخوف في الأسواق.",

        "🚨 ارتفاع التقلبات يستدعي الحذر وإدارة المخاطر.",

        "📊 حركة المؤشرات العامة تؤثر على جودة الفرص."

    ]

    return random.choice(messages)


    # ==================================================
# TRADE PROGRESS MESSAGE
# ==================================================

def get_trade_progress_message(trade):

    messages = [

        (
            "📈 تحديث الصفقة\n"
            f"💰 سعر العقد: {trade['current_price']}$\n"
            f"📈 الربح الحالي: +{trade['profit']}%\n"
            f"⏳ مدة الصفقة: {trade['duration']}\n"
            f"{get_wisdom()}"
        ),

        (
            "📊 متابعة الصفقة\n"
            f"💰 سعر العقد: {trade['current_price']}$\n"
            f"📈 الربح الحالي: +{trade['profit']}%\n"
            f"⏳ مدة الرحلة: {trade['duration']}\n"
            f"{get_wisdom()}"
        ),

        (
            "🚀 الصفقة ما زالت مستمرة\n"
            f"💰 سعر العقد: {trade['current_price']}$\n"
            f"📈 الربح الحالي: +{trade['profit']}%\n"
            f"⏳ مدة الصفقة: {trade['duration']}\n"
            f"{get_wisdom()}"
        )

    ]

    return random.choice(messages)


    # ==================================================
# PERIODIC MESSAGE ENGINE
# ==================================================


# ==================================================
# RISK MANAGEMENT PERIODIC MESSAGE
# ==================================================

def get_risk_management_periodic_message():

    messages = [

        (
            "⚠️ إدارة المخاطر\n\n"
            "• لا تخاطر بأكثر من 1%-5% من رأس المال.\n\n"
            "• وقف الخسارة المقترح لإدارة المخاطر وليس أمراً إلزامياً.\n\n"
            "• عقود الأوبشن عالية التذبذب وقد تلامس وقف الخسارة ثم تعود للاتجاه المتوقع.\n\n"
            "• القرار النهائي ومسؤولية التنفيذ تقع على المتداول.\n\n"
            "━━━━━━━━━━━━━━\n\n"
            "🏆 ADEL SMART BOT ELITE\n"
            "🤖📈"
        )

    ]

    return random.choice(messages)


# ==================================================
# INDEX CONTRACT PERIODIC MESSAGE
# ==================================================

def get_index_contract_periodic_message():

    messages = [

        (
            "⚠️ تنبيه خاص بعقود المؤشرات\n\n"
            "• عقود SPX و SPY و QQQ تتميز بتذبذب مرتفع وفرص كثيرة، لكنها تحمل مستوى خطورة عالياً.\n\n"
            "• لا تدع الطمع يسرق أرباحك، فالسوق يمنح فرصاً جديدة كل يوم.\n\n"
            "• تحكم بمشاعرك، ولا تحول الصفقة الرابحة إلى صفقة خاسرة بسبب الأمل أو التردد.\n\n"
            "• لا تشعر بالندم إذا خرجت بربح جيد، فالاستمرارية أهم من اصطياد كل نقطة.\n\n"
            "• يفضل جني الأرباح تدريجياً وتأمين الأرباح عند تحقيق الأهداف.\n\n"
            "• إذا شعرت بالتوتر أو فقدت السيطرة على مشاعرك، فمن الأفضل التوقف وعدم مطاردة السوق.\n\n"
            "━━━━━━━━━━━━━━\n\n"
            "👑 تذكر دائماً:\n\n"
            "الهدف ليس الفوز في كل صفقة.\n\n"
            "بل البقاء منضبطاً والاستمرار في السوق على المدى الطويل.\n\n"
            "🏆 الانضباط يهزم الطمع.\n"
            "🤖 ADEL SMART BOT ELITE\n"
            "📈"
        )

    ]

    return random.choice(messages)


# ==================================================
# DISCLAIMER PERIODIC MESSAGE
# ==================================================

def get_disclaimer_message():

    messages = [

        (
            "⚠️ تنبيه مهم\n\n"
            "هذه ليست توصية مالية، بل قراءة فنية وتحليل خوارزمي لأغراض تعليمية وتثقيفية.\n\n"
            "عقود الخيارات عالية المخاطر وقد تؤدي إلى خسارة رأس المال.\n\n"
            "إدارة المخاطر أهم من تحقيق الأرباح.\n\n"
            "القرار الاستثماري مسؤولية المتداول وحده، وصاحب البوت غير مسؤول عن أي خسائر أو نتائج ناتجة عن استخدام الإشارات.\n\n"
            "💎 لا نرسل عقداً ثم ننساه، بل نرافق المتداول في رحلة الصفقة من البداية حتى النهاية."
        )

    ]

    return random.choice(messages)


    # ==================================================
# UNIFIED MESSAGE BUILDER
# ==================================================

def build_message(event):
    """
    نقطة الدخول الموحدة لجميع رسائل النظام.
    """

    et = event.type
    trade = event.trade

    # ==========================
    # Trade Events
    # ==========================

    if et == EventType.TP1:
        return get_tp1_message(trade)

    if et == EventType.TP2:
        return get_tp2_message(trade)

    if et == EventType.TP3:
        return get_tp3_message(trade)

    if et == EventType.STOP_LOSS:
        return get_stop_loss_message(trade)

    if et == EventType.MOONSHOT:
        return get_moonshot_message(trade)

    if et == EventType.LEGENDARY:
        return get_legendary_message(trade)

    if et == EventType.GOD_MODE:
        return get_god_mode_message(trade)

    if et == EventType.PROGRESS_UPDATE:
        return get_trade_progress_message(trade)

    if et == EventType.OPEN_PROFIT:
        return get_open_profit_message(trade)

    # ==========================
    # General Messages
    # ==========================

    if et == EventType.RISK:
        return get_risk_management_periodic_message()

    if et == EventType.INDEX:
        return get_index_contract_periodic_message()

    if et == EventType.DISCLAIMER:
        return get_disclaimer_message()

    return "📌 رسالة غير معروفة"


