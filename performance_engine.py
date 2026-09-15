# ==============================================================================
# PERFORMANCE ENGINE (ELITE V5)
# ADEL SMART BOT ELITE
# ==============================================================================

from datetime import datetime
from collections import Counter
import random


class PerformanceEngine:

    def __init__(self):
        self.reset()

    # ==================================================
    # RESET
    # ==================================================

    def reset(self):
        self.trades = []

    # ==================================================
    # SAVE TRADE
    # ==================================================

    def save_trade(self, trade):
        trade["saved_at"] = datetime.now()
        self.trades.append(trade)

    # ==================================================
    # BASIC METRICS
    # ==================================================

    def total_trades(self):
        return len(self.trades)

    def winning_trades(self):
        return len([t for t in self.trades if t.get("profit", 0) > 0])

    def losing_trades(self):
        return len([t for t in self.trades if t.get("profit", 0) <= 0])

    def win_rate(self):
        total = self.total_trades()
        if total == 0:
            return 0
        return round(self.winning_trades() / total * 100, 2)

    def total_profit(self):
        return round(sum(t.get("profit", 0) for t in self.trades), 2)

    def average_profit(self):
        total = self.total_trades()
        if total == 0:
            return 0
        return round(self.total_profit() / total, 2)

    # ==================================================
    # TRADE QUALITY
    # ==================================================

    def best_trade(self):
        if not self.trades:
            return None
        return max(self.trades, key=lambda x: x.get("profit", 0))

    def worst_trade(self):
        if not self.trades:
            return None
        return min(self.trades, key=lambda x: x.get("profit", 0))

    def moon_shots(self):
        return len([t for t in self.trades if t.get("profit", 0) >= 200])

    def legendary_trades(self):
        return len([t for t in self.trades if t.get("profit", 0) >= 1000])

    def best_symbol(self):
        if not self.trades:
            return None
        symbols = [t.get("symbol", "UNKNOWN") for t in self.trades]
        return Counter(symbols).most_common(1)[0][0]

    # ==================================================
    # RAW REPORTS
    # ==================================================

    def get_daily_report(self):
        return {
            "report": "DAILY",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "total_trades": self.total_trades(),
            "winning_trades": self.winning_trades(),
            "losing_trades": self.losing_trades(),
            "win_rate": self.win_rate(),
            "average_profit": self.average_profit(),
            "total_profit": self.total_profit(),
            "moon_shots": self.moon_shots(),
            "legendary_trades": self.legendary_trades(),
            "best_trade": self.best_trade(),
            "worst_trade": self.worst_trade(),
            "best_symbol": self.best_symbol()
        }

    # ==================================================
    # MESSAGE LIBRARY (PROFESSIONAL)
    # ==================================================

    elite_messages = [
        "🏆 أداء استثنائي اليوم. جميع مؤشرات الأداء كانت ضمن أعلى المستويات مع تنفيذ منضبط وإدارة مخاطر ممتازة.",
        "🚀 يوم احترافي بكل المقاييس، حيث اجتمعت جودة الإشارات مع الانضباط في التنفيذ لتحقيق نتائج قوية.",
        "🌟 حقق النظام أداءً متميزًا اليوم مع استغلال فعال للفرص عالية الجودة.",
        "💎 أظهرت نتائج اليوم قوة المنهجية وفعالية معايير اختيار الصفقات.",
        "👑 يوم من فئة Elite، تميز بنسبة نجاح مرتفعة وجودة تنفيذ تعكس قوة النظام."
    ]

    excellent_messages = [
        "📈 أداء قوي ومستقر اليوم مع تحقيق نتائج إيجابية في معظم الصفقات.",
        "💼 حافظ النظام على جودة جيدة في اختيار الفرص وإدارة المخاطر.",
        "🎯 يوم ناجح يعكس التزام الإستراتيجية بمعايير الدخول والخروج.",
        "📊 الأداء كان إيجابيًا مع استقرار واضح في النتائج.",
        "🔝 جودة التنفيذ كانت جيدة وأسهمت في الحفاظ على أداء متوازن."
    ]

    good_messages = [
        "⚖️ أداء متوازن اليوم، مع وجود فرص جيدة وأخرى تحتاج إلى مراجعة.",
        "📊 النتائج كانت مقبولة، وهناك مجال لتحسين جودة اختيار الصفقات.",
        "🔍 الأداء يعكس استقرارًا نسبيًا مع إمكانية رفع الكفاءة في الجلسات القادمة.",
        "📉 لم يكن اليوم مثاليًا، لكنه حافظ على توازن مقبول في النتائج.",
        "🎯 الانضباط كان جيدًا، إلا أن بعض الصفقات أثرت على الأداء العام."
    ]

    average_messages = [
        "📉 أداء متوسط اليوم، بعض الصفقات كانت جيدة وأخرى أثرت على النتائج.",
        "🔍 يوم متقلب، يمكن تحسين جودة نقاط الدخول لرفع الأداء.",
        "⚖️ نتائج متوازنة، لكنها أقل من المستوى المتوقع.",
        "📊 الأداء كان مقبولًا، مع إمكانية تحسين إدارة المخاطر.",
        "🎯 يوم متوسط، يمكن رفع الجودة في الجلسات القادمة."
    ]

    weak_messages = [
        "⚠️ شهد اليوم أداءً دون المتوقع، ويوصى بمراجعة ظروف السوق قبل زيادة حجم المخاطرة.",
        "📉 النتائج تشير إلى ضرورة تحسين جودة اختيار الصفقات وإدارة المخاطر.",
        "🔻 انخفض الأداء اليوم مقارنة بالمعدل المعتاد، وتستحق الجلسة مراجعة تفصيلية.",
        "⚠️ كانت ظروف السوق أقل ملاءمة، مما انعكس على النتائج النهائية.",
        "📌 يُنصح بتحليل الصفقات الخاسرة لاستخلاص الدروس وتحسين الأداء القادم."
    ]

    no_trades_messages = [
        "ℹ️ لم تُنفذ أي صفقات اليوم، وكان الحفاظ على رأس المال هو القرار الأفضل.",
        "🛡️ لم تظهر فرص تستوفي معايير النظام، لذا لم يتم فتح أي صفقات.",
        "📊 لم يوفر السوق فرصًا عالية الجودة اليوم، وتم الالتزام بالانضباط وعدم التداول.",
        "🎯 عدم الدخول في صفقات غير مناسبة يُعد جزءًا من نجاح الإستراتيجية.",
        "💼 اختيار عدم التداول عند غياب الفرص هو سلوك احترافي يحافظ على رأس المال."
    ]

    motivation_messages = [
        "🎯 الجودة أهم من كثرة الصفقات.",
        "🛡️ حماية رأس المال تأتي قبل تحقيق الأرباح.",
        "📈 الاستمرارية تُبنى على الانضباط وليس على المخاطرة.",
        "⚖️ أفضل المتداولين يخسرون أحيانًا، لكنهم يديرون المخاطر دائمًا.",
        "🚀 الفرصة القادمة دائمًا أهم من مطاردة الفرصة الماضية.",
        "💎 الالتزام بالخطة هو أساس النجاح طويل المدى.",
        "📊 النجاح في التداول هو نتيجة قرارات منضبطة وليست صفقات عشوائية.",
        "🌟 الصبر على الفرص الجيدة جزء من الإستراتيجية الناجحة.",
        "📌 كل جلسة تمنح فرصة للتعلم وتحسين الأداء.",
        "🏆 التداول الاحترافي يعتمد على الجودة والاتساق أكثر من عدد الصفقات."
    ]

    # ==================================================
    # PERFORMANCE CLASSIFICATION (CONFLUENCE)
    # ==================================================

    def classify_performance(self, p):

        if p["total_trades"] == 0:
            return "NO_TRADES"

        if p["win_rate"] >= 90 and p["total_profit"] > 500 and p["legendary_trades"] >= 1:
            return "ELITE"

        if p["win_rate"] >= 80 and p["total_profit"] > 0:
            return "EXCELLENT"

        if p["win_rate"] >= 65 and p["total_profit"] > 0:
            return "GOOD"

        if p["win_rate"] >= 50:
            return "AVERAGE"

        return "WEAK"

    # ==================================================
    # SMART CONCLUSION ENGINE
    # ==================================================

    def generate_conclusion(self, performance):

        level = self.classify_performance(performance)

        if level == "ELITE":
            msg = random.choice(self.elite_messages)
        elif level == "EXCELLENT":
            msg = random.choice(self.excellent_messages)
        elif level == "GOOD":
            msg = random.choice(self.good_messages)
        elif level == "AVERAGE":
            msg = random.choice(self.average_messages)
        elif level == "WEAK":
            msg = random.choice(self.weak_messages)
        else:
            msg = random.choice(self.no_trades_messages)

        quote = random.choice(self.motivation_messages)

        return f"{msg}\n\n{quote}"

    # ==================================================
    # EVENING REPORT (STRUCTURED)
    # ==================================================

    def build_evening_data(self):

        performance = self.get_daily_report()

        conclusion = self.generate_conclusion(performance)

        after_items = []

        return performance, conclusion, after_items

    def build_evening_structured(self):

        performance, conclusion, after_items = self.build_evening_data()

        image_data = {
            "total_trades": performance["total_trades"],
            "winning_trades": performance["winning_trades"],
            "losing_trades": performance["losing_trades"],
            "win_rate": performance["win_rate"],
            "average_profit": performance["average_profit"],
            "total_profit": performance["total_profit"],
            "moon_shots": performance["moon_shots"],
            "legendary_trades": performance["legendary_trades"],
            "best_symbol": performance["best_symbol"],
        }

        text_message = (
            f"🌙 تقرير نهاية اليوم\n\n"
            f"📊 إجمالي الصفقات: {performance['total_trades']}\n"
            f"🏆 نسبة الفوز: {performance['win_rate']}%\n"
            f"💰 إجمالي الربح: {performance['total_profit']}\n"
            f"🚀 صفقات Moonshot: {performance['moon_shots']}\n"
            f"👑 صفقات Legendary: {performance['legendary_trades']}\n"
            f"⭐ أفضل رمز تداول اليوم: {performance['best_symbol']}\n\n"
            f"{conclusion}"
        )

        structured = {
            "template": "performance",
            "image_data": image_data,
            "text": text_message
        }

        return structured, after_items

    # ==================================================
    # ENGINE STATUS
    # ==================================================

    def get_engine_status(self):
        return {
            "engine": "Performance Engine",
            "status": "READY",
            "saved_trades": self.total_trades(),
            "win_rate": self.win_rate(),
            "moon_shots": self.moon_shots(),
            "legendary_trades": self.legendary_trades()
        }


# ==================================================
# TEST
# ==================================================

if __name__ == "__main__":

    engine = PerformanceEngine()

    engine.save_trade({"symbol": "NVDA", "profit": 235})
    engine.save_trade({"symbol": "META", "profit": -20})
    engine.save_trade({"symbol": "AAPL", "profit": 1050})

    print(engine.get_summary())
    print(engine.get_daily_report())
    print(engine.get_engine_status())
    print("🚀 PERFORMANCE ENGINE READY")
