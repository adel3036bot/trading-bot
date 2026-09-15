# ==================================================
# ADEL SMART BOT
# NEWS PROVIDER (REMASTERED)
# VERSION 2.2
# ==================================================

import logging
import requests
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime


class NewsProvider:

    def __init__(self):

        # ==================
        # SESSION & HEADERS
        # ==================
        self.timeout = 10
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Adel Smart Bot/2.2 (contact: adelsmartbot@gmail.com)",
            "Accept": "application/rss+xml, application/xml, text/xml"
        })

        # ==================
        # LOGGING
        # ==================
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(levelname)s | %(message)s"
        )

        # ==================
        # CENTRAL PROVIDER LIST
        # ==================
        # ترتيب المصادر حسب الأولوية:
        # 1) مصادر رسمية أساسية
        # 2) مصادر عالمية وجيوسياسية (AP News كمصدر رئيسي)
        # 3) مصادر مساندة للأسواق والاقتصاد (CNBC + MarketWatch)

        self.providers = [

            # COMPANY (PRIMARY SOURCES)
            {"name": "SEC EDGAR", "func": self.get_sec_news, "category": "COMPANY"},
            {"name": "Business Wire", "func": self.get_businesswire_news, "category": "COMPANY"},

            # MACRO (PRIMARY SOURCES)
            {"name": "Federal Reserve", "func": self.get_fed_news, "category": "MACRO"},
            {"name": "BLS", "func": self.get_bls_news, "category": "MACRO"},

            # GEO / GLOBAL (PRIMARY GLOBAL SOURCE)
            {"name": "AP News", "func": self.get_ap_news, "category": "GEO"},

            # GEO / MARKETS (SECONDARY SOURCES)
            {"name": "CNBC", "func": self.get_cnbc_news, "category": "GEO"},
            {"name": "MarketWatch", "func": self.get_marketwatch_news, "category": "GEO"},
        ]

    # ==================================================
    # NEWS OBJECT ENGINE
    # ==================================================

    def create_news_object(self, title, source, url, published, category, summary=""):
        return {
            "title": title.strip(),
            "summary": summary.strip(),
            "url": url.strip(),
            "source": source,
            "published": published,
            "category": category
        }

    # ==================================================
    # RSS PARSER ENGINE
    # ==================================================

    def parse_rss_feed(self, url, source, category):

        news = []

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            root = ET.fromstring(response.content)
            channel = root.find("channel")
            if channel is None:
                return news

            for item in channel.findall("item"):

                title = item.findtext("title", default="").strip()
                link = item.findtext("link", default="").strip()
                description = item.findtext("description", default="").strip()
                pub_date = item.findtext("pubDate", default="").strip()

                if not title or not link:
                    continue

                try:
                    published = parsedate_to_datetime(pub_date).isoformat()
                except Exception:
                    published = pub_date

                news.append(
                    self.create_news_object(
                        title=title,
                        source=source,
                        url=link,
                        published=published,
                        category=category,
                        summary=description
                    )
                )

        except Exception as error:
            logging.error(f"{source} RSS Error: {error}")

        return news

    # ==================================================
    # RETRY ENGINE
    # ==================================================

    def safe_fetch(self, provider):

        name = provider["name"]
        func = provider["func"]
        category = provider["category"]

        logging.info(f"Fetching: {name}")

        # محاولة أولى
        try:
            return func(category)
        except Exception as error:
            logging.warning(f"{name} First Attempt Failed: {error}")

        # محاولة ثانية
        try:
            logging.info(f"{name} Retrying...")
            return func(category)
        except Exception as error:
            logging.error(f"{name} Failed Completely: {error}")
            return []

    # ==================================================
    # COMPANY PROVIDERS (PRIMARY)
    # ==================================================

    def get_sec_news(self, category):
        return self.parse_rss_feed(
            url="https://www.sec.gov/news/pressreleases.rss",
            source="SEC EDGAR",
            category=category
        )

    def get_businesswire_news(self, category):
        return self.parse_rss_feed(
            url="https://feeds.businesswire.com/rss/home/?rss=G1QFDERJXkJeEFZXWA==",
            source="Business Wire",
            category=category
        )

    # ==================================================
    # MACRO PROVIDERS (PRIMARY)
    # ==================================================

    def get_fed_news(self, category):
        return self.parse_rss_feed(
            url="https://www.federalreserve.gov/feeds/press_all.xml",
            source="Federal Reserve",
            category=category
        )

    def get_bls_news(self, category):
        return self.parse_rss_feed(
            url="https://www.bls.gov/feed/bls_latest.rss",
            source="BLS",
            category=category
        )

    # ==================================================
    # GEO / GLOBAL PROVIDER (PRIMARY GLOBAL SOURCE)
    # ==================================================

    def get_ap_news(self, category):
        return self.parse_rss_feed(
            url="https://apnews.com/apf-topnews?format=xml",
            source="AP News",
            category=category
        )


    # ==================================================
    # GEO / MARKETS PROVIDERS (SECONDARY)
    # ==================================================

    def get_cnbc_news(self, category):
        return self.parse_rss_feed(
            url="https://www.cnbc.com/id/100003114/device/rss/rss.html",
            source="CNBC",
            category=category
        )

    def get_marketwatch_news(self, category):
        return self.parse_rss_feed(
            url="https://www.marketwatch.com/rss/topstories",
            source="MarketWatch",
            category=category
        )

    # ==================================================
    # MAIN PROVIDER ENGINE
    # ==================================================

    def get_news(self):

        logging.info("News Provider Started...")

        all_news = []

        for provider in self.providers:
            fetched = self.safe_fetch(provider)
            all_news.extend(fetched)

        logging.info(f"News Provider Completed. Total Raw News: {len(all_news)}")

        return all_news
