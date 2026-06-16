# ==================================================
# NEWS ENGINE
# ==================================================

import random


class NewsEngine:

    def __init__(self):

        self.sources = [

            "Finnhub",

            "NewsAPI"

        ]

    # ==========================================
    # MARKET NEWS
    # ==========================================

    def get_market_news(self):

        return []

    # ==========================================
    # STOCK NEWS
    # ==========================================

    def get_stock_news(self, symbol):

        return []

    # ==========================================
    # NEWS SENTIMENT
    # ==========================================

    def get_news_sentiment(self):

        return random.choice(

            [

                "BULLISH 📈",

                "NEUTRAL ⚖️",

                "BEARISH 📉"

            ]

        )

    # ==========================================
    # HOT NEWS
    # ==========================================

    def get_hot_news(self):

        return []

    # ==========================================
    # MORNING NEWS
    # ==========================================

    def morning_news(self):

        return []

    # ==========================================
    # MIDDAY NEWS
    # ==========================================

    def midday_news(self):

        return []

    # ==========================================
    # EVENING NEWS
    # ==========================================

    def evening_news(self):

        return []


# ==================================================
# TEST
# ==================================================

if __name__ == "__main__":

    news_engine = NewsEngine()

    print(

        "📰 NEWS ENGINE READY"

    )

    