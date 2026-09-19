from __future__ import annotations

import os
import contextlib
import io
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import TestCase

from database.database import DatabaseManager
from daily_scheduler import DailyScheduler
from images.image_engine import ImageEngine
from news.news_engine import NewsEngine
from news.news_editor import NewsEditor
from PIL import Image


class _Provider:
    def __init__(self, items):
        self.items = items

    def get_news(self):
        return list(self.items)


class _Editor:
    def clean_and_translate(self, news):
        return {
            **news,
            "translated": "أعلنت NVIDIA (NVDA) سعراً قدره $120 بارتفاع 5%.",
            "translated_summary": "أعلنت NVIDIA (NVDA) سعراً قدره $120 بارتفاع 5%.",
            "translation_status": "TRANSLATED",
            "translation_error": None,
        }


class _FailingEditor:
    def clean_and_translate(self, news):
        return {**news, "translated": news["summary"], "translation_status": "FAILED", "translation_error": "TRANSLATION_RATE_LIMIT"}


class _Telegram:
    def __init__(self, result=True):
        self.result = result
        self.sent = []

    def news_destination(self):
        return "news-room"

    def send_message(self, text, *, destination=None):
        self.sent.append((text, destination))
        return self.result

    def send_news_with_image(self, image, text, *, destination=None):
        self.sent.append((image, text, destination))
        return self.result


class _BrokenImages:
    def build_image(self, *_args):
        raise RuntimeError("render failed")


class NewsIntegrationPhase7Tests(TestCase):
    def setUp(self):
        self.db_path = Path(__file__).with_name("_phase7_news_test.db")
        if self.db_path.exists():
            self.db_path.unlink()
        self.journal = DatabaseManager(str(self.db_path))
        self.news = {
            "title": "NVIDIA NVDA reports CPI-sensitive results at $120, up 5%",
            "summary": "NVIDIA (NVDA) reported $120 and a 5% gain.",
            "source": "Federal Reserve",
            "url": "https://example.test/news/nvda",
            "published": datetime.now(timezone.utc).isoformat(),
            "category": "MACRO",
        }

    def tearDown(self):
        if self.db_path.exists():
            self.db_path.unlink()

    def engine(self, items=None, editor=None):
        return NewsEngine(provider=_Provider(items or [self.news]), editor=editor or _Editor(), journal=self.journal)

    def test_english_news_becomes_arabic_and_preserves_market_tokens(self):
        item = self.engine().morning_news_structured()[0]
        self.assertIn("NVDA", item["image_data"]["body"])
        self.assertIn("$120", item["image_data"]["body"])
        self.assertIn("5%", item["image_data"]["body"])
        self.assertEqual(item["template"], "news")

    def test_persistent_dedup_survives_new_engine_instance(self):
        engine = self.engine()
        item = engine.morning_news_structured()[0]
        self.assertTrue(engine.mark_as_sent(item["raw"], destination="news-room"))
        self.assertEqual(self.engine().morning_news_structured(), [])

    def test_stale_or_missing_timestamp_is_not_queued(self):
        stale = {**self.news, "url": "https://example.test/old", "published": (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()}
        missing = {**self.news, "url": "https://example.test/missing", "published": ""}
        self.assertEqual(self.engine([stale]).morning_news_structured(), [])
        self.assertEqual(self.engine([missing]).morning_news_structured(), [])

    def test_translation_failure_is_recorded_and_not_sent_as_guessed_arabic(self):
        self.assertEqual(self.engine(editor=_FailingEditor()).morning_news_structured(), [])
        conn = self.journal.connect()
        row = conn.execute("SELECT status FROM news_journal").fetchone()
        conn.close()
        self.assertEqual(row[0], "TRANSLATION_RATE_LIMIT")

    def test_premarket_selects_top_three_before_translation(self):
        translated = []

        class CountingEditor(_Editor):
            def clean_and_translate(self, news):
                translated.append(news["url"])
                return super().clean_and_translate(news)

        items = [
            {**self.news, "url": f"https://example.test/{index}", "title": f"CPI NVDA {index}", "summary": f"CPI NVDA {index}", "category": "MACRO"}
            for index in range(5)
        ]
        result = self.engine(items, editor=CountingEditor()).morning_news_structured()
        self.assertEqual(len(result), 3)
        self.assertEqual(len(translated), 3)

    def test_validated_translation_is_reused_after_restart(self):
        calls = []

        class CountingEditor(_Editor):
            def clean_and_translate(self, news):
                calls.append(news["url"])
                return super().clean_and_translate(news)

        first = self.engine(editor=CountingEditor()).morning_news_structured()[0]
        second = self.engine(editor=CountingEditor()).morning_news_structured()[0]
        self.assertEqual(len(calls), 1)
        self.assertEqual(first["text"], second["text"])

    def test_translation_error_categories_are_not_collapsed(self):
        class _QuotaError(Exception):
            code = 429
            message = "quota exhausted; check billing"

        class _DailyError(Exception):
            code = 429
            message = "requests per day quota exceeded"

        class _ServerError(Exception):
            code = 503
            message = "backend unavailable"

        self.assertEqual(NewsEditor.classify_translation_error(_QuotaError()), "TRANSLATION_QUOTA_EXHAUSTED")
        self.assertEqual(NewsEditor.classify_translation_error(_DailyError()), "TRANSLATION_DAILY_QUOTA")
        self.assertEqual(NewsEditor.classify_translation_error(_ServerError()), "TRANSLATION_SERVER_ERROR")

    def test_title_quota_failure_does_not_spend_a_summary_request(self):
        class _QuotaError(Exception):
            code = 429
            message = "quota exhausted; check billing"

        class _Models:
            def __init__(self):
                self.calls = 0

            def generate_content(self, **_kwargs):
                self.calls += 1
                raise _QuotaError()

        class _Client:
            def __init__(self):
                self.models = _Models()

        editor = NewsEditor.__new__(NewsEditor)
        editor.max_title_length = 120
        editor.max_summary_length = 280
        editor.remove_words = []
        editor.client = _Client()
        editor.model_name = "test-model"
        result = editor.clean_and_translate(self.news)
        self.assertEqual(editor.client.models.calls, 1)
        self.assertEqual(result["translation_status"], "FAILED")
        self.assertEqual(result["translation_error"], "TRANSLATION_QUOTA_EXHAUSTED")

    def test_translation_validation_accepts_equivalent_arabic_currency_notation(self):
        """$5 and 5 دولار are the same protected financial value.

        Tickers still have to remain literal: this is normalization, not a
        relaxation of the validation boundary.
        """
        original = "NVDA rises from $5 to $7, up 2.4% on SPX"
        arabic = "ارتفع NVDA من 5 دولار إلى 7 دولار، بنسبة 2.4% على SPX"
        self.assertEqual(
            NewsEditor.protected_tokens(original) - NewsEditor.protected_tokens(arabic),
            set(),
        )
        missing_ticker = NewsEditor.protected_tokens(original) - NewsEditor.protected_tokens(
            "ارتفع من 5 دولار إلى 7 دولار، بنسبة 2.4% على SPX"
        )
        self.assertIn("symbol:NVDA", missing_ticker)

    def test_validation_rejection_exposes_exact_missing_symbol_for_journal_diagnostics(self):
        class _Response:
            text = "ارتفع سهم SPX بنسبة 2.4% إلى 5 دولار"

        class _Models:
            def generate_content(self, **_kwargs):
                return _Response()

        class _Client:
            models = _Models()

        editor = NewsEditor.__new__(NewsEditor)
        editor.max_title_length = 120
        editor.max_summary_length = 280
        editor.remove_words = []
        editor.client = _Client()
        editor.model_name = "test-model"
        result = editor.clean_and_translate({**self.news, "title": "NVDA SPX rises to $5, up 2.4%"})
        self.assertEqual(result["translation_error"], "TRANSLATION_VALIDATION_REJECTED")
        self.assertEqual(result["translation_validation_missing"], {"title": ["symbol:NVDA"]})

    def test_marketwatch_source_is_preserved_as_an_html_original_link(self):
        item = self.engine([
            {**self.news, "source": "MarketWatch", "url": "https://example.test/marketwatch"}
        ]).morning_news_structured()[0]
        self.assertIn('<a href="https://example.test/marketwatch">MarketWatch</a>', item["text"])

    def test_image_failure_falls_back_to_ready_text_and_records_delivery(self):
        engine = self.engine()
        item = engine.morning_news_structured()[0]
        telegram = _Telegram(result=True)
        scheduler = object.__new__(DailyScheduler)
        scheduler.telegram, scheduler.news_engine = telegram, engine
        scheduler.image_engine = _BrokenImages()
        with contextlib.redirect_stdout(io.StringIO()):
            result = scheduler.send_structured(item, message_type="news")
        self.assertTrue(result)
        self.assertEqual(telegram.sent[0][1], "news-room")
        self.assertTrue(self.journal.news_was_sent(engine.generate_news_id(self.news)))

    def test_telegram_failure_has_delivery_history_but_is_not_marked_sent(self):
        engine = self.engine()
        item = engine.morning_news_structured()[0]
        telegram = _Telegram(result=False)
        scheduler = object.__new__(DailyScheduler)
        scheduler.telegram, scheduler.news_engine = telegram, engine
        scheduler.image_engine = None
        with contextlib.redirect_stdout(io.StringIO()):
            result = scheduler.send_structured(item, message_type="news")
        self.assertFalse(result)
        news_id = engine.generate_news_id(self.news)
        self.assertFalse(self.journal.news_was_sent(news_id))
        conn = self.journal.connect()
        row = conn.execute("SELECT success FROM news_deliveries WHERE news_id = ?", (news_id,)).fetchone()
        conn.close()
        self.assertEqual(row[0], 0)

    def test_provider_failure_is_isolated_by_existing_safe_fetch(self):
        from news.news_provider import NewsProvider
        provider = NewsProvider()
        provider.providers = [
            {"name": "bad", "category": "MACRO", "func": lambda _category: (_ for _ in ()).throw(RuntimeError("down"))},
            {"name": "good", "category": "MACRO", "func": lambda _category: [self.news]},
        ]
        self.assertEqual(provider.get_news(), [self.news])

    def test_breaking_context_selects_existing_breaking_template(self):
        item = self.engine().breaking_news_structured()[0]
        self.assertEqual(item["template"], "breaking")
        self.assertEqual(item["image_data"]["session"], "MARKET_OPEN")

    def test_rtl_renderer_accepts_ready_arabic_without_changing_payload(self):
        engine = ImageEngine()
        payload = "خبر عربي NVDA بسعر $120 ونسبة 5%"
        canvas = Image.new("RGBA", (800, 300), "#000000")
        self.assertIs(engine.draw_text_block(canvas, payload, 760, 40, rtl=True), canvas)
        self.assertEqual(payload, "خبر عربي NVDA بسعر $120 ونسبة 5%")
