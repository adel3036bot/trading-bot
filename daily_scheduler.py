# ============================================================
# ADEL SMART BOT ELITE
# DAILY SCHEDULER — FINAL OPERATIONAL VERSION
# ============================================================

from datetime import datetime, time
from zoneinfo import ZoneInfo
import contextlib
import concurrent.futures
import io
import threading
import time as _runtime_time
from telegram_bot.telegram_engine import TelegramEngine
from news.news_engine import NewsEngine
from performance_engine import PerformanceEngine

try:
    from images.image_engine import ImageEngine
except Exception:
    ImageEngine = None


# ============================================================
# DAILY SCHEDULER
# ============================================================

class DailyScheduler:

    def __init__(self, telegram=None, news_engine=None):

        # ----------------------------------------------------
        # CORE ENGINES
        # ----------------------------------------------------
        # Inject shared process engines when available.  Keeping the defaults
        # preserves direct Scheduler use in existing tests and scripts.
        self.telegram = telegram or TelegramEngine()
        self.news_engine = news_engine or NewsEngine()
        self.performance = PerformanceEngine(journal=getattr(self.news_engine, "journal", None))
        self.market_timezone = ZoneInfo("America/New_York")
        self.display_timezone = ZoneInfo("Asia/Riyadh")

        # ----------------------------------------------------
        # IMAGE ENGINE
        # Image failure must NEVER stop the bot.
        # ----------------------------------------------------
        self.image_engine = None

        if ImageEngine is not None:
            try:
                self.image_engine = ImageEngine()
                print("✅ IMAGE ENGINE READY")
            except Exception as e:
                print(f"⚠️ IMAGE ENGINE DISABLED: {e}")
                self.image_engine = None

        # ----------------------------------------------------
        # DAILY FLAGS
        # ----------------------------------------------------
        self.morning_report_sent = False
        self.morning_news_sent = False
        self.full_pre_market_sent = False
        self.evening_report_sent = False
        self.market_open_sent = False

        self.last_reset_date = None

        # ----------------------------------------------------
        # ASYNC TASK STATE
        # Scheduler must never block AdelSmartBot main loop.
        # ----------------------------------------------------
        self._task_lock = threading.Lock()
        self._tasks_running = {
            "morning_report": False,
            "full_pre_market": False,
            "pre_market_status": False,
            "evening_report": False,
            "sleep_collection": False,
        }

        self._last_sleep_collection = None
        self._sleep_collection_interval = 20 * 60

        # ----------------------------------------------------
        # ONE-TIME PRE-MARKET PREPARATION / OPEN WARMUP
        # ----------------------------------------------------
        self._premarket_preparation_done = False
        self._market_open_warmup_started = False

        # ----------------------------------------------------
        # PRE-MARKET PREPARATION CACHE
        # 14:30 performs internal lightweight preparation only.
        # No Telegram report and no options/contracts are sent.
        # ----------------------------------------------------
        self._premarket_lock = threading.Lock()
        self._premarket_cache = {
            "opportunities": [],
            "candidates": 0,
            "rejected": 0,
            "analyzed": 0,
            "available": False,
            "timed_out": False,
            "timestamp": 0.0,
        }

        # ----------------------------------------------------
        # SLEEP DATA CACHE
        # ----------------------------------------------------
        self.sleep_data = {
            "macro": [],
            "company": [],
            "earnings": [],
            "events": []
        }

    # ========================================================
    # ASYNC / NON-BLOCKING HELPERS
    # ========================================================

    def _start_async_task(self, task_name, target):
        """Start one daemon task only if the same task is not running."""
        with self._task_lock:
            if self._tasks_running.get(task_name, False):
                return False
            self._tasks_running[task_name] = True

        def runner():
            try:
                target()
            except Exception as e:
                print(f"⚠️ ASYNC TASK ERROR [{task_name}]: {e}")
            finally:
                with self._task_lock:
                    self._tasks_running[task_name] = False

        threading.Thread(
            target=runner,
            name=f"ADEL-{task_name}",
            daemon=True
        ).start()

        return True

    def _run_safely_with_timeout(self, target, timeout, default=None):
        """Run a blocking provider call in a daemon thread with a hard wait limit."""
        result = {"value": default}

        def runner():
            try:
                result["value"] = target()
            except Exception as e:
                result["error"] = e

        thread = threading.Thread(
            target=runner,
            name="ADEL-provider-call",
            daemon=True
        )
        thread.start()
        thread.join(max(0.1, timeout))

        return result.get("value", default)

    def _quiet_call(self, target, default=None):
        """Suppress extremely verbose engine diagnostics during background pre-market scans."""
        buffer = io.StringIO()
        try:
            with contextlib.redirect_stdout(buffer):
                return target()
        except Exception:
            return default

    # ========================================================
    # SAFE TEXT SENDER
    # ========================================================

    def send_text_safe(self, text, *, destination=None):

        if not text:
            print("⚠️ EMPTY TEXT")
            return False

        try:
            return bool(self.telegram.send_message(text, destination=destination))
        except Exception as e:
            print(f"❌ TELEGRAM TEXT SEND ERROR: {e}")
            return False

    # ========================================================
    # UNIFIED STRUCTURED SENDER
    # IMAGE → TEXT FALLBACK
    # ========================================================

    def send_structured(self, data, message_type="report"):

        if not data:
            print("⚠️ EMPTY STRUCTURED DATA")
            return False

        if not isinstance(data, dict):
            print("⚠️ INVALID STRUCTURED DATA")
            return False

        template = data.get("template")
        image_data = data.get("image_data")
        text = data.get("text", "")
        raw_news = data.get("raw") if message_type == "news" else None
        destination = None
        if message_type == "news" and hasattr(self.telegram, "news_destination"):
            try:
                destination = self.telegram.news_destination()
            except Exception as error:
                print(f"⚠️ NEWS ROUTE LOOKUP FAILED: {error}")

        def finish(result, failure_reason=None):
            success = bool(result)
            if raw_news:
                try:
                    if success:
                        self.news_engine.mark_as_sent(raw_news, destination=destination or "DEFAULT")
                    else:
                        self.news_engine.record_delivery_failure(raw_news, destination=destination or "DEFAULT", reason=failure_reason or "news_delivery_failed")
                except Exception as error:
                    print(f"⚠️ NEWS DELIVERY JOURNAL ERROR: {error}")
            return success

        if not text:
            print("⚠️ STRUCTURED MESSAGE HAS NO TEXT")

        # ----------------------------------------------------
        # No template
        # ----------------------------------------------------
        if not template:
            print("⚠️ MISSING TEMPLATE → TEXT ONLY")
            return finish(self.send_text_safe(text, destination=destination), "missing_template")

        # ----------------------------------------------------
        # No image data
        # ----------------------------------------------------
        if image_data is None:
            print("⚠️ MISSING IMAGE DATA → TEXT ONLY")
            return finish(self.send_text_safe(text, destination=destination), "missing_image_data")

        # ----------------------------------------------------
        # Image engine unavailable
        # ----------------------------------------------------
        if self.image_engine is None:
            print("⚠️ IMAGE ENGINE UNAVAILABLE → TEXT ONLY")
            return finish(self.send_text_safe(text, destination=destination), "image_engine_unavailable")

        # ----------------------------------------------------
        # Generate image
        # ----------------------------------------------------
        try:
            image_path = self.image_engine.build_image(
                template,
                image_data
            )

            if not image_path:
                print("⚠️ IMAGE NOT GENERATED → TEXT ONLY")
                return finish(self.send_text_safe(text, destination=destination), "image_not_generated")

        except Exception as e:
            print(f"⚠️ IMAGE GENERATION FAILED: {e}")
            return finish(self.send_text_safe(text, destination=destination), "image_generation_failed")

        # ----------------------------------------------------
        # Send image through current TelegramEngine API
        # ----------------------------------------------------
        try:

            if message_type == "news":

                if hasattr(
                    self.telegram,
                    "send_news_with_image"
                ):
                    result = self.telegram.send_news_with_image(image_path, text, destination=destination)
                    return finish(True if result is None else bool(result), "news_image_delivery_failed")

            else:

                if hasattr(
                    self.telegram,
                    "send_report_with_image"
                ):
                    result = self.telegram.send_report_with_image(
                        image_path,
                        text
                    )
                    return True if result is None else bool(result)

            # ------------------------------------------------
            # Final fallback
            # ------------------------------------------------
            print(
                "⚠️ IMAGE SEND METHOD UNAVAILABLE "
                "→ TEXT ONLY"
            )

            return finish(self.send_text_safe(text, destination=destination), "news_send_method_unavailable")

        except Exception as e:

            print(
                f"⚠️ IMAGE SEND FAILED: {e}"
            )

            return finish(self.send_text_safe(text, destination=destination), "image_send_failed")

    # ========================================================
    # MARKET HOURS — SAUDI TIME
    # ========================================================

    def is_morning_report_time(self):
        now = datetime.now(self.display_timezone).time()

        return (
            time(10, 0)
            <= now
            <
            time(10, 30)
        )

    # --------------------------------------------------------

    def is_full_pre_market(self):

        now = datetime.now(self.display_timezone).time()

        return (
            time(14, 30)
            <= now
            <
            time(15, 30)
        )

    # --------------------------------------------------------

    def is_pre_market(self):

        now = datetime.now(self.display_timezone).time()

        return (
            time(15, 30)
            <= now
            <
            time(16, 30)
        )

    # --------------------------------------------------------

    def is_market_open(self):

        now = datetime.now(self.display_timezone).time()

        return (
            time(16, 30)
            <= now
            <
            time(23, 0)
        )

    # --------------------------------------------------------

    def is_after_market(self):

        now = datetime.now(self.display_timezone).time()

        return (
            now >= time(23, 0)
            or
            now < time(0, 30)
        )

    # --------------------------------------------------------

    def is_sleep_time(self):

        now = datetime.now(self.display_timezone).time()

        return (
            (
                time(0, 30)
                <= now
                <
                time(10, 0)
            )
            or
            (
                time(10, 30)
                <= now
                <
                time(14, 30)
            )
        )

    # ========================================================
    # OPERATIONAL DAY RESET
    # ========================================================

    def reset_daily_flags(self):

        now = datetime.now(self.display_timezone)

        # 00:00–00:30 belongs to previous operational day.
        if now.time() >= time(0, 30):

            operational_date = now.date()

        else:

            operational_date = (
                now.date().fromordinal(
                    now.date().toordinal() - 1
                )
            )

        if self.last_reset_date == operational_date:
            return

        self.last_reset_date = operational_date

        self.morning_report_sent = False
        self.morning_news_sent = False
        self.full_pre_market_sent = False
        self.evening_report_sent = False
        self.market_open_sent = False

        self._premarket_preparation_done = False
        self._market_open_warmup_started = False

        self.sleep_data = {
            "macro": [],
            "company": [],
            "earnings": [],
            "events": []
        }

        self._last_sleep_collection = None

        

    # ========================================================
    # SLEEP DATA COLLECTION
    # ========================================================

    def collect_sleep_data(self):

        now = _runtime_time.monotonic()

        # Prevent the scheduler loop from refetching all providers every cycle.
        if (
            self._last_sleep_collection is not None
            and now - self._last_sleep_collection < self._sleep_collection_interval
        ):
            return False

        with self._task_lock:
            if self._tasks_running.get("sleep_collection", False):
                return False
            self._tasks_running["sleep_collection"] = True

        self._last_sleep_collection = now

        def background_collection():
            try:
                print("😴 SLEEP MODE: COLLECTING BACKGROUND DATA...")
                self._collect_sleep_data_sync()
            finally:
                with self._task_lock:
                    self._tasks_running["sleep_collection"] = False

        threading.Thread(
            target=background_collection,
            name="ADEL-sleep-collection",
            daemon=True
        ).start()

        return True

    def _collect_sleep_data_sync(self):

        try:

            # ------------------------------------------------
            # Preferred current NewsEngine path
            # ------------------------------------------------

            if not hasattr(
                self.news_engine,
                "fetch_news"
            ):
                print(
                    "⚠️ NewsEngine.fetch_news() unavailable"
                )
                return

            raw = self.news_engine.fetch_news()

            if not raw:
                print("⚠️ NO RAW NEWS")
                return

            classified = self.news_engine.classify_news(
                raw
            )

            if not classified:
                print("⚠️ NO CLASSIFIED NEWS")
                return

            important = self.news_engine.filter_important(
                classified
            )

            if not important:
                print("⚠️ NO IMPORTANT NEWS")
                return

            # ------------------------------------------------
            # Categorize
            # ------------------------------------------------

            for item in important:

                if not isinstance(item, dict):
                    continue

                category = str(
                    item.get("category", "")
                ).upper()

                session = str(
                    item.get("session", "")
                ).upper()

                text = item.get(
                    "title"
                ) or item.get(
                    "headline"
                ) or item.get(
                    "text"
                )

                if not text:
                    continue

                if "EARNING" in category:
                    self.sleep_data["earnings"].append(
                        text
                    )

                elif (
                    "COMPANY" in category
                    or
                    "CORPORATE" in category
                    or
                    "STOCK" in category
                ):
                    self.sleep_data["company"].append(
                        text
                    )

                elif (
                    "EVENT" in category
                    or
                    "GEO" in category
                    or
                    "POLITICAL" in category
                ):
                    self.sleep_data["events"].append(
                        text
                    )

                else:
                    self.sleep_data["macro"].append(
                        text
                    )

            print("✅ SLEEP DATA UPDATED")

        except Exception as e:

            print(
                f"⚠️ SLEEP DATA ERROR: {e}"
            )

    # ========================================================
    # HELPER — FORMAT PRE-MARKET REPORT
    # ========================================================

    def _build_pre_market_report(self):

        macro = list(
            self.sleep_data.get(
                "macro", []
            )
        )

        company = list(
            self.sleep_data.get(
                "company", []
            )
        )

        earnings = list(
            self.sleep_data.get(
                "earnings", []
            )
        )

        events = list(
            self.sleep_data.get(
                "events", []
            )
        )

        # ----------------------------------------------------
        # Use the background cache collected during sleep mode.
        # No provider refresh is performed here, so the 14:30
        # report cannot block the main bot on a slow source.
        # ----------------------------------------------------

        # ----------------------------------------------------
        # Existing formatter
        # ----------------------------------------------------

        formatter = getattr(
            self.news_engine,
            "formatter",
            None
        )

        if formatter is None:

            return {
                "template": "daily_report",
                "image_data": {
                    "title": "📊 تقرير ما قبل الافتتاح",
                    "date": datetime.now().strftime(
                        "%Y-%m-%d"
                    ),
                    "summary": (
                        "تقرير ما قبل الافتتاح"
                    )
                },
                "text": (
                    "📊 تقرير ما قبل الافتتاح\n\n"
                    "لا توجد بيانات كافية حاليًا."
                )
            }

        # ----------------------------------------------------
        # Use the EXISTING formatter method.
        #
        # Important:
        # build_pre_market_report() currently exists,
        # while build_full_pre_market_report() was not
        # consistently available.
        # ----------------------------------------------------

        try:

            text = formatter.build_pre_market_report(
                macro_news=macro,
                company_news=company,
                earnings_news=earnings,
                economic_calendar=events
            )

        except TypeError:

            # Compatibility with positional-only variants.

            try:

                text = formatter.build_pre_market_report(
                    macro,
                    company,
                    earnings,
                    events
                )

            except Exception as e:

                print(
                    f"⚠️ PRE-MARKET FORMAT ERROR: {e}"
                )

                text = ""

        except Exception as e:

            print(
                f"⚠️ PRE-MARKET FORMAT ERROR: {e}"
            )

            text = ""

        # ----------------------------------------------------
        # THE IMPORTANT FIX
        #
        # Current formatter's pre-market header is:
        # "🌅 التقرير الصباحي"
        #
        # Replace ONLY that header here so we do not touch
        # news_formatter.py.
        # ----------------------------------------------------

        if text:

            replacements = [

                (
                    "🌅 التقرير الصباحي",
                    "📊 تقرير ما قبل الافتتاح"
                ),

                (
                    "🌅 التقرير الصباحي ",
                    "📊 تقرير ما قبل الافتتاح "
                ),

                (
                    "التقرير الصباحي",
                    "تقرير ما قبل الافتتاح"
                )
            ]

            for old, new in replacements:

                if old in text:

                    text = text.replace(
                        old,
                        new,
                        1
                    )

                    break

        # ----------------------------------------------------
        # Absolute fallback
        # ----------------------------------------------------

        if not text:

            sections = [
                "📊 تقرير ما قبل الافتتاح",
                "",
                f"📅 {datetime.now().strftime('%Y-%m-%d')}",
                ""
            ]

            if macro:

                sections.append(
                    "🌍 الأخبار الاقتصادية"
                )

                sections.extend(
                    f"• {x}"
                    for x in macro
                )

            if company:

                sections.append(
                    "\n🏢 أخبار الشركات"
                )

                sections.extend(
                    f"• {x}"
                    for x in company
                )

            if earnings:

                sections.append(
                    "\n💰 أرباح الشركات"
                )

                sections.extend(
                    f"• {x}"
                    for x in earnings
                )

            if events:

                sections.append(
                    "\n📅 الأحداث"
                )

                sections.extend(
                    f"• {x}"
                    for x in events
                )

            text = "\n".join(sections)

        # ----------------------------------------------------
        # Structured payload
        # ----------------------------------------------------

        image_data = {
            "title": "📊 تقرير ما قبل الافتتاح",
            "date": datetime.now().strftime(
                "%Y-%m-%d"
            ),
            # Pre-market has no completed-session performance yet.  Omit
            # unavailable values rather than rendering zero as a real result.
            "total_trades": None,
            "win_rate": None,
            "best_trade": None,
            "worst_trade": None,
            "total_profit": None,
            "total_loss": None,
            "summary": (
                "تقرير ما قبل الافتتاح "
                "قبل بدء جلسة التداول."
            ),

            # Additional data preserved for engines
            "macro": macro,
            "company": company,
            "earnings": earnings,
            "events": events,
            "session": "FULL_PRE_MARKET"
        }

        return {
            "template": "daily_report",
            "image_data": image_data,
            "text": text
        }

    # ========================================================
    # MORNING REPORT — 10:00
    # ========================================================

    def send_morning_report(self):

        if self.morning_report_sent:
            return True

        return self._start_async_task(
            "morning_report",
            self._send_morning_report_sync
        )

    def _send_morning_report_sync(self):

        if self.morning_report_sent:
            return True

        print(
            "🌅 SENDING MORNING REPORT"
        )

        try:

            # 10:00 uses the same formatter method that is actually
            # implemented in the current NewsFormatter.
            # No call is made to the incompatible
            # NewsEngine.build_morning_report_structured().
            data = self._build_pre_market_report()

            if not isinstance(data, dict):
                return False

            text = data.get("text", "")

            if text:
                text = text.replace(
                    "📊 تقرير ما قبل الافتتاح",
                    "🌅 التقرير الصباحي",
                    1
                )
                data["text"] = text

            image_data = data.setdefault(
                "image_data",
                {}
            )
            image_data["title"] = "🌅 التقرير الصباحي"
            image_data["session"] = "MORNING"

            success = self.send_structured(
                data,
                message_type="report"
            )

            if success:
                self.morning_report_sent = True

            return success

        except Exception as e:

            print(
                f"❌ MORNING REPORT ERROR: {e}"
            )

            return False

    # ========================================================
    # DETAILED PRE-MARKET NEWS — 15:30
    #
    # No stock signal scanning is triggered because run()
    # returns SLEEP in this period.
    # ========================================================


    def _scan_premarket_opportunities(self):
        """
        Lightweight pre-market screening.

        IMPORTANT:
        - Does NOT call create_trade().
        - Does NOT query option chains.
        - Does NOT generate CALL/PUT contracts.
        - Uses the existing trend + score engines only.
        - Runs the expensive symbol work concurrently and is bounded by time.

        Full contract construction remains exclusively in the normal
        market-open pipeline inside AdelSmartBot.py.
        """
        result = {
            "opportunities": [],
            "candidates": 0,
            "rejected": 0,
            "analyzed": 0,
            "available": False,
            "timed_out": False,
        }

        try:
            import sys

            main_module = sys.modules.get("__main__")
            if main_module is None:
                return result

            required = (
                "WATCHLIST",
                "get_trend",
                "get_signal_score",
            )

            if not all(hasattr(main_module, name) for name in required):
                print("⚠️ PRE-MARKET LIGHT SCAN NOT AVAILABLE")
                return result

            watchlist = getattr(main_module, "WATCHLIST")
            categories = (
                "INDICES",
                "ETFS",
                "STOCKS",
                "ENERGY",
                "GOLD",
                "BITCOIN",
            )

            symbols = []
            seen = set()

            for category in categories:

                for symbol in watchlist.get(
                    category,
                    []
                ) or []:

                    symbol = str(
                        symbol
                    ).strip()

                    if symbol and symbol not in seen:

                        seen.add(symbol)

                        symbols.append(symbol)

            if not symbols:
                return result

            result["available"] = True
            result["candidates"] = len(symbols)

            def analyze(symbol):

                # Suppress the very verbose score-engine console output.
                def work():

                    signal_type = (
                        main_module.get_trend(
                            symbol
                        )
                    )

                    score_data = (
                        main_module.get_signal_score(
                            symbol
                        )
                    )

                    if not isinstance(
                        score_data,
                        dict
                    ):
                        return None

                    confidence = score_data.get(
                        "confidence",
                        "NO TRADE"
                    )

                    score = score_data.get(
                        "score",
                        0
                    )

                    if confidence == "NO TRADE":
                        return None

                    try:
                        numeric_score = float(
                            score
                        )
                    except Exception:
                        numeric_score = 0.0

                    return {

                        "symbol":
                            symbol,

                        "signal_type":
                            signal_type,

                        "score":
                            numeric_score,

                        "confidence":
                            confidence,

                        # Contract is intentionally unresolved before open.
                        "contract_rating":
                            "PRE_MARKET_PENDING",

                        "approval":
                            "PRE_MARKET",

                        "trade_type":
                            "Pre-Market Analysis",

                        "status":
                            "WATCH",
                    }

                try:

                    return work()

                except Exception:

                    return None

            max_workers = min(
                6,
                max(
                    1,
                    len(symbols)
                )
            )

            executor = (
                concurrent.futures
                .ThreadPoolExecutor(
                    max_workers=max_workers,
                    thread_name_prefix="ADEL-premarket"
                )
            )

            futures = {
                executor.submit(
                    analyze,
                    symbol
                ): symbol
                for symbol in symbols
            }

            # Hard ceiling for pre-market analysis.
            timeout_seconds = 8.0

            deadline = (
                _runtime_time.monotonic()
                +
                timeout_seconds
            )

            try:

                for future in (
                    concurrent.futures.as_completed(
                        futures,
                        timeout=timeout_seconds
                    )
                ):

                    remaining = max(
                        0.1,
                        deadline
                        -
                        _runtime_time.monotonic()
                    )

                    if remaining <= 0:
                        break

                    try:

                        trade = future.result(
                            timeout=remaining
                        )

                    except Exception:

                        trade = None

                    if not trade:
                        continue

                    result["analyzed"] += 1

                    # Pre-market opportunity filter:
                    # actual score/confidence is dynamic; contracts are not.
                    if (
                        trade["confidence"]
                        in
                        ("A+", "A", "B+")
                        and
                        trade["score"] >= 80
                    ):

                        result[
                            "opportunities"
                        ].append(
                            trade
                        )

                    else:

                        result[
                            "rejected"
                        ] += 1

            except concurrent.futures.TimeoutError:

                result[
                    "timed_out"
                ] = True

                print(
                    "⏱️ PRE-MARKET LIGHT SCAN TIME LIMIT REACHED"
                )

            # Never wait for slow network providers.
            executor.shutdown(
                wait=False,
                cancel_futures=True
            )

            result[
                "opportunities"
            ] = sorted(
                result[
                    "opportunities"
                ],
                key=lambda x: x.get(
                    "score",
                    0
                ),
                reverse=True
            )[:5]

            return result

        except Exception as e:

            print(
                f"⚠️ PRE-MARKET LIGHT SCAN ERROR: {e}"
            )

            return result

    # ========================================================
    # PRE-MARKET STATUS — 15:30
    #
    # ALWAYS SEND A DYNAMIC STATUS.
    # News and opportunities remain separate sections.
    # No trading signal is emitted from this method.
    # ========================================================

    def send_morning_news(self):

        if self.morning_news_sent:
            return True

        # Do not block AdelSmartBot while news/providers are working.
        if self._tasks_running.get(
            "pre_market_status",
            False
        ):
            return True

        def worker():

            print(
                "📰 SENDING PRE-MARKET STATUS"
            )

            try:

                news_result = {
                    "messages": []
                }

                scan_result = {
                    "opportunities": [],
                    "candidates": 0,
                    "rejected": 0,
                    "analyzed": 0,
                    "available": False,
                    "timed_out": False,
                }

                # News and opportunity analysis run in parallel.
                def fetch_news():

                    try:

                        news_result[
                            "messages"
                        ] = (
                            self.news_engine
                            .morning_news_structured()
                            or []
                        )

                    except Exception as e:

                        news_result[
                            "error"
                        ] = e

                        news_result[
                            "messages"
                        ] = []

                news_thread = threading.Thread(
                    target=fetch_news,
                    name="ADEL-premarket-news",
                    daemon=True
                )

                news_thread.start()

                # Reuse the internal 14:30 preparation when it is ready.
                # If it is not ready, perform one bounded lightweight scan
                # in parallel so the report remains dynamic.

                cached_scan = (
                    self._get_premarket_cached_scan()
                )

                scan_thread = None

                if cached_scan.get(
                    "available"
                ):

                    scan_result.update(
                        cached_scan
                    )

                else:

                    scan_thread = threading.Thread(
                        target=lambda:
                        scan_result.update(
                            self._scan_premarket_opportunities()
                        ),
                        name="ADEL-premarket-analysis",
                        daemon=True
                    )

                    scan_thread.start()

                # Never allow a news/provider call to block the main bot.
                news_thread.join(
                    22.0
                )

                if scan_thread is not None:

                    scan_thread.join(
                        8.0
                    )

                messages = (
                    news_result.get(
                        "messages",
                        []
                    )
                )

                opportunities = (
                    scan_result.get(
                        "opportunities",
                        []
                    )
                )

                candidates = (
                    scan_result.get(
                        "candidates",
                        0
                    )
                )

                rejected = (
                    scan_result.get(
                        "rejected",
                        0
                    )
                )

                analyzed = (
                    scan_result.get(
                        "analyzed",
                        0
                    )
                )

                # ------------------------------------------------
                # NEWS SECTION
                # ------------------------------------------------

                news_lines = [
                    "📰 الأخبار المؤثرة"
                ]

                news_index = 0

                for news in messages:

                    if not isinstance(
                        news,
                        dict
                    ):
                        continue

                    text = (
                        news.get(
                            "text"
                        )
                        or
                        news.get(
                            "message"
                        )
                        or
                        ""
                    ).strip()

                    if not text:
                        continue

                    news_index += 1

                    news_lines.append(
                        f"\n{news_index}. {text}"
                    )

                if news_index == 0:

                    news_lines.append(
                        "\nلا توجد أخبار مؤثرة جديدة حاليًا."
                    )

                # ------------------------------------------------
                # OPPORTUNITIES SECTION
                # ------------------------------------------------

                opportunity_lines = [
                    "📈 فرص التداول"
                ]

                if opportunities:

                    opportunity_lines.append(
                        "\n✅ نتائج التحليل الأولي الديناميكي:"
                    )

                    for trade in opportunities:

                        symbol = trade.get(
                            "symbol",
                            "UNKNOWN"
                        )

                        score = trade.get(
                            "score",
                            "—"
                        )

                        confidence = trade.get(
                            "confidence",
                            "—"
                        )

                        opportunity_lines.append(
                            f"\n• {symbol} | "
                            f"Score: {score} | "
                            f"Confidence: {confidence}"
                        )

                    opportunity_lines.append(
                        "\nℹ️ هذه نتائج تحليل ما قبل الافتتاح فقط. "
                        "لا يتم إصدار CALL/PUT أو عقد قبل افتتاح السوق."
                    )

                elif (
                    scan_result.get(
                        "available"
                    )
                    and
                    analyzed > 0
                ):

                    opportunity_lines.append(
                        "\n🟡 تم فحص المرشحين ديناميكيًا، "
                        "لكن لم يصل أي مرشح إلى شروط الفرصة الحالية."
                    )

                    opportunity_lines.append(
                        f"\nالمرشحون: {candidates} | "
                        f"تم تحليلهم: {analyzed} | "
                        f"غير مؤهلين: {rejected}"
                    )

                elif scan_result.get(
                    "available"
                ):

                    opportunity_lines.append(
                        "\n🟡 بدأ الفحص الديناميكي، "
                        "لكن بيانات بعض المزودين لم تكتمل ضمن المهلة."
                    )

                else:

                    opportunity_lines.append(
                        "\n⚠️ مسار تحليل الفرص غير متاح حاليًا."
                    )

                # ------------------------------------------------
                # STATUS
                # ------------------------------------------------

                status_section = (
                    "⏳ حالة السوق\n"
                    "السوق لم يفتتح بعد.\n"
                    "✅ التحليل والمراقبة مستمران حتى الافتتاح."
                )

                report_text = (
                    "📊 تقرير ما قبل الافتتاح\n\n"
                    +
                    "\n".join(
                        news_lines
                    )
                    +
                    "\n\n"
                    +
                    "\n".join(
                        opportunity_lines
                    )
                    +
                    "\n\n"
                    +
                    status_section
                )

                report_data = {

                    "template":
                        "daily_report",

                    "image_data": {

                        "title":
                            "📊 تقرير ما قبل الافتتاح",

                        "date":
                            datetime.now().strftime(
                                "%Y-%m-%d"
                            ),

                        "total_trades":
                            len(
                                opportunities
                            ),

                        "win_rate":
                            0,

                        "best_trade":
                            (
                                opportunities[0].get(
                                    "symbol",
                                    ""
                                )
                                if opportunities
                                else ""
                            ),

                        "worst_trade":
                            "",

                        "total_profit":
                            0,

                        "total_loss":
                            0,

                        "summary":
                            (
                                "تقرير ديناميكي يجمع "
                                "الأخبار ونتيجة الفحص "
                                "الأولي قبل افتتاح السوق."
                            ),

                        "opportunities":
                            opportunities,

                        "candidate_count":
                            candidates,

                        "rejected_count":
                            rejected,

                        "analyzed_count":
                            analyzed,

                        "session":
                            "PRE_MARKET"
                    },

                    "text":
                        report_text
                }

                success = (
                    self.send_structured(
                        report_data,
                        message_type="report"
                    )
                )

                if success:

                    self.morning_news_sent = True

                    for news in messages:

                        if not isinstance(
                            news,
                            dict
                        ):
                            continue

                        try:

                            self.news_engine.mark_as_sent(
                                news.get(
                                    "raw"
                                )
                            )

                        except Exception:

                            pass

            except Exception as e:

                print(
                    f"❌ PRE-MARKET STATUS ERROR: {e}"
                )

                fallback = (
                    "📊 تقرير ما قبل الافتتاح\n\n"
                    "📰 الأخبار المؤثرة:\n"
                    "تعذر الحصول على تحديث الأخبار حاليًا.\n\n"
                    "📈 فرص التداول:\n"
                    "تعذر إكمال الفحص الأولي حاليًا.\n\n"
                    "⏳ حالة السوق:\n"
                    "السوق لم يفتتح بعد.\n\n"
                    "✅ النظام مستمر في العمل حتى افتتاح السوق."
                )

                if self.send_text_safe(
                    fallback
                ):

                    self.morning_news_sent = True

        return self._start_async_task(
            "pre_market_status",
            worker
        )

    # ========================================================
    # PRE-MARKET INTERNAL PREPARATION — 14:30
    #
    # IMPORTANT:
    # 14:30 is NOT a Telegram report.
    # It is an internal preparation window only.
    # We perform a lightweight dynamic market scan and cache
    # the result for the 15:30 pre-market status report.
    # No options/contract lookup and no CALL/PUT are allowed.
    # ========================================================

    def start_premarket_preparation(self):

        if self._premarket_preparation_done:
            return True

        if self._tasks_running.get(
            "full_pre_market",
            False
        ):
            return True

        def worker():

            print(
                "🧠 PRE-MARKET PREPARATION STARTED"
            )

            try:

                scan = (
                    self._scan_premarket_opportunities()
                )

                with self._premarket_lock:

                    self._premarket_cache = {
                        **scan,
                        "timestamp":
                            _runtime_time.monotonic(),
                    }

                self._premarket_preparation_done = True

                print(
                    "✅ PRE-MARKET PREPARATION COMPLETE | "
                    f"Qualified: "
                    f"{len(scan.get('opportunities', []))} | "
                    f"Analyzed: "
                    f"{scan.get('analyzed', 0)}"
                )

            except Exception as e:

                print(
                    f"⚠️ PRE-MARKET PREPARATION ERROR: {e}"
                )

        return self._start_async_task(
            "full_pre_market",
            worker
        )

    def _get_premarket_cached_scan(self):

        with self._premarket_lock:

            cache = dict(
                self._premarket_cache
            )

        timestamp = cache.get(
            "timestamp",
            0.0
        )

        # Cache is valid for the same pre-market cycle only.
        if timestamp > 0:

            age = (
                _runtime_time.monotonic()
                -
                timestamp
            )

            if age <= 70 * 60:

                return cache

        return {
            "opportunities": [],
            "candidates": 0,
            "rejected": 0,
            "analyzed": 0,
            "available": False,
            "timed_out": False,
            "timestamp": 0.0,
        }

    # ========================================================
    # MARKET OPEN CACHE WARMUP
    # ========================================================

    def _warm_market_cache_before_open(self):
        """
        Warm the existing market cache before 16:30.
        Runs in the background and never creates trades or options.
        """

        if self._market_open_warmup_started:
            return True

        self._market_open_warmup_started = True

        def worker():
            try:
                import sys

                main_module = sys.modules.get("__main__")
                if main_module is None:
                    return

                get_cached_market = getattr(
                    main_module,
                    "get_cached_market",
                    None
                )

                if not callable(get_cached_market):
                    return

                print(
                    "🔥 PRE-OPEN MARKET CACHE WARMUP STARTED"
                )

                try:
                    get_cached_market()
                    print(
                        "✅ PRE-OPEN MARKET CACHE WARMUP COMPLETE"
                    )
                except Exception as e:
                    print(
                        f"⚠️ PRE-OPEN MARKET CACHE WARMUP ERROR: {e}"
                    )

            except Exception as e:
                print(
                    f"⚠️ PRE-OPEN WARMUP ERROR: {e}"
                )

        threading.Thread(
            target=worker,
            name="ADEL-market-open-warmup",
            daemon=True
        ).start()

        return True

    # ========================================================
    # MARKET OPEN BREAKING NEWS
    #
    # Disabled here intentionally.
    #
    # AdelSmartBot.py handles MARKET_OPEN by:
    #   1. show_top_signals()
    #   2. breaking_news()
    #
    # Compatibility adapter above makes breaking_news()
    # work with the current structured NewsEngine.
    # ========================================================

    def send_market_open_news(self):

        if self.market_open_sent:
            return True

        print(
            "🚨 MARKET OPEN HANDLED BY MAIN BOT"
        )

        self.market_open_sent = True

        return True

    # ========================================================
    # EVENING REPORT
    # ========================================================

    def send_evening_report(self):

        if self.evening_report_sent:
            return True

        return self._start_async_task(
            "evening_report",
            self._send_evening_report_sync
        )

    def _send_evening_report_sync(self):

        if self.evening_report_sent:
            return True

        print(
            "🌙 SENDING EVENING REPORT"
        )

        try:

            data, after_items = (
                self.performance
                .build_evening_structured()
            )

            if not data:

                print(
                    "⚠️ EVENING REPORT EMPTY"
                )

                return False

            report_success = self.send_structured(
                data,
                message_type="report"
            )

            news_success = True

            if after_items:

                print(
                    "📰 SENDING AFTER-MARKET "
                    "DETAILED NEWS"
                )

                for item in after_items:

                    success = self.send_structured(
                        item,
                        message_type="news"
                    )

                    if not success:

                        news_success = False

            if (
                report_success
                and
                news_success
            ):

                self.evening_report_sent = True

                return True

            return False

        except Exception as e:

            print(
                f"❌ EVENING REPORT ERROR: {e}"
            )

            return False

    # ========================================================
    # MAIN SCHEDULER LOOP
    # ========================================================

    def run(self):

        try:

            self.reset_daily_flags()

            # ------------------------------------------------
            # 10:00
            # MORNING REPORT
            # ------------------------------------------------

            if self.is_morning_report_time():

                self.send_morning_report()

                return "SLEEP"

            # ------------------------------------------------
            # 14:30
            # PRE-MARKET INTERNAL PREPARATION
            # No report is sent at this time.
            # ------------------------------------------------

            if self.is_full_pre_market():

                self.start_premarket_preparation()

                return "SLEEP"

            # ------------------------------------------------
            # 15:30
            # PRE-MARKET
            #
            # IMPORTANT:
            # Do NOT return PRE_MARKET.
            #
            # AdelSmartBot.py launches stock signal scanning
            # whenever it receives PRE_MARKET.
            #
            # Therefore we process news but return SLEEP.
            # ------------------------------------------------

            if self.is_pre_market():

                self.send_morning_news()

                now = datetime.now().time()

                if now >= time(16, 20):
                    self._warm_market_cache_before_open()

                return "SLEEP"

            # ------------------------------------------------
            # 16:30
            # MARKET OPEN
            # ------------------------------------------------

            if self.is_market_open():

                return "MARKET_OPEN"

            # ------------------------------------------------
            # 23:00
            # EVENING / AFTER MARKET
            # ------------------------------------------------

            if self.is_after_market():

                self.send_evening_report()

                return "SLEEP"

            # ------------------------------------------------
            # SLEEP
            # ------------------------------------------------

            if self.is_sleep_time():

                self.collect_sleep_data()

                return "SLEEP"

            # ------------------------------------------------
            # DEFAULT
            # ------------------------------------------------

            print(
                "😴 DEFAULT SLEEP MODE"
            )

            return "SLEEP"

        except Exception as e:

            # Absolute safety:
            # scheduler exception must NEVER kill main bot.

            print(
                f"❌ SCHEDULER ERROR: {e}"
            )

            return "SLEEP"


# ============================================================
# DIRECT TEST ENTRY
# ============================================================

if __name__ == "__main__":

    scheduler = DailyScheduler()

    status = scheduler.run()

    print(
        "SCHEDULER STATUS:",
        status
    )
