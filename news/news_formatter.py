# ==================================================
# IMPORTS
# ==================================================

from datetime import datetime, timedelta, timezone
from html import unescape
import re


# ==================================================
# NEWS FORMATTER
# ==================================================

class NewsFormatter:

    def __init__(self):

        # ==================
        # BOT IDENTITY
        # ==================

        self.bot_name = "🤖 ADEL SMART BOT"
        self.bot_slogan = "حلّل بذكاء... وتداول بثقة"
        self.bot_url = "https://t.me/Adel_smart_ai_bot"

        # ==================
        # TIME SETTINGS
        # ==================

        self.saudi_timezone = timezone(timedelta(hours=3))
        self.newyork_timezone = timezone(timedelta(hours=-4))
        self.time_format = "%d-%m-%Y %I:%M %p"

        # ==================
        # FORMAT SETTINGS
        # ==================

        self.max_summary_length = 220
        self.separator = "━━━━━━━━━━━━━━━━━━"
        self.bullet = "•"

        # ==================
        # REPORT TITLES
        # ==================

        self.pre_market_title = "🌅 التقرير الصباحي"
        self.after_market_title = "🌙 التقرير المسائي"
        self.breaking_title = "🚨 خبر عاجل"

        # ==================
        # SECTION TITLES
        # ==================

        self.news_section = "📰 أهم الأخبار"
        self.company_section = "🏢 أهم أخبار الشركات"
        self.market_events = "📅 أهم أحداث اليوم"
        self.tomorrow_events = "📅 أهم أحداث الغد"
        self.watchlist_section = "👀 الأسهم تحت المراقبة"
        self.result_section = "📊 النتيجة"
        self.assets_section = "🎯 الأصول المتأثرة"
        self.source_section = "🔵 المصدر"

        # ==================
        # PRIORITY ICONS
        # ==================

        self.priority_icons = {
            "CRITICAL": "🚨",
            "HIGH": "🔴",
            "MEDIUM": "🟡",
            "LOW": "🟢"
        }

        # ==================
        # CATEGORY ICONS
        # ==================

        self.category_icons = {
            "COMPANY": "🏢",
            "MACRO": "🌍",
            "FED": "🏛",
            "ECONOMIC": "📊",
            "GEOPOLITICAL": "🌐"
        }

    # ==================================================
    # TEXT CLEANER ENGINE
    # ==================================================

    def clean_text(self, text):
        if not text:
            return ""
        text = unescape(str(text))
        text = re.sub(r"<.*?>", "", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    # ==================================================
    # SUMMARY ENGINE
    # ==================================================

    def shorten_summary(self, summary):
        summary = self.clean_text(summary)
        if len(summary) <= self.max_summary_length:
            return summary
        summary = summary[:self.max_summary_length]
        last_space = summary.rfind(" ")
        if last_space > 0:
            summary = summary[:last_space]
        return summary + "..."

    # ==================================================
    # DATE FORMAT ENGINE
    # ==================================================

    def format_datetime(self, news):
        published = news.get("published", "")
        if not published:
            return "-"
        try:
            dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
            saudi_time = dt.astimezone(self.saudi_timezone)
            return saudi_time.strftime(self.time_format)
        except Exception:
            return published

    # ==================================================
    # ARABIC DAY NAME ENGINE
    # ==================================================

    def arabic_day(self, english_day):
        days = {
            "Monday": "الإثنين",
            "Tuesday": "الثلاثاء",
            "Wednesday": "الأربعاء",
            "Thursday": "الخميس",
            "Friday": "الجمعة",
            "Saturday": "السبت",
            "Sunday": "الأحد"
        }
        return days.get(english_day, english_day)

    # ==================================================
    # BOT SIGNATURE ENGINE
    # ==================================================

    def build_bot_signature(self):
        return (
            f'<a href="{self.bot_url}">{self.bot_name}</a>\n'
            f"{self.bot_slogan}"
        )

    # ==================================================
    # NEWS HEADER ENGINE
    # ==================================================

    def build_news_header(self, news, news_analysis):
        priority = news_analysis.get("priority", "LOW").upper()
        icon = self.priority_icons.get(priority, "🟢")
        return f"{icon} {self.breaking_title}"

    # ==================================================
    # NEWS TITLE ENGINE
    # ==================================================

    def build_news_title(self, news):
        company = self.clean_text(news.get("company", ""))
        source = self.clean_text(news.get("source", ""))
        title = self.clean_text(news.get("title", ""))

        if company:
            return f"🏢 {company}"

        source_map = {
            "Federal Reserve": "🏛 الاحتياطي الفيدرالي",
            "FED": "🏛 الاحتياطي الفيدرالي",
            "SEC": "🏛 هيئة الأوراق المالية الأمريكية",
            "Business Wire": "🏢 Business Wire",
            "PR Newswire": "🏢 PR Newswire",
            "GlobeNewswire": "🏢 GlobeNewswire",
            "BLS": "📊 مكتب إحصاءات العمل الأمريكي"
        }

        if source in source_map:
            return source_map[source]

        return f"📰 {title}"

    # ==================================================
    # NEWS BODY ENGINE
    # ==================================================

    def build_news_body(self, news, news_analysis):
        sections = []

        translated = self.clean_text(news.get("translated", ""))
        if not translated:
            translated = self.shorten_summary(news.get("summary", ""))

        if translated:
            sections.append(translated)

        market_effect = news_analysis.get("market_effect", [])
        if market_effect:
            sections.append("")
            sections.append(self.result_section)
            for item in market_effect:
                sections.append(f"{self.bullet} {item}")

        affected_assets = news_analysis.get("affected_assets", [])
        if affected_assets:
            sections.append("")
            sections.append(self.assets_section)
            sections.append(" • ".join(affected_assets))

        return "\n".join(sections)

    # ==================================================
    # SOURCE ENGINE
    # ==================================================

    def build_news_source(self, news):
        source = self.clean_text(news.get("source", "Unknown"))
        url = news.get("url", "").strip()

        if url:
            return f'🔵 <a href="{url}">{source}</a>'
        return f"🔵 {source}"

    # ==================================================
    # TELEGRAM MESSAGE ENGINE
    # ==================================================

    def format_news_message(self, news, news_analysis):
        return "\n\n".join([
            self.build_news_header(news, news_analysis),
            self.build_news_title(news),
            self.build_news_body(news, news_analysis),
            self.build_news_source(news),
            self.build_bot_signature()
        ])

    # ==================================================
    # BREAKING NEWS ENGINE
    # ==================================================

    def build_breaking_news_message(self, news, news_analysis):
        return self.format_news_message(news, news_analysis)

    # ==================================================
    # REPORT HEADER ENGINE
    # ==================================================

    def build_pre_market_header(self):
        saudi_now = datetime.now(self.saudi_timezone)
        newyork_now = datetime.now(self.newyork_timezone)

        day_ar = self.arabic_day(saudi_now.strftime('%A'))

        return (
            f"{self.pre_market_title}\n\n"
            f"📅 {day_ar} | {saudi_now.strftime('%d-%m-%Y')}\n"
            f"🇸🇦 {saudi_now.strftime('%I:%M %p')}\n"
            f"🇺🇸 {newyork_now.strftime('%I:%M %p')}\n\n"
            f"{self.separator}"
        )

    def build_after_market_header(self):
        saudi_now = datetime.now(self.saudi_timezone)
        newyork_now = datetime.now(self.newyork_timezone)

        day_ar = self.arabic_day(saudi_now.strftime('%A'))

        return (
            f"{self.after_market_title}\n\n"
            f"📅 {day_ar} | {saudi_now.strftime('%d-%m-%Y')}\n"
            f"🇸🇦 {saudi_now.strftime('%I:%M %p')}\n"
            f"🇺🇸 {newyork_now.strftime('%I:%M %p')}\n\n"
            f"{self.separator}"
        )


    # ==================================================
    # ECONOMIC TEMPLATE ENGINE
    # ==================================================

    def build_economic_event_template(self, events):
        if not events:
            return ""

        lines = ["📅 أهم الأحداث الاقتصادية اليوم", ""]

        for event in events:
            country = event.get("country", "🇺🇸 الولايات المتحدة")
            name = event.get("name", "")
            previous = event.get("previous", "-")
            expected = event.get("expected", "-")
            actual = event.get("actual", "-")

            # الوقت كما يأتي من NewsProvider
            raw_time = event.get("time", "")
            time_str = raw_time

            lines.append(f"{country}")
            lines.append(f"🕘 {time_str}")
            lines.append(f"🏛️ {name}")
            lines.append("")
            lines.append(f"▪️ السابق: {previous}")
            lines.append(f"▪️ المتوقع: {expected}")
            lines.append(f"▪️ الفعلي: {actual}")
            lines.append(self.separator)
            lines.append("")

        return "\n".join(lines)

    # ==================================================
    # COMPANY TEMPLATE ENGINE
    # ==================================================

    def build_company_event_template(self, companies):
        if not companies:
            return ""

        lines = ["🏢 أهم إعلانات الشركات", ""]

        for item in companies:
            name = item.get("name", "")
            desc = item.get("desc", "")
            lines.append(f"{name}")
            lines.append(desc)
            lines.append("")

        lines.append(self.separator)
        lines.append("⚠️ قد تشهد الأسواق تقلبات مرتفعة اليوم.")

        return "\n".join(lines)

    # ==================================================
    # GEOPOLITICAL TEMPLATE ENGINE
    # ==================================================

    def build_geopolitical_event_template(self, events):
        if not events:
            return ""

        lines = ["🌍 أهم الأحداث السياسية والجيوسياسية المؤثرة", ""]

        for item in events:
            lines.append(f"🌐 {item}")

        lines.append("")
        lines.append(self.separator)

        return "\n".join(lines)

    # ==================================================
    # PRE MARKET REPORT ENGINE
    # ==================================================

    def build_pre_market_report(
        self,
        macro_news,
        company_news,
        earnings_news,
        economic_calendar,
        geo_events=None
    ):

        report = [self.build_pre_market_header(), ""]

        # القسم الاقتصادي الجديد
        economic_section = self.build_economic_event_template(economic_calendar)
        if economic_section:
            report.append(economic_section)

        # قسم الأخبار العامة (macro_news)
        if macro_news:
            report.append("📰 أهم الأخبار")
            for item in macro_news:
                report.append(f"{self.bullet} {item}")
            report.append("")

        # قسم أخبار الشركات
        if company_news:
            report.append("🏢 أهم أخبار الشركات")
            for item in company_news:
                report.append(f"{self.bullet} {item}")
            report.append("")

        # قسم أرباح الشركات
        if earnings_news:
            report.append("💰 أرباح الشركات")
            for item in earnings_news:
                report.append(f"{self.bullet} {item}")
            report.append("")

        # القسم الجيوسياسي الجديد
        if geo_events:
            geo_section = self.build_geopolitical_event_template(geo_events)
            report.append(geo_section)

        report.append("")
        report.append(self.build_bot_signature())

        return "\n".join(report)

    # ==================================================
    # AFTER MARKET REPORT ENGINE
    # ==================================================

    def build_after_market_report(
        self,
        trade_summary,
        macro_news,
        company_news,
        conclusion,
        geo_events=None
    ):

        report = [self.build_after_market_header(), ""]

        # ملخص الجلسة
        if trade_summary:
            report.append("📊 ملخص الجلسة")
            for item in trade_summary:
                report.append(f"{self.bullet} {item}")
            report.append("")

        # الأخبار الاقتصادية
        if macro_news:
            report.append("📰 أهم الأخبار الاقتصادية")
            for item in macro_news:
                report.append(f"{self.bullet} {item}")
            report.append("")

        # أخبار الشركات
        if company_news:
            report.append("🏢 أهم أخبار الشركات")
            for item in company_news:
                report.append(f"{self.bullet} {item}")
            report.append("")

        # الأحداث الجيوسياسية
        if geo_events:
            report.append("🌍 أبرز الأحداث السياسية والجيوسياسية المؤثرة")
            for item in geo_events:
                report.append(f"{self.bullet} {item}")
            report.append("")

        # الخلاصة
        if conclusion:
            report.append(conclusion)

        report.append("")
        report.append(self.build_bot_signature())

        return "\n".join(report)

    # ==================================================
    # DAILY CONCLUSION ENGINE
    # ==================================================

    def build_daily_conclusion(self, market_status, total_news):
        if market_status == "BULLISH":
            return "🟢 أنهى السوق الجلسة بزخم إيجابي مع استمرار قوة المشترين."
        if market_status == "BEARISH":
            return "🔴 أنهى السوق الجلسة بضغط بيعي واستمرار حالة الحذر."
        return f"🟡 تمت متابعة {total_news} خبر مؤثر خلال الجلسة."

    # ==================================================
    # PREVIEW ENGINE
    # ==================================================

    def preview_message(self, news, news_analysis):
        return self.format_news_message(news, news_analysis)

    # ==================================================
    # MAIN FORMATTER ENGINE
    # ==================================================

    def format(self, news, news_analysis):
        return self.format_news_message(news, news_analysis)

# ==================================================
# TEST
# ==================================================

if __name__ == "__main__":

    formatter = NewsFormatter()

    sample_news = {
        "company": "NVIDIA",
        "symbol": "NVDA",
        "title": "NVIDIA Raises Guidance",
        "summary": (
            "NVIDIA announced quarterly results above expectations "
            "and raised guidance for the next quarter."
        ),
        "source": "Business Wire",
        "url": "https://www.businesswire.com/",
        "published": "2026-07-09T10:00:00Z"
    }

    sample_analysis = {
        "priority": "CRITICAL",
        "market_effect": [
            "إيجابي لسهم NVDA",
            "دعم لقطاع أشباه الموصلات",
            "قد يدعم مؤشر NASDAQ"
        ],
        "affected_assets": [
            "NVDA",
            "SOXX",
            "QQQ",
            "SPX"
        ]
    }

    print(
        formatter.format(
            sample_news,
            sample_analysis
        )
    )
