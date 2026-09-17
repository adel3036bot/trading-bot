# ==================================================
# NEWS ENGINE (STRUCTURED VERSION)
# ADEL SMART BOT ELITE
# ==================================================

from collections import deque
from datetime import datetime, timedelta, timezone
import logging

from news.news_provider import NewsProvider
from news.news_filter import NewsFilter
from news.news_editor import NewsEditor
from news.news_formatter import NewsFormatter
from database.database import DatabaseManager


class NewsEngine:

    def __init__(self, provider=None, news_filter=None, editor=None, formatter=None, journal=None):

        self.provider = provider or NewsProvider()
        self.filter = news_filter or NewsFilter()
        self.editor = editor or NewsEditor()
        self.formatter = formatter or NewsFormatter()
        self.journal = journal or DatabaseManager()
        self.max_news_age = timedelta(hours=48)

        self.sent_history = set()
        self.queue = deque()
        self.max_queue_size = 100

        self.failed_news = []
        self.pending_news = []

    # ==================================================
    # NEWS ID ENGINE
    # ==================================================

    def generate_news_id(self, news):
        return self.journal.build_news_id(news)

    @staticmethod
    def _parse_timestamp(news):
        value = news.get("timestamp") or news.get("published")
        if not value:
            return None
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except (TypeError, ValueError):
            return None
        return parsed if parsed.tzinfo else None

    def has_reliable_timestamp(self, news):
        published = self._parse_timestamp(news)
        if published is None:
            return False
        now = datetime.now(timezone.utc)
        return now - self.max_news_age <= published.astimezone(timezone.utc) <= now + timedelta(minutes=5)

    def is_duplicate(self, news):

        nid = self.generate_news_id(news)

        if nid in self.sent_history:
            return True

        try:
            if self.journal.news_was_sent(nid):
                return True
        except Exception as error:
            # Database persistence is a reliability improvement; a temporary
            # journal read failure must not stop independent source processing.
            logging.error("News journal dedup lookup failed: %s", error)

        for item in self.queue:
            if self.generate_news_id(item) == nid:
                return True

        return False

    def mark_as_sent(self, news, *, destination="DEFAULT", success=True, failure_reason=None):
        """Record delivery independently; a failed delivery is never marked sent."""
        if not news:
            return False
        try:
            news_id = self.journal.record_news(news, status="APPROVED")
            self.journal.record_news_delivery(news_id, destination, success=success, failure_reason=failure_reason)
            if success:
                self.journal.update_news_status(news_id, "SENT")
                self.sent_history.add(news_id)
                return True
            self.journal.update_news_status(news_id, "DELIVERY_FAILED", metadata={"reason": failure_reason})
        except Exception as error:
            logging.error("News delivery journal failed: %s", error)
        return False

    def record_delivery_failure(self, news, *, destination="DEFAULT", reason="telegram_delivery_failed"):
        return self.mark_as_sent(news, destination=destination, success=False, failure_reason=reason)

    # ==================================================
    # QUEUE ENGINE
    # ==================================================

    def add_to_queue(self, news):

        if not self.has_reliable_timestamp(news):
            try:
                news_id = self.journal.record_news(news, status="REJECTED_TIMESTAMP")
                self.journal.update_news_status(news_id, "REJECTED_TIMESTAMP")
            except Exception as error:
                logging.error("News timestamp journal failed: %s", error)
            return False

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
        raw = self.provider.get_news()
        for item in raw or []:
            try:
                self.journal.record_news(item, status="FETCHED")
            except Exception as error:
                logging.error("News fetch journal failed: %s", error)
        return raw

    def classify_news(self, raw):
        return self.filter.classify_news_list(raw)

    def filter_important(self, classified):
        return self.filter.filter_important_news(classified)

    def prepare_structured(self, news):

        edited = self.editor.clean_and_translate(news)

        if edited.get("translation_status") == "FAILED":
            try:
                news_id = self.journal.record_news(news, status="FAILED_TRANSLATION")
                self.journal.update_news_status(news_id, "FAILED_TRANSLATION", metadata={"reason": edited.get("translation_error")})
            except Exception as error:
                logging.error("News translation journal failed: %s", error)
            return None

        try:
            self.journal.record_news(news, status="TRANSLATED", metadata={"priority": news.get("priority"), "breaking": news.get("breaking", False)})
        except Exception as error:
            logging.error("News journal write failed: %s", error)

        # ------------------------------
        # IMAGE DATA (for ImageEngine)
        # ------------------------------
        image_data = {
            "headline": edited.get("title", ""),
            "body": edited.get("translated", ""),
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

        # Providers deliver source facts, not Telegram session labels.  Attach
        # the caller's delivery context here; this fixes the previous empty
        # PRE_MARKET/MARKET_OPEN lists without inferring a market direction.
        filtered = [
            {**n, "session": session_mode}
            for n in important
            if (not n.get("session") or n.get("session") == session_mode)
            and self.has_reliable_timestamp(n)
            and not self.is_duplicate(n)
        ]

        for item in important:
            if not self.has_reliable_timestamp(item):
                try:
                    news_id = self.journal.record_news(item, status="REJECTED_TIMESTAMP")
                    self.journal.update_news_status(news_id, "REJECTED_TIMESTAMP")
                except Exception as error:
                    logging.error("News timestamp journal failed: %s", error)
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
            prepared = self.prepare_structured(item)
            if prepared:
                structured_list.append(prepared)

        return structured_list

    def morning_news_structured(self):
        return self.run_internal_structured("PRE_MARKET")

    def breaking_news_structured(self):
        return self.run_internal_structured("MARKET_OPEN")

    def after_market_structured(self):
        return self.run_internal_structured("AFTER_MARKET")

    # Compatibility belongs to NewsEngine, not to DailyScheduler monkey patches.
    def _legacy_messages(self, structured):
        return [{"message": item.get("text", ""), "raw": item.get("raw")} for item in structured or [] if isinstance(item, dict)]

    def morning_news(self):
        return self._legacy_messages(self.morning_news_structured())

    def breaking_news(self):
        return self._legacy_messages(self.breaking_news_structured())

    def after_market_news(self):
        return self._legacy_messages(self.after_market_structured())

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
