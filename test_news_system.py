# ==================================================
# IMPORTS
# ==================================================

from news.news_provider import NewsProvider
from news.news_filter import NewsFilter
from news.news_scoring import NewsScoring
from news.news_formatter import NewsFormatter
from news.news_queue import NewsQueue
from news.news_engine import NewsEngine


# ==================================================
# NEWS SYSTEM TEST
# ==================================================

def run_news_system_test():

    print("\n======================================")
    print("ADEL SMART BOT")
    print("NEWS SYSTEM TEST")
    print("======================================\n")

    provider = NewsProvider()
    news_filter = NewsFilter()
    scoring = NewsScoring()
    formatter = NewsFormatter()
    queue = NewsQueue()
    engine = NewsEngine()

    try:

        # ==================
        # PROVIDER
        # ==================

        news = provider.get_news()

        print(
            f"✅ Provider ............ PASS ({len(news)} News)"
        )

        # ==================
        # FILTER
        # ==================

        filtered_news = news_filter.filter_news(

            news

        )

        print(
            f"✅ Filter .............. PASS ({len(filtered_news)} News)"
        )

        if filtered_news:

            # ==================
            # SCORING
            # ==================

            analysis = scoring.score_news(

                filtered_news[0]

            )

            print(
                "✅ Scoring ............ PASS"
            )

            # ==================
            # FORMATTER
            # ==================

            message = formatter.format(

                filtered_news[0],

                analysis

            )

            print(
                "✅ Formatter .......... PASS"
            )

            # ==================
            # PREVIEW
            # ==================

            print("\n======================================")
            print("NEWS MESSAGE PREVIEW")
            print("======================================\n")

            print(message)

            print("\n======================================\n")

            # ==================
            # QUEUE
            # ==================

            test_news = filtered_news[0].copy()

            test_news.update(

                analysis

            )

            test_news["message"] = message

            queue.process_news(

                test_news

            )

            if queue.get_next_message():

                print(
                    "✅ Queue .............. PASS"
                )

            else:

                print(
                    "❌ Queue .............. FAIL"
                )

        else:

            print(
                "⚠️ No News After Filter"
            )

        # ==================
        # ENGINE
        # ==================

        messages = engine.process_news()

        print(
            f"✅ Engine .............. PASS ({len(messages)} Ready)"
        )

        # ==================
        # PRE MARKET
        # ==================

        pre_market = engine.morning_news()

        print(
            f"✅ Pre Market ......... PASS ({len(pre_market)} News)"
        )

        # ==================
        # BREAKING NEWS
        # ==================

        breaking = engine.breaking_news()

        print(
            f"✅ Breaking ........... PASS ({len(breaking)} News)"
        )

        # ==================
        # AFTER MARKET
        # ==================

        after_market = engine.after_market_news()

        print(
            f"✅ After Market ....... PASS ({len(after_market)} News)"
        )

        # ==================
        # READY
        # ==================

        print("\n======================================")
        print("🎉 NEWS SYSTEM READY")
        print("======================================")

    except Exception as error:

        print("\n======================================")
        print("❌ NEWS SYSTEM FAILED")
        print("======================================")

        print(error)


# ==================================================
# TEST
# ==================================================

if __name__ == "__main__":

    run_news_system_test()
    