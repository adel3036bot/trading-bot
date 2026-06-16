from telegram_sender import send_telegram_message
import random


# ==================================================
# WISDOM ENGINE
# ==================================================

WISDOM_QUOTES = [

    "💡 الانضباط يهزم الطمع.",

    "💡 دع الأرباح تركض، واقطع الخسائر بسرعة.",

    "💡 السوق يعطي فرصاً جديدة كل يوم.",

    "💡 ليست كل صفقة رابحة، لكن الانضباط دائماً رابح.",

    "💡 لا نرسل إشارة ثم ننساها، بل نرافق المتداول في رحلة الصفقة من البداية حتى النهاية.",

    "💡 الخسارة الصغيرة تحمي من الخسارة الكبيرة.",

    "💡 الصبر جزء من الربح.",

    "💡 حماية رأس المال أهم من مطاردة الأرباح."

]


# ==================================================
# TRADE STORY ENGINE
# ==================================================

TRADE_STORIES = [

    "📖 رحلة الصفقة مستمرة.",

    "📖 تم تحقيق مرحلة جديدة من الصفقة.",

    "📖 الانضباط هو مفتاح الوصول للأهداف.",

    "📖 بعض الصفقات تحتاج إلى الصبر حتى تظهر قوتها.",

    "📖 إدارة الصفقة لا تقل أهمية عن الدخول."

]


class TelegramEngine:

    def __init__(self):

        self.channel_name = "ADEL SMART BOT"

    # ==================================================
    # WISDOM
    # ==================================================

    def get_random_wisdom(self):

        return random.choice(
            WISDOM_QUOTES
        )

    # ==================================================
    # TRADE STORY
    # ==================================================

    def get_trade_story(self):

        return random.choice(
            TRADE_STORIES
        )



# ==================================================
    # NEW SIGNAL
    # ==================================================

    def send_signal(self, signal):

        message = f"""
🚀 إشارة جديدة | ADEL SMART BOT

🏢 الشركة: {signal['symbol']}

📦 العقد:
{signal['symbol']} {signal['strike']} {signal['signal_type']}

⭐ التقييم:
{signal['confidence']} ({signal['score']})

💰 سعر الدخول:
{signal['entry']}$

📅 تاريخ الانتهاء:
{signal['expiry']}

━━━━━━━━━━━━━━

🎯 الهدف الأول: {signal['tp1']}$
🎯 الهدف الثاني: {signal['tp2']}$
🏆 الهدف الثالث: {signal['tp3']}$
🛑 وقف الخسارة: {signal['sl']}$

━━━━━━━━━━━━━━

🕒 وقت الإشارة:
{signal['created_at']}

💡 {self.get_random_wisdom()}
"""

        send_telegram_message(message)

        print(message)


    # ==================================================
    # UPDATE
    # ==================================================

    def send_update(self, trade):

        message = f"""
📊 تحديث الصفقة | ADEL SMART BOT

🏢 الشركة: {trade['symbol']}

💰 السعر الحالي: {trade['current_price']}$
📈 الربح: {trade['profit']}%
⏱ مدة الصفقة: {trade['duration']}

🔄 آخر تحديث:
{trade['last_update']}

📖 {self.get_trade_story()}

💡 {self.get_random_wisdom()}
"""

        send_telegram_message(message)

        print(message)


    # ==================================================
    # TP1
    # ==================================================

    def send_tp1(self, trade):

        message = f"""
🎯 TP1 HIT

📈 الربح: +{trade['profit']}%
⏱ مدة الصفقة: {trade['duration']}

🛡 تم نقل وقف الخسارة إلى نقطة الدخول.

💡 {self.get_random_wisdom()}
"""

        send_telegram_message(message)

        print(message)


    # ==================================================
    # TP2
    # ==================================================

    def send_tp2(self, trade):

        message = f"""
🎯 TP2 HIT

📈 الربح: +{trade['profit']}%
⏱ مدة الصفقة: {trade['duration']}

🛡 تم حماية أرباح الهدف الأول.

💡 {self.get_random_wisdom()}
"""

        send_telegram_message(message)

        print(message)


    # ==================================================
    # TARGET ACHIEVED
    # ==================================================

    def send_tp3(self, trade):

        message = f"""
🏆 TARGET ACHIEVED

📈 الربح: +{trade['profit']}%
⏱ مدة الصفقة: {trade['duration']}

🛡 تم حماية أرباح الهدف الثاني.

💡 {self.get_random_wisdom()}
"""

        send_telegram_message(message)

        print(message)


    # ==================================================
    # STOP LOSS
    # ==================================================

    def send_stop_loss(self, trade):

        message = f"""
🛑 STOP LOSS

📉 الربح: {trade['profit']}%
⏱ مدة الصفقة: {trade['duration']}

💡 {self.get_random_wisdom()}
"""

        send_telegram_message(message)

        print(message)


    # ==================================================
    # MOON SHOT
    # ==================================================

    def send_moon_shot(self, trade):

        message = f"""
🌙 MOON SHOT

💰 السعر الحالي: {trade['current_price']}$
📈 الربح: +{trade['profit']}%
⏱ مدة الصفقة: {trade['duration']}

💡 {self.get_random_wisdom()}
"""

        send_telegram_message(message)

        print(message)


    # ==================================================
    # LEGENDARY TRADE
    # ==================================================

    def send_legendary_trade(self, trade):

        message = f"""
👑 LEGENDARY TRADE

💰 السعر الحالي: {trade['current_price']}$
📈 الربح: +{trade['profit']}%
⏱ مدة الصفقة: {trade['duration']}

📖 {self.get_trade_story()}

💡 {self.get_random_wisdom()}
"""

        send_telegram_message(message)

        print(message)

        # ==================================================
# TP1 MESSAGES
# ==================================================

TP1_MESSAGES = [

    "🛡 تم نقل وقف الخسارة إلى نقطة الدخول.",

    "📈 بداية ممتازة للصفقة.",

    "🎯 الانضباط أهم من الطمع.",

    "💰 حماية رأس المال أولاً."

]


# ==================================================
# TP2 MESSAGES
# ==================================================

TP2_MESSAGES = [

    "🛡 تم تأمين أرباح الهدف الأول.",

    "📖 الصفقة تواصل رحلتها.",

    "🚀 دع الأرباح تركض.",

    "📈 بعض الصفقات تحتاج إلى الصبر."

]


# ==================================================
# TP3 MESSAGES
# ==================================================

TP3_MESSAGES = [

    "🏆 تم تحقيق الهدف الثالث.",

    "🌙 الباب مفتوح لمرحلة MOON SHOT.",

    "📈 بعض الصفقات لا تتوقف عند TP3.",

    "🚀 الرحلة لم تنته بعد."

]


# ==================================================
# STOP LOSS MESSAGES
# ==================================================

STOP_LOSS_MESSAGES = [

    "💡 الخسارة الصغيرة تحمي من الخسارة الكبيرة.",

    "💡 السوق يعطي فرصاً جديدة كل يوم.",

    "💡 ليست كل صفقة رابحة، لكن الانضباط دائماً رابح.",

    "💡 إدارة المخاطر أهم من مطاردة الأرباح."

]


# ==================================================
# MOON SHOT MESSAGES
# ==================================================

MOON_SHOT_MESSAGES = [

    "🌙 الصفقة دخلت مرحلة استثنائية.",

    "🚀 دع الأرباح تركض.",

    "📖 بعض الصفقات تكافئ الصبر.",

    "🏆 رحلة مميزة حتى الآن."

]


# ==================================================
# LEGENDARY TRADE MESSAGES
# ==================================================

LEGENDARY_MESSAGES = [

    "👑 من إشارة عادية إلى صفقة أسطورية.",

    "🏆 الصفقات العظيمة لا تأتي كل يوم.",

    "🚀 الصبر والانضباط يصنعان المعجزات.",

    "📖 رحلة استثنائية تستحق التذكر."

]


