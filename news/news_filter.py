# ==================================================
# IMPORTS
# ==================================================

from config import WATCHLIST


# ==================================================
# NEWS FILTER (ANALYTICS ENGINE)
# ==================================================

class NewsFilter:

    def __init__(self):

        # ==================
        # WATCHLIST
        # ==================
        self.watchlist = [symbol.upper() for symbol in WATCHLIST]

        # ==================
        # HIGH IMPACT EVENTS
        # ==================
        self.high_impact_events = [
            "FOMC", "FED", "FEDERAL RESERVE", "POWELL",
            "CPI", "CORE CPI", "PPI", "CORE PPI",
            "NFP", "PAYROLL", "GDP", "PCE",
            "INTEREST RATE", "RATE DECISION",
            "UNEMPLOYMENT", "INFLATION",
            "JOBS REPORT", "LABOR MARKET"
        ]

        # ==================
        # EARNINGS KEYWORDS
        # ==================
        self.earnings_keywords = [
            "EARNINGS", "EPS", "REVENUE",
            "GUIDANCE", "FORECAST", "OUTLOOK"
        ]

        # ==================
        # BREAKING KEYWORDS
        # ==================
        self.breaking_keywords = [
            "BREAKING", "URGENT", "EMERGENCY",
            "BANKRUPTCY", "MERGER", "ACQUISITION",
            "CEO", "SEC", "FDA",
            "ALERT", "JUST IN"
        ]

        # ==================
        # GEOPOLITICAL KEYWORDS
        # ==================
        self.geopolitical_keywords = [
            "SANCTIONS", "TARIFF", "TARIFFS", "TRADE WAR",
            "GEOPOLITICAL", "MILITARY", "DEFENSE", "SECURITY",
            "CONFLICT", "WAR", "ATTACK", "MISSILE", "NUCLEAR",
            "WHITE HOUSE", "CONGRESS", "TREASURY",
            "STATE DEPARTMENT", "UN", "NATO"
        ]

        # ==================
        # REGULATORY KEYWORDS (FINAL IMPROVED VERSION)
        # ==================
        self.regulatory_keywords = [
            "SYSTEMIC RISK",
            "CAPITAL REQUIREMENTS",
            "BASEL",
            "STRESS TEST",
            "AML",
            "ANTI-MONEY LAUNDERING",
            "ENFORCEMENT",
            "VIOLATION",
            "PENALTY"
        ]

        # ==================
        # SECTOR MAP
        # ==================
        self.sector_map = {
            "TECHNOLOGY": ["APPLE", "MICROSOFT", "NVIDIA", "AMD", "INTEL", "GOOGLE", "META", "AMAZON", "TESLA"],
            "SEMICONDUCTOR": ["NVIDIA", "AMD", "INTEL", "TSMC", "QUALCOMM", "BROADCOM"],
            "FINANCIAL": ["BANK", "JPMORGAN", "GOLDMAN", "MORGAN STANLEY", "CITI"],
            "ENERGY": ["OIL", "CRUDE", "OPEC", "CHEVRON", "EXXON"],
            "HEALTHCARE": ["FDA", "PFIZER", "MODERNA", "JOHNSON"],
            "MACRO": ["INFLATION", "CPI", "PPI", "GDP", "PCE", "UNEMPLOYMENT", "PAYROLL", "JOBS REPORT", "LABOR MARKET"]
        }

        # ==================
        # EVENT MAP
        # ==================
        self.event_map = {
            "CPI": ["CPI", "CORE CPI"],
            "PPI": ["PPI", "CORE PPI"],
            "NFP": ["NFP", "NONFARM", "PAYROLL", "JOBS REPORT", "LABOR MARKET", "UNEMPLOYMENT"],
            "GDP": ["GDP"],
            "PCE": ["PCE"],
            "FOMC": ["FOMC", "RATE DECISION"],
            "FED": ["FEDERAL RESERVE", "POWELL", "FED"],
            "OIL": ["CRUDE", "OIL", "OPEC"],
            "EARNINGS": ["EARNINGS", "EPS", "REVENUE"]
        }

        # ==================
        # SCORE WEIGHTS
        # ==================
        self.weights = {
            "high_impact": 40,
            "watchlist": 25,
            "sector": 10,
            "macro": 10,
            "earnings": 10,
            "breaking": 10
        }

        # ==================
        # PRIORITY LEVELS
        # ==================
        self.priority_levels = {
            "CRITICAL": 90,
            "HIGH": 70,
            "MEDIUM": 50,
            "LOW": 0
        }

        # ==================
        # IMPACT LEVELS
        # ==================
        self.impact_levels = {
            "HIGH": 80,
            "MEDIUM": 50,
            "LOW": 20
        }


    # ==================================================
    # TEXT ENGINE
    # ==================================================

    def get_text(self, news):
        title = news.get("title", "")
        summary = news.get("summary", "")
        source = news.get("source", "")
        return f"{title} {summary} {source}".upper()


    # ==================================================
    # WATCHLIST ENGINE
    # ==================================================

    def detect_watchlist(self, text):
        return [symbol for symbol in self.watchlist if symbol in text]


    # ==================================================
    # GEOPOLITICAL ENGINE
    # ==================================================

    def detect_geopolitical(self, text):
        return any(keyword in text for keyword in self.geopolitical_keywords)


    # ==================================================
    # REGULATORY ENGINE
    # ==================================================

    def detect_regulatory(self, text):
        return any(keyword in text for keyword in self.regulatory_keywords)


    # ==================================================
    # HIGH IMPACT ENGINE
    # ==================================================

    def detect_high_impact(self, text, news, watchlist):

        # أحداث اقتصادية مؤثرة
        if any(keyword in text for keyword in self.high_impact_events):
            return True

        # أحداث جيوسياسية كبيرة
        if self.detect_geopolitical(text):
            return True

        # أحداث تنظيمية ضخمة فقط (بعد التحسين الأخير)
        if self.detect_regulatory(text):
            return True

        # أحداث شركات استثنائية جدًا خارج WATCHLIST
        if not watchlist and any(k in text for k in ["BANKRUPTCY", "MERGER", "ACQUISITION"]):
            return True

        # المصدر الرسمي لا يجعل الخبر High Impact تلقائيًا
        return False


    # ==================================================
    # EARNINGS ENGINE
    # ==================================================

    def detect_earnings(self, text):
        return any(keyword in text for keyword in self.earnings_keywords)


    # ==================================================
    # BREAKING ENGINE
    # ==================================================

    def detect_breaking(self, text, event, news):

        breaking_keywords_found = any(keyword in text for keyword in self.breaking_keywords)

        urgent_events = ["CPI", "PPI", "NFP", "FOMC"]

        if breaking_keywords_found:
            return True

        if event in urgent_events:
            return True

        # جيوسياسي عاجل
        if self.detect_geopolitical(text):
            return True

        # أحداث تنظيمية ضخمة فقط (بعد التحسين الأخير)
        if self.detect_regulatory(text):
            return True

        return False


    # ==================================================
    # SECTOR ENGINE
    # ==================================================

    def detect_sector(self, text):
        for sector, keywords in self.sector_map.items():
            if any(keyword in text for keyword in keywords):
                return sector
        return None


    # ==================================================
    # EVENT ENGINE
    # ==================================================

    def detect_event(self, text):
        for event, keywords in self.event_map.items():
            if any(keyword in text for keyword in keywords):
                return event
        return None


    # ==================================================
    # AFFECTED ASSETS ENGINE
    # ==================================================

    def detect_affected_assets(self, text, watchlist):
        assets = set()

        if any(k in text for k in self.high_impact_events):
            assets.update(["SPX", "SPY", "QQQ", "USD", "GOLD"])

        if "OIL" in text or "CRUDE" in text:
            assets.update(["OIL", "USD"])

        if "GOLD" in text:
            assets.add("GOLD")

        if "TREASURY" in text or "BOND" in text or "YIELD" in text:
            assets.add("BONDS")

        if self.detect_geopolitical(text):
            assets.update(["SPX", "QQQ", "DXY", "GOLD", "OIL"])

        if watchlist:
            assets.update(["SPY", "QQQ", "SPX"])

        return sorted(assets)


    # ==================================================
    # MARKET EFFECT ENGINE
    # ==================================================

    def detect_market_effect(self, text):

        if any(k in text for k in ["CPI", "CORE CPI", "PPI", "CORE PPI", "INFLATION"]):
            return {
                "SPX": "BEARISH",
                "SPY": "BEARISH",
                "QQQ": "BEARISH",
                "USD": "BULLISH",
                "GOLD": "BEARISH"
            }

        if any(k in text for k in ["RATE HIKE", "RAISE RATES", "INTEREST RATE HIKE"]):
            return {
                "SPX": "BEARISH",
                "SPY": "BEARISH",
                "QQQ": "BEARISH",
                "USD": "BULLISH",
                "GOLD": "BEARISH"
            }

        if any(k in text for k in ["RATE CUT", "CUT RATES", "INTEREST RATE CUT"]):
            return {
                "SPX": "BULLISH",
                "SPY": "BULLISH",
                "QQQ": "BULLISH",
                "USD": "BEARISH",
                "GOLD": "BULLISH"
            }

        if any(k in text for k in ["NFP", "PAYROLL", "UNEMPLOYMENT", "JOBS REPORT", "LABOR MARKET"]):
            return {"SPX": "NEUTRAL", "USD": "NEUTRAL", "GOLD": "NEUTRAL"}

        if "GDP" in text:
            return {"SPX": "BULLISH", "USD": "BULLISH"}

        if any(k in text for k in ["OIL", "CRUDE", "OPEC"]):
            return {"OIL": "NEUTRAL", "USD": "NEUTRAL"}

        if any(k in text for k in ["TREASURY", "BOND", "YIELD"]):
            return {"SPX": "BEARISH", "USD": "BULLISH", "GOLD": "BEARISH"}

        if self.detect_geopolitical(text):
            return {
                "SPX": "BEARISH",
                "QQQ": "BEARISH",
                "DXY": "BULLISH",
                "GOLD": "BULLISH",
                "OIL": "BULLISH"
            }

        if any(k in text for k in self.earnings_keywords):
            return {"SPX": "BULLISH", "QQQ": "BULLISH"}

        return {}


    # ==================================================
    # MARKET SENTIMENT ENGINE
    # ==================================================

    def detect_market_sentiment(self, market_effect):
        bullish = sum(1 for v in market_effect.values() if v == "BULLISH")
        bearish = sum(1 for v in market_effect.values() if v == "BEARISH")

        if bullish > bearish:
            return "BULLISH"
        if bearish > bullish:
            return "BEARISH"
        return "NEUTRAL"


    # ==================================================
    # SCORE ENGINE
    # ==================================================

    def calculate_score(self, high_impact, watchlist, sector, category, earnings, breaking):
        score = 0

        if high_impact:
            score += self.weights["high_impact"]

        if watchlist:
            score += self.weights["watchlist"]

        if sector:
            score += self.weights["sector"]

        if category.upper() == "MACRO":
            score += self.weights["macro"]

        if earnings:
            score += self.weights["earnings"]

        if breaking:
            score += self.weights["breaking"]

        return min(score, 100)


    # ==================================================
    # PRIORITY ENGINE
    # ==================================================

    def detect_priority(self, score):
        if score >= self.priority_levels["CRITICAL"]:
            return "CRITICAL"
        if score >= self.priority_levels["HIGH"]:
            return "HIGH"
        if score >= self.priority_levels["MEDIUM"]:
            return "MEDIUM"
        return "LOW"


    # ==================================================
    # IMPACT ENGINE
    # ==================================================

    def detect_impact(self, score):
        if score >= self.impact_levels["HIGH"]:
            return "HIGH"
        if score >= self.impact_levels["MEDIUM"]:
            return "MEDIUM"
        return "LOW"


    # ==================================================
    # RISK ENGINE
    # ==================================================

    def detect_risk(self, score):
        return self.detect_impact(score)


    # ==================================================
    # CLASSIFICATION ENGINE
    # ==================================================

    def classify(self, news):

        text = self.get_text(news)

        watchlist_symbols = self.detect_watchlist(text)
        watchlist = bool(watchlist_symbols)

        high_impact = self.detect_high_impact(text, news, watchlist)
        earnings = self.detect_earnings(text)
        sector = self.detect_sector(text)
        event = self.detect_event(text)

        breaking = self.detect_breaking(text, event, news)

        affected_assets = self.detect_affected_assets(text, watchlist)
        market_effect = self.detect_market_effect(text)
        sentiment = self.detect_market_sentiment(market_effect)

        score = self.calculate_score(
            high_impact,
            watchlist,
            sector,
            news.get("category", ""),
            earnings,
            breaking
        )

        priority = self.detect_priority(score)
        impact = self.detect_impact(score)
        risk = self.detect_risk(score)

        classified = dict(news)
        classified.update({
            "watchlist": watchlist,
            "watchlist_symbols": watchlist_symbols,
            "high_impact": high_impact,
            "earnings": earnings,
            "breaking": breaking,
            "sector": sector,
            "event": event,
            "affected_assets": affected_assets,
            "market_effect": market_effect,
            "sentiment": sentiment,
            "score": score,
            "priority": priority,
            "impact": impact,
            "risk": risk
        })

        return classified


    # ==================================================
    # IMPORTANT NEWS ENGINE
    # ==================================================

    def is_important(self, news):
        return (
            news.get("breaking") or
            news.get("high_impact") or
            news.get("earnings") or
            news.get("watchlist")
        )


    # ==================================================
    # FILTER ENGINE
    # ==================================================

    def classify_news_list(self, news_list):
        return [self.classify(news) for news in news_list]

    def filter_high_impact_news(self, news_list):
        return [news for news in news_list if news.get("high_impact")]

    def filter_company_news(self, news_list):
        return [news for news in news_list if news.get("category") == "COMPANY"]

    def filter_macro_news(self, news_list):
        return [news for news in news_list if news.get("category") == "MACRO"]

    def filter_watchlist_news(self, news_list):
        return [news for news in news_list if news.get("watchlist")]

    def filter_important_news(self, news_list):
        return [news for news in news_list if self.is_important(news)]
