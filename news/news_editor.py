# ==================================================
# IMPORTS
# ==================================================

import re
from html import unescape
from google import genai
from config import GEMINI_API_KEY

# ==================================================
# NEWS EDITOR
# ==================================================

class NewsEditor:

    def __init__(self):

        # ==================
        # SETTINGS
        # ==================

        self.max_title_length = 120
        self.max_summary_length = 280

        # ==================
        # COMMON WORDS
        # ==================

        self.remove_words = [
            "Breaking",
            "Update",
            "Press Release",
            "Business Wire",
            "PR Newswire",
            "GlobeNewswire"
        ]

        # ==================
        # GEMINI CLIENT
        # ==================

        self.client = genai.Client(api_key=GEMINI_API_KEY)

        # ==================
        # MODEL SETTINGS
        # ==================

        self.model_name = "gemini-flash-latest"

    # ==================================================
    # TRANSLATION PROMPT ENGINE
    # ==================================================

    def build_translation_prompt(self, title, summary):

        return f"""
You are a professional financial news editor for ADEL SMART BOT ELITE.

Your job is to rewrite the summary in clear, concise Arabic suitable for traders.

Rules:
- Use only the information provided.
- Focus on the market-relevant information only.
- Never invent information.
- Never add analysis or predictions.
- Never complete missing facts.
- If the summary is incomplete, rewrite only the available part clearly.
- If the summary contains multiple facts, present them as 2–4 short bullet points using (🔹).
- If the summary contains only one key fact, present it as one short sentence.
- Do not repeat the title.
- Use formal Arabic suitable for financial markets.
- Keep company names in English.
- Keep stock symbols (for example NVDA, AAPL, TSLA, SPY), numbers, prices,
  percentages, dates, times, institutions and people exactly when present.
- Keep numbers, dates, and percentages unchanged.
- Output Arabic only.

Title:
{title}

Summary:
{summary}
"""

    def build_title_translation_prompt(self, title):
        return f"""
Translate this financial-news headline into clear professional Arabic.
Use only the supplied headline. Do not add analysis, prediction, or facts.
Keep company names, stock symbols (NVDA, AAPL, TSLA, SPY), numbers, prices,
percentages, dates, times, institutions and people exactly when present.
Return the headline only in Arabic.

Headline:
{title}
"""

    @staticmethod
    def protected_tokens(text):
        return set(re.findall(r"\$?\d[\d,]*(?:\.\d+)?%?|\b[A-Z]{1,5}\b", text or ""))

    def translate_title(self, title):
        title = self.clean_title(title)
        if not title:
            return title, None
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=self.build_title_translation_prompt(title),
            )
            translated = self.format_translation(getattr(response, "text", ""))
            if not translated:
                return title, "empty_title_translation"
            missing = self.protected_tokens(title) - self.protected_tokens(translated)
            if missing:
                return title, "missing_protected_title_tokens"
            return translated, None
        except Exception as error:
            print("TITLE TRANSLATION ERROR", error)
            return title, type(error).__name__

    # ==================================================
    # GEMINI TRANSLATION ENGINE
    # ==================================================

    def translate_news(self, title, summary):

        title = self.clean_title(title)
        summary = self.clean_summary(summary)

        prompt = self.build_translation_prompt(title, summary)

        self.last_translation_error = None
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )

            translated_text = self.format_translation(getattr(response, "text", ""))

            if not translated_text or translated_text.strip() == "":
                self.last_translation_error = "empty_translation"
                return summary

            return translated_text

        except Exception as error:
            self.last_translation_error = type(error).__name__
            print("\n===================================")
            print("GEMINI TRANSLATION ERROR")
            print("===================================")
            print(error)
            print("===================================\n")

            return summary

    # ==================================================
    # FORMAT TRANSLATION ENGINE
    # ==================================================

    def format_translation(self, translated_text):

        if not translated_text:
            return ""

        translated_text = unescape(translated_text).strip()

        translated_text = re.sub(r"\n{3,}", "\n\n", translated_text)
        translated_text = re.sub(r"[ \t]+", " ", translated_text)

        return translated_text.strip()

    # ==================================================
    # TITLE CLEANER ENGINE
    # ==================================================

    def clean_title(self, title):

        if not title:
            return ""

        title = unescape(title).strip()

        for word in self.remove_words:
            title = title.replace(word, "")

        title = re.sub(r"\s+", " ", title).strip()

        if len(title) > self.max_title_length:
            title = title[:self.max_title_length].rstrip() + "..."

        return title

    # ==================================================
    # SUMMARY CLEANER ENGINE
    # ==================================================

    def clean_summary(self, summary):

        if not summary:
            return ""

        summary = unescape(summary).strip()

        summary = re.sub(r"<.*?>", "", summary)

        summary = re.sub(r"\.{3,}$", "", summary).strip()

        summary = re.sub(r"\s+", " ", summary).strip()

        if len(summary) > self.max_summary_length:
            summary = summary[:self.max_summary_length].rstrip() + "..."

        return summary

    # ==================================================
    # NEWS CLEANER ENGINE
    # ==================================================

    def clean_news(self, news):

        if not news:
            return {}

        edited_news = news.copy()

        edited_news["title"] = self.clean_title(news.get("title", ""))
        edited_news["summary"] = self.clean_summary(news.get("summary", ""))

        return edited_news

    # ==================================================
    # CLEAN + TRANSLATE PIPELINE (متوافقة مع NewsEngine)
    # ==================================================

    def clean_and_translate(self, news):

        if not news:
            return {}

        cleaned = self.clean_news(news)

        title = cleaned.get("title", "")
        summary = cleaned.get("summary", "")

        translated_title, title_error = self.translate_title(title)
        translated_summary = self.translate_news(title, summary)

        # The existing editor is the only translation layer.  Keep the old
        # translated_summary key for compatibility and expose the canonical
        # translated key consumed by Formatter/ImageEngine.
        translation_error = title_error or getattr(self, "last_translation_error", None)
        missing_summary_tokens = self.protected_tokens(summary) - self.protected_tokens(translated_summary)
        if missing_summary_tokens:
            translation_error = "missing_protected_summary_tokens"

        edited_news = cleaned.copy()
        edited_news["original_title"] = title
        edited_news["title"] = translated_title
        edited_news["translated_summary"] = translated_summary
        edited_news["translated"] = translated_summary
        edited_news["translation_status"] = "FAILED" if translation_error else "TRANSLATED"
        edited_news["translation_error"] = translation_error

        return edited_news
