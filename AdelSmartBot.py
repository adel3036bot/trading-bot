# ==================================================
# ADEL SMART BOT V2.1 - PRODUCTION READY
# ==================================================

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes
)

from datetime import (
    datetime,
    timedelta,
    time
)

import random
import time
import threading
import pandas as pd

# ==================================================
# CONFIG
# ==================================================

from config import (
    WATCHLIST,

    BOT_TOKEN,
    CHAT_ID,
    CHANNEL_URL,
    ADMIN_ID,

    MIN_OPTION_PRICE,
    MAX_OPTION_PRICE,

    CONFIDENCE_A_PLUS,
    CONFIDENCE_A,
    CONFIDENCE_B
)

# ==================================================
# TRADE MANAGER
# ==================================================

from trade_manager import update_trade

# ==================================================
# SCHEDULER
# ==================================================

from daily_scheduler import DailyScheduler

# ==================================================
# TELEGRAM ENGINE
# ==================================================

from telegram_bot.telegram_engine import TelegramEngine
from telegram_bot.telegram_app import TelegramApp

# ==================================================
# MARKET DATA ENGINES
# ==================================================

from market.data_engine import (
    get_stock_data,
    get_option_chain_data,
    get_vix_data,
    get_gold_data,
    get_crypto_data
)

# ==================================================
# NEWS ENGINE (NEW SYSTEM)
# ==================================================

from news.news_engine import NewsEngine


# ==================================================
# GLOBAL CACHE
# ==================================================

market_cache = None
market_cache_time = None

sent_signals = set()

# ==================================================
# MARKET FUNCTIONS
# ==================================================

def get_stock_price(symbol):
    try:
        data = get_stock_data(symbol)
        if data is not None and not data.empty:
            return round(float(data["Close"].iloc[-1]), 2)
    except: pass
    return None

def get_trend(symbol):
    try:
        data = get_stock_data(symbol)
        if data is not None and len(data) >= 2:
            return "CALL 📈" if data["Close"].iloc[-1] > data["Close"].iloc[0] else "PUT 📉"
    except: pass
    return random.choice(["CALL 📈", "PUT 📉"])

# ==================================================
# OPTION FUNCTIONS
# ==================================================

def get_option_expiry(symbol):
    try:
        chain = get_option_chain_data(symbol)
        expiries = chain.get("expiries", []) if chain else []
        return expiries[0] if expiries else None
    except: return None

# ==================================================
# CONTRACT SELECTION ENGINE
# ==================================================

def get_best_option(symbol, signal_type):
    try:
        stock_data = get_stock_data(symbol)
        chain = get_option_chain_data(symbol)
        if stock_data is None or chain is None: return None
        
        expiry = get_option_expiry(symbol)
        if not expiry: return None

        current_price = float(stock_data["Close"].iloc[-1])
        options = pd.DataFrame(chain.get("calls" if "CALL" in signal_type else "puts", []))

        # 1. فلترة العقود الضعيفة
        options = options[(options["openInterest"] > 0) & (options["volume"] > 0)]
        if len(options) == 0: return None

        # 2. فلتر الـ Strike
        max_dist = 0.05 if symbol in ["SPY", "QQQ", "SPX"] else 0.10
        if "CALL" in signal_type:
            options = options[(options["strike"] >= current_price) & (options["strike"] <= current_price * (1 + max_dist))]
        else:
            options = options[(options["strike"] <= current_price) & (options["strike"] >= current_price * (1 - max_dist))]
        
        if len(options) == 0: return None

        # 3. فلتر السعر
        options = options[(options["lastPrice"] >= 1) & (options["lastPrice"] <= 10)].copy()
        if len(options) == 0: return None

        # 4. حساب المسافة والسكور
        options["distance"] = (options["strike"] - current_price).abs()
        options["score"] = ((1 / (options["distance"] + 1)) * 35) + (options["openInterest"] * 0.002) + (options["volume"] * 0.003)
        options = options.sort_values(by="score", ascending=False)
        
        best = options.iloc[0]

        # 5. الإرجاع النهائي
        return {
            "contract_symbol": str(best["contractSymbol"]),
            "strike": float(best["strike"]),
            "option_price": round(float(best["lastPrice"]), 2),
            "expiry": expiry,
            "open_interest": int(best["openInterest"]),
            "volume": int(best["volume"]),
            "distance": round(float(best["distance"]), 2)
        }
    except Exception as e:
        print("OPTION ERROR:", e)
        return None

 # ==================================================
# CONTRACT RATING ENGINE
# ==================================================

def get_contract_rating(
    option_price,
    open_interest,
    volume,
    distance
):

    score = 0

    # ==================
    # PRICE QUALITY
    # ==================

    if 0.5 <= option_price <= 5:
        score += 35
    elif option_price <= 10:
        score += 25
    else:
        score += 10

    # ==================
    # OPEN INTEREST
    # ==================

    if open_interest >= 1000:
        score += 30
    elif open_interest >= 500:
        score += 20
    elif open_interest >= 100:
        score += 10

    # ==================
    # VOLUME
    # ==================

    if volume >= 300:
        score += 20
    elif volume >= 150:
        score += 15
    elif volume >= 50:
        score += 10

    # ==================
    # DISTANCE
    # ==================

    if distance <= 3:
        score += 15
    elif distance <= 5:
        score += 10
    else:
        score += 5

    # ==================
    # FINAL SCORE
    # ==================

    score = min(score, 100)

    # ==================
    # RATING
    # ==================

    if score >= 90:
        return "A+"

    elif score >= 75:
        return "A"

    elif score >= 60:
        return "B"

    return "WEAK"

# ==================================================
# FINAL APPROVAL ENGINE
# ==================================================

def final_approval(
    stock_rating,
    contract_rating
):

    # ==================
    # ELITE
    # ==================

    if (
        stock_rating == "A+"
        and
        contract_rating == "A+"
    ):

        return "SEND"

    # ==================
    # STRONG
    # ==================

    if (
        stock_rating in ["A+", "A"]
        and
        contract_rating in ["A+", "A"]
    ):

        return "SEND"

    # ==================
    # ACCEPTABLE
    # ==================

    if (
        stock_rating == "A"
        and
        contract_rating == "B"
    ):

        return "ALLOW"

    # ==================
    # WEAK CONTRACT
    # ==================

    if contract_rating == "WEAK":

        return "NO TRADE"

    # ==================
    # DEFAULT
    # ==================

    return "NO TRADE"


# ==================================================
# CREATE TRADE
# ==================================================

def create_trade(symbol):

    signal_type = get_trend(symbol)

    score_data = get_signal_score(symbol)

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

    option_data = get_best_option(
        symbol,
        signal_type
    )

    if not option_data:

        return None

    entry = option_data["option_price"]

    strike = option_data["strike"]

    expiry = option_data["expiry"]

    contract_symbol = option_data["contract_symbol"]


    # ==================================================
    # CONTRACT RATING
    # ==================================================

    contract_rating = get_contract_rating(
        entry,
        option_data["open_interest"],
        option_data["volume"],
        option_data["distance"]
    )

    # ==================================================
    # FINAL APPROVAL
    # ==================================================

    approval = final_approval(
        confidence,
        contract_rating
    )

    print(
        "CONTRACT RATING =",
        contract_rating
    )

    print(
        "FINAL APPROVAL =",
        approval
    )

    if approval == "NO TRADE":

        return None

    return {

        "symbol": symbol,

        "entry": entry,

        "strike": strike,

        "contract_symbol": contract_symbol,

        "signal_type": signal_type,

        "score": score,

        "confidence": confidence,

        "contract_rating": contract_rating,

        "approval": approval,

        "trade_type": "Real Option",

        "expiry": expiry,

        "tp1": round(
            entry * 1.30,
            2
        ),

        "tp2": round(
            entry * 1.60,
            2
        ),

        "tp3": round(
            entry * 2.00,
            2
        ),

        "sl": round(
            entry * 0.70,
            2
        ),

        "status": "NEW",

        "profit": 0.0,

        "stage": 0,

        "created_at": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    }


# ==================================================
# SIGNAL SCORE ENGINE
# ==================================================
# ==================================================
# MARKET REGIME ENGINE
# ==================================================

def get_market_regime():

    try:

        market_symbols = {

            "SPX": "^GSPC",
            "NASDAQ": "^IXIC",
            "SPY": "SPY",
            "QQQ": "QQQ"

        }

        score = 0

        for name, symbol in market_symbols.items():

            data = get_stock_data(symbol)

            if data is None or len(data) < 200:

                continue

            close = float(

                data["Close"].iloc[-1]

            )

            ema50 = (

                data["Close"]
                .ewm(span=50)
                .mean()
                .iloc[-1]

            )

            ema200 = (

                data["Close"]
                .ewm(span=200)
                .mean()
                .iloc[-1]

            )

            symbol_score = 0

            if close > ema50:

                symbol_score += 50

            if close > ema200:

                symbol_score += 50

            if name == "SPX":

                score += symbol_score * 0.40

            elif name == "NASDAQ":

                score += symbol_score * 0.30

            elif name == "SPY":

                score += symbol_score * 0.20

            elif name == "QQQ":

                score += symbol_score * 0.10

        score = round(score)
        
# ==================
# MARKET SENTIMENT
# ==================

        sentiment_score = 0

        # VIX
        vix_data = get_vix_data()

        if vix_data is not None and len(vix_data) > 0:

            vix_close = float(
                vix_data["Close"].iloc[-1]
            )

            if vix_close < 20:

                sentiment_score += 3

            elif vix_close > 25:

                sentiment_score -= 3

        # GOLD
        gold_data = get_gold_data()

        if gold_data is not None and len(gold_data) > 0:

            gold_close = float(
                gold_data["Close"].iloc[-1]
            )

            gold_ema20 = (
                gold_data["Close"]
                .ewm(span=20)
                .mean()
                .iloc[-1]
            )

            if gold_close > gold_ema20:

                sentiment_score -= 2

            else:

                sentiment_score += 2

        # BITCOIN
        btc_data = get_crypto_data()

        if btc_data is not None and len(btc_data) > 0:

            btc_close = float(
                btc_data["Close"].iloc[-1]
            )

            btc_ema20 = (
                btc_data["Close"]
                .ewm(span=20)
                .mean()
                .iloc[-1]
            )

            if btc_close > btc_ema20:

                sentiment_score += 2

            else:

                sentiment_score -= 2

        score += sentiment_score

        score = round(score)

        if score >= 75:

            bias = "BULLISH 📈"

        elif score >= 50:

            bias = "NEUTRAL ⚖️"

        else:

            bias = "BEARISH 📉"

        return {

            "market_score": score,

            "market_bias": bias

        }

    except Exception as e:

        print(
            f"MARKET ERROR: {e}"
        )

        return {

            "market_score": 0,

            "market_bias": "UNKNOWN"

        }

 # ==================================================
# MARKET CACHE
# ==================================================

def get_cached_market():

    global market_cache
    global market_cache_time

    now = datetime.now()

    if (
        market_cache is None
        or market_cache_time is None
        or (now - market_cache_time).seconds > 300
    ):

        market_cache = get_market_regime()

        market_cache_time = now

    return market_cache


# ==================================================
# REAL SCORE ENGINE
# ==================================================

def get_signal_score(symbol):

    try:

        score = 0

        market = get_cached_market()

        print("START:", symbol)
        print("MARKET:", market)

        trend = get_trend(symbol)

        print("TREND:", trend)

        score += round(
            market["market_score"] * 0.35
        )

        print(
            "AFTER MARKET =",
            score
        )

        # ==========================
        # GET DATA FROM SOURCE ENGINE
        # ==========================

        data = get_stock_data(symbol)

        if data is None:

            return {

                "score": 0,

                "confidence": "NO TRADE"

            }

        print(
            "LEN =",
            len(data)
        )

        if len(data) < 100:

            print(
                "NOT ENOUGH DATA"
            )

            return {

                "score": 0,

                "confidence": "NO TRADE"

            }

        close = float(
            data["Close"].iloc[-1]
        )

        ema20 = (
            data["Close"]
            .ewm(span=20)
            .mean()
            .iloc[-1]
        )

        ema50 = (
            data["Close"]
            .ewm(span=50)
            .mean()
            .iloc[-1]
        )

        ema200 = (
            data["Close"]
            .ewm(span=200)
            .mean()
            .iloc[-1]
        )

        structure_score = 0

        if close > ema20:

            structure_score += 30

        if close > ema50:

            structure_score += 35

        if close > ema200:

            structure_score += 35

        print(
            "STRUCTURE SCORE =",
            structure_score
        )

        score += round(
            structure_score * 0.30
        )

        print(
            "AFTER STRUCTURE =",
            score
        )

       # ==================
# MOMENTUM LAYER
# ==================

        rsi_period = 14

        delta = data["Close"].diff()

        gain = delta.where(delta > 0, 0)

        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.rolling(rsi_period).mean()

        avg_loss = gain.rolling(rsi_period).mean() * 0 + loss.rolling(rsi_period).mean()
        avg_loss = avg_loss.replace(0, 0.000001)

        rs = avg_gain / avg_loss

        rsi = 100 - (100 / (1 + rs))

        rsi_value = rsi.iloc[-1]

        print("RSI =", round(rsi_value, 2))

        momentum_score = 0

        if 50 <= rsi_value <= 70:
            momentum_score += 60

        elif 40 <= rsi_value < 50:
            momentum_score += 30

        elif rsi_value > 70:
            momentum_score += 20

        print("MOMENTUM SCORE =", momentum_score)

        score += round(
            momentum_score * 0.10
        )

        print("AFTER MOMENTUM =", score)


        # ==================
        # VOLUME SCORE
        # ==================

        volume_avg = data["Volume"].rolling(20).mean().iloc[-1]

        current_volume = data["Volume"].iloc[-1]

        print("CURRENT VOLUME =", int(current_volume))

        print("AVG VOLUME =", int(volume_avg))

        volume_score = 0

        if current_volume > volume_avg * 1.5:

            volume_score = 100

        elif current_volume > volume_avg:

            volume_score = 60

        else:

            volume_score = 0

        print("VOLUME SCORE =", volume_score)

        score += round(
            volume_score * 0.10
        )

        print("AFTER VOLUME =", score)


        # =========================
        # SMART MONEY LAYER (BoS)
        # =========================

        last_close = data["Close"].iloc[-1]

        recent_high = data["High"].iloc[-21:-1].max()

        recent_low = data["Low"].iloc[-21:-1].min()

        bos_score = 0

        if last_close > recent_high:

            bos_score = 100

        elif last_close < recent_low:

            bos_score = 100

        print("BOS SCORE =", bos_score)

        score += round(
            bos_score * 0.20
        )

        print("AFTER BOS =", score)


       # ==================
        # BREAKOUT PATTERN
        # ==================

        recent_high = data["High"].iloc[-11:-1].max()

        breakout_score = 0

        if last_close > recent_high:
            breakout_score = 100

        print("BREAKOUT SCORE =", breakout_score)

        score += round(
            breakout_score * 0.05
        )

        print("AFTER BREAKOUT =", score)


# ==================
        # FVG LAYER
        # ==================

        fvg_score = 0

        candle1_high = data["High"].iloc[-3]

        candle1_low = data["Low"].iloc[-3]

        candle3_high = data["High"].iloc[-1]

        candle3_low = data["Low"].iloc[-1]

        bullish_fvg = False

        bearish_fvg = False

        # Bullish FVG
        if candle3_low > candle1_high:

            bullish_fvg = True

        # Bearish FVG
        elif candle3_high < candle1_low:

            bearish_fvg = True

        if bullish_fvg:

            fvg_score = 20

        elif bearish_fvg:

            fvg_score = 20

        print("BULLISH FVG =", bullish_fvg)

        print("BEARISH FVG =", bearish_fvg)

        print("FVG SCORE =", fvg_score)

        score += round(
            fvg_score * 0.10
        )

        print("AFTER FVG =", score)



# ==================
        # ORDER BLOCK LAYER
        # ==================

        current_open = data["Open"].iloc[-1]
        current_close = data["Close"].iloc[-1]

        previous_open = data["Open"].iloc[-2]
        previous_close = data["Close"].iloc[-2]

        current_high = data["High"].iloc[-1]
        current_low = data["Low"].iloc[-1]

        previous_high = data["High"].iloc[-2]
        previous_low = data["Low"].iloc[-2]

        orderblock_score = 0

        # ==================
        # BULLISH ORDER BLOCK
        # ==================

        bullish_ob = False

        if (
            previous_close < previous_open
            and current_close > current_open
            and close > ema20
            and close > ema50
            and rsi_value > 50
        ):

            bullish_ob = True

        # ==================
        # BEARISH ORDER BLOCK
        # ==================

        bearish_ob = False

        if (
            previous_close > previous_open
            and current_close < current_open
            and close < ema20
            and close < ema50
            and rsi_value < 50
        ):

            bearish_ob = True

            # ==================
        # BOS CONFIRMATION
        # ==================

        bos_confirmation = False

        if (
            last_close > recent_high
            or last_close < recent_low
        ):

            bos_confirmation = True


        # ==================
        # INSTITUTIONAL CANDLE
        # ==================

        candle_size = abs(
            current_close - current_open
        )

        avg_candle_size = abs(
            data["Close"] - data["Open"]
        ).tail(20).mean()

        institutional_candle = False

        if candle_size > avg_candle_size * 1.5:

            institutional_candle = True


        # ==================
        # VOLUME CONFIRMATION
        # ==================

        volume_confirmation = False

        if current_volume > volume_avg:

            volume_confirmation = True

            
            # ==================
        # FVG CONFIRMATION
        # ==================

        fvg_confirmation = False

        previous_high = data["High"].iloc[-2]
        current_low = data["Low"].iloc[-1]

        previous_low = data["Low"].iloc[-2]
        current_high = data["High"].iloc[-1]

        if current_low > previous_high:

            fvg_confirmation = True

        elif current_high < previous_low:

            fvg_confirmation = True

# ==================
        # LIQUIDITY SWEEP
        # ==================

        liquidity_sweep = False

        current_high = data["High"].iloc[-1]

        current_low = data["Low"].iloc[-1]

        current_close = data["Close"].iloc[-1]

        last_5_high = data["High"].iloc[-6:-1].max()

        last_5_low = data["Low"].iloc[-6:-1].min()

        # سحب سيولة القمم
        if (
            current_high > last_5_high
            and current_close < last_5_high
        ):

            liquidity_sweep = True

        # سحب سيولة القيعان
        elif (
            current_low < last_5_low
            and current_close > last_5_low
        ):

            liquidity_sweep = True

        print("LIQUIDITY SWEEP =", liquidity_sweep)

        
        # ==================
        # MITIGATION
        # ==================

        mitigation = False

        recent_mid = (
            recent_high + recent_low
        ) / 2

        if abs(
            close - recent_mid
        ) / close < 0.01:

            mitigation = True


            # ==================
        # RE-TEST
        # ==================

        retest_confirmation = False

        if bullish_ob:

            if close > previous_low:

                retest_confirmation = True

        elif bearish_ob:

            if close < previous_high:

                retest_confirmation = True


        # ==================
        # ZERO REVERSAL ZONE
        # ==================

        zero_reversal_zone = False

        recent_range = recent_high - recent_low

        if recent_range > 0:

            distance_from_mid = abs(
                close - recent_mid
            ) / recent_range

            if distance_from_mid < 0.15:

                zero_reversal_zone = True


# ==================
        # MULTI TIME FRAME
        # ==================

        mtf_confirmation = False

        if (
            close > ema20
            and close > ema50
            and rsi_value > 50
        ):

            mtf_confirmation = True

        elif (
            close < ema20
            and close < ema50
            and rsi_value < 50
        ):

            mtf_confirmation = True

           

        # ==================
        # ORDER BLOCK SCORE
        # ==================

        orderblock_score = 0

        # BOS
        if bos_score == 100:
            orderblock_score += 20

        # Institutional Candle
        if institutional_candle:
            orderblock_score += 10

        # Volume Confirmation
        if volume_confirmation:
            orderblock_score += 10

        # FVG Confirmation
        if fvg_confirmation:
            orderblock_score += 15

        # Liquidity Sweep
        if liquidity_sweep:
            orderblock_score += 15

        # Mitigation
        if mitigation:
            orderblock_score += 10

        # Re-Test
        if retest_confirmation:
            orderblock_score += 10

        # Zero Reversal Zone
        if zero_reversal_zone:
            orderblock_score += 5

        # Multi Time Frame
        if mtf_confirmation:
            orderblock_score += 15

        print("BOS =", bos_score)
        print("INSTITUTIONAL =", institutional_candle)
        print("VOLUME =", volume_confirmation)
        print("FVG =", fvg_confirmation)
        print("LIQUIDITY =", liquidity_sweep)
        print("MITIGATION =", mitigation)
        print("RETEST =", retest_confirmation)
        print("ZERO REVERSAL =", zero_reversal_zone)
        print("MTF =", mtf_confirmation)

        print("ORDER BLOCK SCORE =", orderblock_score)

        score += round(
            orderblock_score * 0.10
        )

        print("AFTER ORDER BLOCK =", score)

        
# ==================
# PULLBACK LAYER
# ==================

        pullback_score = 0

        # ==================
        # TREND ALIGNMENT
        # ==================

        trend_alignment = False

        if (
            close > ema20
            and close > ema50
        ):

            trend_alignment = True

        # ==================
        # HEALTHY RSI
        # ==================

        healthy_rsi = False

        if 45 <= rsi_value <= 65:

            healthy_rsi = True

        # ==================
        # VOLUME PULLBACK
        # ==================

        volume_pullback = False

        if current_volume < volume_avg:

            volume_pullback = True

        # ==================
        # REVERSAL CANDLE
        # ==================

        reversal_candle = False

        previous_open = data["Open"].iloc[-2]

        previous_close = data["Close"].iloc[-2]

        current_open = data["Open"].iloc[-1]

        current_close = data["Close"].iloc[-1]

        if (
            previous_close < previous_open
            and current_close > current_open
            and current_close > previous_open
        ):

            reversal_candle = True

        print("REVERSAL CANDLE =", reversal_candle)

        # Trend Alignment
        if trend_alignment:

            pullback_score += 30

        # Healthy RSI
        if healthy_rsi:

            pullback_score += 25

        # Volume Pullback
        if volume_pullback:

            pullback_score += 20

        # Reversal Candle
        if reversal_candle:

            pullback_score += 25

        # عدم تجاوز الحد الأقصى
        pullback_score = min(pullback_score, 100)

        print("PULLBACK SCORE =", pullback_score)

        score += round(
            pullback_score * 0.05
        )

        print("AFTER PULLBACK =", score)


# ==================
# BULL FLAG LAYER
# ==================

        bullflag_score = 0

        # السعر فوق EMA20
        if close > ema20:
            bullflag_score += 20

        # السعر فوق EMA50
        if close > ema50:
            bullflag_score += 20

        # RSI إيجابي
        if rsi_value > 55:
            bullflag_score += 15

        # حجم التداول أعلى من المتوسط
        if current_volume > volume_avg:
            bullflag_score += 15

        # وجود شمعة مؤسساتية
        if institutional_candle:
            bullflag_score += 10

        # وجود FVG
        if fvg_confirmation:
            bullflag_score += 10

        # توافق الفريمات
        if mtf_confirmation:
            bullflag_score += 10

        bullflag_score = min(
            bullflag_score,
            100
        )

        print("BULL FLAG SCORE =", bullflag_score)

        score += round(
            bullflag_score * 0.05
        )

        print("AFTER BULL FLAG =", score)

        # ==================
        # SCORE LIMIT
        # ==================

        score = min(
            score,
            100
        )

        print("FINAL SCORE =", score)

        if score >= 90:

            confidence = "A+"

        elif score >= 85:

            confidence = "A"

        elif score >= 80:

            confidence = "B+"

        else:

            confidence = "NO TRADE"

        return {

            "score": score,

            "confidence": confidence

        }

    except Exception as e:

        print(f"ERROR IN {symbol}: {e}")

        return {

            "score": 0,

            "confidence": "NO TRADE"

        }

# ==================================================
# SIGNAL ENGINE
# ==================================================

import time

sent_signals = set()


def scan_watchlist():

    signals = []

    all_symbols = (

        WATCHLIST["INDICES"]
        + WATCHLIST["ETFS"]
        + WATCHLIST["STOCKS"]
        + WATCHLIST["ENERGY"]
        + WATCHLIST["GOLD"]
        + WATCHLIST["BITCOIN"]

    )

    for symbol in all_symbols:

        trade = create_trade(symbol)

        if trade:

            trade = update_trade(
                trade,
                trade["entry"]
            )

            signals.append(trade)

    signals = sorted(
        signals,
        key=lambda x: x["score"],
        reverse=True
    )

    return signals[:5]


def show_top_signals():

    global sent_signals

    print("\n📊 SCANNING WATCHLIST\n")

    telegram = TelegramEngine()

    signals = scan_watchlist()

    for signal in signals:

        signal_id = (

            signal["symbol"],

            signal["signal_type"],

            signal["contract_symbol"],

            signal["expiry"]

        )

        if signal_id not in sent_signals:

            telegram.send_signal(signal)

            sent_signals.add(signal_id)

            print(

                f"{signal['symbol']} | "

                f"Score: {signal['score']} | "

                f"{signal['confidence']}"

            )

        else:

            print(

                f"⏩ Skipping "

                f"{signal['symbol']} "

                f"(already sent)"

            )

# ==================================================
# ADEL SMART BOT V2.1 - PRODUCTION READY (ELITE FINAL FREEZE)
# ==================================================

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes
)

from datetime import (
    datetime,
    timedelta,
    time
)

import random
import time
import threading
import pandas as pd

# ==================================================
# CONFIG
# ==================================================

from config import (
    WATCHLIST,
    BOT_TOKEN,
    CHAT_ID,
    CHANNEL_URL,
    ADMIN_ID,
    MIN_OPTION_PRICE,
    MAX_OPTION_PRICE,
    CONFIDENCE_A_PLUS,
    CONFIDENCE_A,
    CONFIDENCE_B
)

# ==================================================
# TRADE MANAGER
# ==================================================

from trade_manager import update_trade

# ==================================================
# SCHEDULER
# ==================================================

from daily_scheduler import DailyScheduler

# ==================================================
# TELEGRAM ENGINE
# ==================================================

from telegram_bot.telegram_engine import TelegramEngine
from telegram_bot.telegram_app import TelegramApp

# ==================================================
# MARKET DATA ENGINES
# ==================================================

from market.data_engine import (
    get_stock_data,
    get_option_chain_data,
    get_vix_data,
    get_gold_data,
    get_crypto_data
)

# ==================================================
# NEWS ENGINE (NEW SYSTEM)
# ==================================================

from news.news_engine import NewsEngine


# ==================================================
# GLOBAL CACHE
# ==================================================

market_cache = None
market_cache_time = None

sent_signals = set()

# ==================================================
# MARKET FUNCTIONS
# ==================================================

def get_stock_price(symbol):
    try:
        data = get_stock_data(symbol)
        if data is not None and not data.empty:
            return round(float(data["Close"].iloc[-1]), 2)
    except:
        pass
    return None


def get_trend(symbol):
    try:
        data = get_stock_data(symbol)
        if data is not None and len(data) >= 2:
            return "CALL 📈" if data["Close"].iloc[-1] > data["Close"].iloc[0] else "PUT 📉"
    except:
        pass
    return random.choice(["CALL 📈", "PUT 📉"])


# ==================================================
# OPTION FUNCTIONS
# ==================================================

def get_option_expiry(symbol):
    try:
        chain = get_option_chain_data(symbol)
        expiries = chain.get("expiries", []) if chain else []
        return expiries[0] if expiries else None
    except:
        return None


# ==================================================
# CONTRACT SELECTION ENGINE
# ==================================================

def get_best_option(symbol, signal_type):
    try:
        stock_data = get_stock_data(symbol)
        chain = get_option_chain_data(symbol)
        if stock_data is None or chain is None:
            return None

        expiry = get_option_expiry(symbol)
        if not expiry:
            return None

        current_price = float(stock_data["Close"].iloc[-1])
        options = pd.DataFrame(chain.get("calls" if "CALL" in signal_type else "puts", []))

        options = options[(options["openInterest"] > 0) & (options["volume"] > 0)]
        if len(options) == 0:
            return None

        max_dist = 0.05 if symbol in ["SPY", "QQQ", "SPX"] else 0.10
        if "CALL" in signal_type:
            options = options[(options["strike"] >= current_price) & (options["strike"] <= current_price * (1 + max_dist))]
        else:
            options = options[(options["strike"] <= current_price) & (options["strike"] >= current_price * (1 - max_dist))]

        if len(options) == 0:
            return None

        options = options[(options["lastPrice"] >= MIN_OPTION_PRICE) & (options["lastPrice"] <= MAX_OPTION_PRICE)]
        if len(options) == 0:
            return None

        options["distance"] = (options["strike"] - current_price).abs()
        options["score"] = ((1 / (options["distance"] + 1)) * 35) + (options["openInterest"] * 0.002) + (options["volume"] * 0.003)
        options = options.sort_values(by="score", ascending=False)

        best = options.iloc[0]

        return {
            "contract_symbol": str(best["contractSymbol"]),
            "strike": float(best["strike"]),
            "option_price": round(float(best["lastPrice"]), 2),
            "expiry": expiry,
            "open_interest": int(best["openInterest"]),
            "volume": int(best["volume"]),
            "distance": round(float(best["distance"]), 2),
            "bid": float(best.get("bid", best["lastPrice"])),
            "ask": float(best.get("ask", best["lastPrice"])),
            "delta": float(best.get("delta", 0.0))
        }
    except Exception as e:
        print("OPTION ERROR:", e)
        return None


# ==================================================
# CONTRACT RATING ENGINE
# ==================================================

def get_contract_rating(
    option_price,
    open_interest,
    volume,
    distance,
    bid=None,
    ask=None,
    delta=None
):

    score = 0

    if MIN_OPTION_PRICE <= option_price <= MAX_OPTION_PRICE:
        score += 35
    elif option_price <= MAX_OPTION_PRICE * 1.5:
        score += 25
    else:
        score += 10

    if open_interest >= 1000:
        score += 30
    elif open_interest >= 500:
        score += 20
    elif open_interest >= 100:
        score += 10

    if volume >= 300:
        score += 20
    elif volume >= 150:
        score += 15
    elif volume >= 50:
        score += 10

    if distance <= 3:
        score += 15
    elif distance <= 5:
        score += 10
    else:
        score += 5

    if bid is not None and ask is not None:
        spread = ask - bid
        if spread <= option_price * 0.05:
            score += 10
        elif spread <= option_price * 0.10:
            score += 5

    if delta is not None:
        if 0.3 <= abs(delta) <= 0.7:
            score += 10

    score = min(score, 100)

    if score >= 90:
        return "A+"
    elif score >= 75:
        return "A"
    elif score >= 60:
        return "B"
    return "WEAK"


# ==================================================
# FINAL APPROVAL ENGINE
# ==================================================

def final_approval(
    stock_rating,
    contract_rating
):

    if stock_rating == "A+" and contract_rating == "A+":
        return "SEND"

    if stock_rating in ["A+", "A"] and contract_rating in ["A+", "A"]:
        return "SEND"

    if stock_rating == "A" and contract_rating == "B":
        return "ALLOW"

    if contract_rating == "WEAK":
        return "NO TRADE"

    return "NO TRADE"


# ==================================================
# DATA QUALITY ENGINE
# ==================================================

def check_data_quality(symbol, data, option_data) -> bool:
    if data is None or len(data) < 100:
        print(f"❌ DATA QUALITY: insufficient data for {symbol}")
        return False

    if option_data is None:
        print(f"❌ DATA QUALITY: no option data for {symbol}")
        return False

    if option_data["option_price"] <= 0:
        print(f"❌ DATA QUALITY: invalid option price for {symbol}")
        return False

    return True


# ==================================================
# CONFIDENCE ENGINE
# ==================================================

def confidence_engine(layers, score, market_bias, market_score, trend):
    ok_count = sum(1 for v in layers.values() if v)
    missing_layers = [name for name, ok in layers.items() if not ok]

    if market_bias == "BEARISH 📉" and "CALL" in trend:
        print("❌ Confidence rejected — CALL vs Bearish Market")
        print("Missing:", missing_layers)
        return "NO TRADE"

    if market_score < 50 and score >= 80:
        print("❌ Confidence rejected — Weak Market")
        print("Missing:", missing_layers)
        return "NO TRADE"

    if score >= CONFIDENCE_A_PLUS and ok_count >= 6:
        return "A+"
    if score >= CONFIDENCE_A and ok_count >= 5:
        return "A"
    if score >= CONFIDENCE_B and ok_count >= 4:
        return "B+"

    print("❌ Confidence rejected — Missing:", missing_layers)
    return "NO TRADE"


# ==================================================
# REAL SCORE ENGINE
# ==================================================

def get_signal_score(symbol):

    try:

        score = 0
        reasons = []

        market = get_cached_market()

        trend = get_trend(symbol)

        score += round(
            market["market_score"] * 0.35
        )

        data = get_stock_data(symbol)

        if data is None or len(data) < 100:
            return {
                "score": 0,
                "confidence": "NO TRADE",
                "reasons": ["Not enough data"]
            }

        close = float(data["Close"].iloc[-1])

        ema20 = data["Close"].ewm(span=20).mean().iloc[-1]
        ema50 = data["Close"].ewm(span=50).mean().iloc[-1]
        ema200 = data["Close"].ewm(span=200).mean().iloc[-1]

        structure_score = 0

        if close > ema20:
            structure_score += 30
            reasons.append("Price above EMA20")

        if close > ema50:
            structure_score += 35
            reasons.append("Price above EMA50")

        if close > ema200:
            structure_score += 35
            reasons.append("Price above EMA200")

        score += round(structure_score * 0.30)

        rsi_period = 14
        delta = data["Close"].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(rsi_period).mean()
        avg_loss = loss.rolling(rsi_period).mean().replace(0, 0.000001)
        rs = avg_gain / avg_loss
        rsi_value = 100 - (100 / (1 + rs))

        momentum_score = 0

        if 50 <= rsi_value.iloc[-1] <= 70:
            momentum_score += 60
            reasons.append("RSI bullish zone")
        elif 40 <= rsi_value.iloc[-1] < 50:
            momentum_score += 30
            reasons.append("RSI neutral")
        elif rsi_value.iloc[-1] > 70:
            momentum_score += 20
            reasons.append("RSI overbought")

        score += round(momentum_score * 0.10)

        volume_avg = data["Volume"].rolling(20).mean().iloc[-1]
        current_volume = data["Volume"].iloc[-1]

        volume_score = 0

        if current_volume > volume_avg * 1.5:
            volume_score = 100
            reasons.append("Volume spike")
        elif current_volume > volume_avg:
            volume_score = 60
            reasons.append("Volume above average")

        score += round(volume_score * 0.10)

        last_close = data["Close"].iloc[-1]
        recent_high = data["High"].iloc[-21:-1].max()
        recent_low = data["Low"].iloc[-21:-1].min()

        bos_score = 0

        if last_close > recent_high:
            bos_score = 100
            reasons.append("Bullish BOS")
        elif last_close < recent_low:
            bos_score = 100
            reasons.append("Bearish BOS")

        score += round(bos_score * 0.20)

        recent_high = data["High"].iloc[-11:-1].max()
        breakout_score = 0

        if last_close > recent_high:
            breakout_score = 100
            reasons.append("Breakout")

        score += round(breakout_score * 0.05)

        candle1_high = data["High"].iloc[-3]
        candle1_low = data["Low"].iloc[-3]
        candle3_high = data["High"].iloc[-1]
        candle3_low = data["Low"].iloc[-1]

        fvg_score = 0
        bullish_fvg = candle3_low > candle1_high
        bearish_fvg = candle3_high < candle1_low

        if bullish_fvg:
            fvg_score = 20
            reasons.append("Bullish FVG")
        elif bearish_fvg:
            fvg_score = 20
            reasons.append("Bearish FVG")

        score += round(fvg_score * 0.10)

        bullish_ob = (
            data["Close"].iloc[-2] < data["Open"].iloc[-2]
            and data["Close"].iloc[-1] > data["Open"].iloc[-1]
            and close > ema20
            and close > ema50
        )

        bearish_ob = (
            data["Close"].iloc[-2] > data["Open"].iloc[-2]
            and data["Close"].iloc[-1] < data["Open"].iloc[-1]
            and close < ema20
            and close < ema50
        )

        liquidity_sweep = False
        last_5_high = data["High"].iloc[-6:-1].max()
        last_5_low = data["Low"].iloc[-6:-1].min()

        if data["High"].iloc[-1] > last_5_high and data["Close"].iloc[-1] < last_5_high:
            liquidity_sweep = True
            reasons.append("Liquidity sweep (highs)")
        elif data["Low"].iloc[-1] < last_5_low and data["Close"].iloc[-1] > last_5_low:
            liquidity_sweep = True
            reasons.append("Liquidity sweep (lows)")

        layers = {}
        layers["market"] = market["market_score"] >= 60
        layers["structure"] = structure_score >= 60
        layers["momentum"] = momentum_score >= 30
        layers["volume"] = volume_score >= 60
        layers["smc"] = bos_score == 100 or bullish_ob or bearish_ob or liquidity_sweep
        layers["pattern"] = breakout_score == 100 or fvg_score >= 20

        score = min(score, 100)

        confidence = confidence_engine(
            layers,
            score,
            market["market_bias"],
            market["market_score"],
            trend
        )

        return {
            "score": score,
            "confidence": confidence,
            "reasons": reasons
        }

    except Exception as e:

        print(f"ERROR IN {symbol}: {e}")

        return {
            "score": 0,
            "confidence": "NO TRADE",
            "reasons": [f"Error: {e}"]
        }


# ==================================================
# SIGNAL ENGINE
# ==================================================

sent_signals = set()


def hard_filter(trade: dict, market: dict, session: str, news_engine: NewsEngine) -> bool:
    try:
        if news_engine.has_high_impact_event_window():
            print("❌ HARD FILTER: high impact news window")
            return False
    except:
        pass

    if market["market_score"] < 50 and trade["confidence"] in ["A+", "A", "B+"]:
        print("❌ HARD FILTER: weak market")
        return False

    if market["market_bias"] == "BEARISH 📉" and "CALL" in trade["signal_type"]:
        print("❌ HARD FILTER: CALL vs Bearish")
        return False

    if trade.get("contract_rating") == "WEAK":
        print("❌ HARD FILTER: weak contract")
        return False

    if session == "PRE_MARKET" and trade["symbol"] not in ["SPX", "SPY", "QQQ"]:
        print("❌ HARD FILTER: non-index in pre-market")
        return False

    return True


def scan_watchlist(session: str, news_engine: NewsEngine):

    signals = []

    all_symbols = (
        WATCHLIST["INDICES"]
        + WATCHLIST["ETFS"]
        + WATCHLIST["STOCKS"]
        + WATCHLIST["ENERGY"]
        + WATCHLIST["GOLD"]
        + WATCHLIST["BITCOIN"]
    )

    market = get_cached_market()

    for symbol in all_symbols:

        trade = create_trade(symbol)

        if trade:

            trade = update_trade(
                trade,
                trade["entry"]
            )

            if not hard_filter(trade, market, session, news_engine):
                continue

            signals.append(trade)

    signals = sorted(
        signals,
        key=lambda x: x["score"],
        reverse=True
    )

    return signals[:5]


def show_top_signals(session: str, news_engine: NewsEngine):

    global sent_signals

    telegram = TelegramEngine()

    signals = scan_watchlist(session, news_engine)

    for signal in signals:

        signal_id = (
            signal["symbol"],
            signal["signal_type"],
            signal["contract_symbol"],
            signal["expiry"]
        )

        explain = "سبب الترشيح:\n" + "\n".join(
            f"✔ {reason}" for reason in signal.get("reasons", [])
        )

        if signal_id not in sent_signals:

            telegram.send_signal(signal, extra_text=explain)

            sent_signals.add(signal_id)

        else:

            print(
                f"⏩ Skipping "
                f"{signal['symbol']} "
                f"(already sent)"
            )


# ==================================================
# MAIN
# ==================================================

if __name__ == "__main__":

    print("🚀 ADEL SMART BOT STARTED")

    scheduler = DailyScheduler()
    telegram = TelegramEngine()

    news_engine = NewsEngine()

    # ==================================================
    # TELEGRAM USER INTERFACE
    # ==================================================

    telegram_ui = TelegramApp(
        token=BOT_TOKEN,
        channel_url=CHANNEL_URL,
        admin_id=ADMIN_ID
    )

    ui_thread = threading.Thread(
        target=lambda: telegram_ui.get_application().run_polling(
            drop_pending_updates=True
        ),
        daemon=True
    )

    ui_thread.start()

    # ==================================================
    # MAIN LOOP
    # ==================================================

    while True:

        try:

            status = scheduler.run()

            if status == "MARKET_OPEN":

                print("📈 MARKET OPEN MODE")

                show_top_signals("MARKET_OPEN", news_engine)

                breaking_news = news_engine.breaking_news()
                for news in breaking_news:
                    telegram.send_message(news["message"])

            elif status == "PRE_MARKET":

                print("🌅 PRE MARKET MODE")

                show_top_signals("PRE_MARKET", news_engine)

                pre_market_news = news_engine.morning_news()
                for news in pre_market_news:
                    telegram.send_message(news["message"])

            elif status == "AFTER_MARKET":

                print("📊 AFTER MARKET MODE")

                show_top_signals("AFTER_MARKET", news_engine)

                after_market_news = news_engine.after_market_news()
                for news in after_market_news:
                    telegram.send_message(news["message"])

            else:

                print("🌙 MARKET CLOSED")

            print("⏳ Waiting 60 seconds...")
            time.sleep(60)

        except Exception as e:

            print("ERROR:", e)
            time.sleep(60)

            

            