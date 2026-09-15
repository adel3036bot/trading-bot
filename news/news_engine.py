# ==================================================
# NEWS ENGINE (STRUCTURED VERSION)
# ADEL SMART BOT ELITE
# ==================================================

from collections import deque
import logging

from news.news_provider import NewsProvider
from news.news_filter import NewsFilter
from news.news_editor import NewsEditor
from news.news_formatter import NewsFormatter


class NewsEngine:

    def __init__(self):

        self.provider = NewsProvider()
        self.filter = NewsFilter()
        self.editor = NewsEditor()
        self.formatter = NewsFormatter()

        self.sent_history = set()
        self.queue = deque()
        self.max_queue_size = 100

        self.failed_news = []
        self.pending_news = []

    # ==================================================
    # NEWS ID ENGINE
    # ==================================================

    def generate_news_id(self, news):

        headline = news.get("headline", news.get("title", "")).strip().lower()
        source = news.get("source", "").strip().lower()
        published = news.get("timestamp", news.get("published", "")).strip()

        return f"{source}|{headline}|{published}"

    def is_duplicate(self, news):

        nid = self.generate_news_id(news)

        if nid in self.sent_history:
            return True

        for item in self.queue:
            if self.generate_news_id(item) == nid:
                return True

        return False

    def mark_as_sent(self, news):
        self.sent_history.add(self.generate_news_id(news))

    # ==================================================
    # QUEUE ENGINE
    # ==================================================

    def add_to_queue(self, news):

        if self.is_duplicate(news):
            return False

        if len(self.queue) >= self.max_queue_size:
            return False

        self.queue.append(news)
        return True

    def get_next_priority_news(self):

        if not self.queue:
            return None

        priority_map = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}

        sorted_queue = sorted(
            list(self.queue),
            key=lambda n: priority_map.get(n.get("priority", "LOW"), 1),
            reverse=True
        )

        news = sorted_queue[0]
        self.queue.remove(news)
        return news

    # ==================================================
    # MAIN WORKFLOW (STRUCTURED OUTPUT)
    # ==================================================

    def fetch_news(self):
        return self.provider.get_news()

    def classify_news(self, raw):
        return self.filter.classify_news_list(raw)

    def filter_important(self, classified):
        return self.filter.filter_important_news(classified)

    def prepare_structured(self, news):

        edited = self.editor.clean_and_translate(news)

        # ------------------------------
        # IMAGE DATA (for ImageEngine)
        # ------------------------------
        image_data = {
            "headline": edited.get("title", ""),
            "body": edited.get("translated", edited.get("summary", "")),
            "category": edited.get("category", "غير مصنف"),
            "session": edited.get("session", "غير محدد"),
            "timestamp": edited.get("published", ""),
            "source": edited.get("source", "")
        }

        # ------------------------------
        # TEXT MESSAGE (for Telegram)
        # ------------------------------
        text_message = self.formatter.format(edited, news)

        # ------------------------------
        # TEMPLATE SELECTION (CENTRALIZED)
        # ------------------------------
        session = news.get("session")

        if session == "MARKET_OPEN":
            template = "breaking"
        else:
            template = "news"

        return {
            "template": template,
            "image_data": image_data,
            "text": text_message,
            "raw": news
        }

    def process_structured(self):

        raw = self.fetch_news()
        classified = self.classify_news(raw)
        important = self.filter_important(classified)

        for item in important:
            self.add_to_queue(item)

        next_news = self.get_next_priority_news()

        if not next_news:
            return None

        return self.prepare_structured(next_news)

    # ==================================================
    # LEGACY MODES (STRUCTURED)
    # ==================================================

    def run_internal_structured(self, session_mode):

        raw = self.fetch_news()
        classified = self.classify_news(raw)
        important = self.filter_important(classified)

        filtered = [n for n in important if n.get("session") == session_mode]
        unique = [n for n in filtered if not self.is_duplicate(n)]

        if not unique:
            return []

        priority_map = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}

        sorted_news = sorted(
            unique,
            key=lambda n: priority_map.get(n.get("priority", "LOW"), 1),
            reverse=True
        )

        structured_list = []

        for item in sorted_news:
            structured_list.append(self.prepare_structured(item))

        return structured_list

    def morning_news_structured(self):
        return self.run_internal_structured("PRE_MARKET")

    def breaking_news_structured(self):
        return self.run_internal_structured("MARKET_OPEN")

    def after_market_structured(self):
        return self.run_internal_structured("AFTER_MARKET")

    # ==================================================
    # MORNING REPORT (STRUCTURED)
    # ==================================================

    def build_morning_report_structured(self, macro, company, earnings, events):

        text = self.formatter.build_morning_report(
            macro_news=macro,
            company_news=company,
            earnings_news=earnings,
            events=events
        )

        image_data = {
            "macro": macro,
            "company": company,
            "earnings": earnings,
            "events": events
        }

        return {
            "template": "daily_report",
            "image_data": image_data,
            "text": text
        }

    # ==================================================
    # FULL PRE-MARKET REPORT (STRUCTURED)
    # ==================================================

    def full_pre_market_structured(self):

        text = self.formatter.build_full_pre_market_report()

        image_data = {
            "session": "FULL_PRE_MARKET"
        }

        return {
            "template": "daily_report",
            "image_data": image_data,
            "text": text
        }
