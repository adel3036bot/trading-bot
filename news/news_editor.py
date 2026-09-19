# ==================================================
# IMPORTS
# ==================================================

import logging
import re
import unicodedata
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
        self.last_validation_missing = {}

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

        # A single news translation can legitimately take longer than the
        # SDK's short default network timeout.  This does not add retries or
        # change quota behavior.
        self.client = genai.Client(api_key=GEMINI_API_KEY, http_options={"timeout": 60_000})

        # ==================
        # MODEL SETTINGS
        # ==================

        self.model_name = "gemini-3.1-flash-lite"

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
        """Return semantic tokens that must survive a translation.

        The former raw-string comparison incorrectly rejected equivalent
        Arabic financial notation, e.g. ``$5`` versus ``5 دولار``.  Symbols
        remain strict and numbers retain their financial meaning (plain,
        currency, or percentage); only Unicode/directional representation is
        normalized.
        """
        normalized = unicodedata.normalize("NFKC", str(text or "")).translate(
            str.maketrans("٠١٢٣٤٥٦٧٨٩٫٬٪", "0123456789.,%")
        )
        tokens = {
            f"symbol:{symbol}"
            for symbol in re.findall(r"\b[A-Z]{2,5}\b", normalized)
        }

        for match in re.finditer(r"\$?\d[\d,]*(?:\.\d+)?%?", normalized):
            raw = match.group(0)
            number = raw.replace("$", "").replace(",", "")
            context = normalized[max(0, match.start() - 12):match.end() + 24]
            if raw.endswith("%"):
                kind = "percent"
            elif raw.startswith("$") or re.search(
                r"(?:\b(?:USD|US\$)\b|دولار(?:ات|ًا|اً)?|أمريكي(?:ة)?)",
                context,
                flags=re.IGNORECASE,
            ):
                kind = "currency"
            else:
                kind = "number"
            tokens.add(f"{kind}:{number}")
        return tokens

    @staticmethod
    def classify_translation_error(error):
        """Map provider failures to safe, actionable journal statuses.

        The provider response is intentionally not logged: it can contain
        request context and is not needed for retries or reporting.
        """
        code = getattr(error, "code", None) or getattr(error, "status_code", None)
        message = str(getattr(error, "message", "") or error).lower()
        if str(code) == "429" or "resource_exhausted" in message:
            if any(marker in message for marker in ("per day", "daily", "requests per day", "rpd")):
                return "TRANSLATION_DAILY_QUOTA"
            if "quota" in message or "billing" in message:
                return "TRANSLATION_QUOTA_EXHAUSTED"
            return "TRANSLATION_RATE_LIMIT"
        if str(code).startswith("5"):
            return "TRANSLATION_SERVER_ERROR"
        return "TRANSLATION_API_FAILED"

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
                return title, "TRANSLATION_RESPONSE_INVALID"
            missing = self.protected_tokens(title) - self.protected_tokens(translated)
            if missing:
                self.last_validation_missing = {"title": sorted(missing)}
                return title, "TRANSLATION_VALIDATION_REJECTED"
            return translated, None
        except Exception as error:
            status = self.classify_translation_error(error)
            logging.warning("Gemini title translation failed with status=%s", status)
            return title, status

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
                self.last_translation_error = "TRANSLATION_RESPONSE_INVALID"
                return summary

            return translated_text

        except Exception as error:
            self.last_translation_error = self.classify_translation_error(error)
            logging.warning("Gemini summary translation failed with status=%s", self.last_translation_error)

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
        self.last_validation_missing = {}

        title = cleaned.get("title", "")
        summary = cleaned.get("summary", "")

        translated_title, title_error = self.translate_title(title)
        # A failed headline request means the complete Arabic payload cannot
        # be validated.  Do not spend a second Gemini request on its summary.
        if title_error:
            translated_summary = summary
            self.last_translation_error = title_error
        else:
            translated_summary = self.translate_news(title, summary)

        # The existing editor is the only translation layer.  Keep the old
        # translated_summary key for compatibility and expose the canonical
        # translated key consumed by Formatter/ImageEngine.
        translation_error = title_error or getattr(self, "last_translation_error", None)
        missing_summary_tokens = self.protected_tokens(summary) - self.protected_tokens(translated_summary)
        if missing_summary_tokens:
            translation_error = "TRANSLATION_VALIDATION_REJECTED"
            self.last_validation_missing["summary"] = sorted(missing_summary_tokens)

        edited_news = cleaned.copy()
        edited_news["original_title"] = title
        edited_news["title"] = translated_title
        edited_news["translated_summary"] = translated_summary
        edited_news["translated"] = translated_summary
        edited_news["translation_status"] = "FAILED" if translation_error else "TRANSLATED"
        edited_news["translation_error"] = translation_error
        edited_news["translation_validation_missing"] = dict(self.last_validation_missing)

        return edited_news
