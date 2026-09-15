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
- Keep numbers, dates, and percentages unchanged.
- Output Arabic only.

Title:
{title}

Summary:
{summary}
"""

    # ==================================================
    # GEMINI TRANSLATION ENGINE
    # ==================================================

    def translate_news(self, title, summary):

        title = self.clean_title(title)
        summary = self.clean_summary(summary)

        prompt = self.build_translation_prompt(title, summary)

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )

            translated_text = self.format_translation(getattr(response, "text", ""))

            if not translated_text or translated_text.strip() == "":
                return summary

            return translated_text

        except Exception as error:
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

        translated_summary = self.translate_news(title, summary)

        edited_news = cleaned.copy()
        edited_news["translated_summary"] = translated_summary

        return edited_news
