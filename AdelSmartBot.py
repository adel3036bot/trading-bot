# ==================================================
# ADEL SMART BOT V2
# ==================================================

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from datetime import datetime, timedelta

import yfinance as yf
import random
from config import WATCHLIST

from trade_manager import update_trade
from telegram_bot.telegram_engine import TelegramEngine



# ==================================================
# MARKET FUNCTIONS
# ==================================================

def get_stock_price(symbol):

    try:
        stock = yf.Ticker(symbol)

        data = stock.history(period="1d")

        if not data.empty:
            return round(data["Close"].iloc[-1], 2)

    except Exception:
        pass

    return None


def get_trend(symbol):

    try:
        stock = yf.Ticker(symbol)

        data = stock.history(period="5d")

        if len(data) >= 2:

            first_close = data["Close"].iloc[0]
            last_close = data["Close"].iloc[-1]

            if last_close > first_close:
                return "CALL 📈"

            return "PUT 📉"

    except Exception:
        pass

    return random.choice([
        "CALL 📈",
        "PUT 📉"
    ])

# ==================================================
# OPTION FUNCTIONS
# ==================================================

def get_option_expiry(symbol):

    try:

        stock = yf.Ticker(symbol)

        expiries = stock.options

        if len(expiries) == 0:
            return None

        weekly_expiry = None

        daily_expiry = None

        swing_expiry = None

        today = datetime.now().date()

        for expiry in expiries:

            expiry_date = datetime.strptime(
                expiry,
                "%Y-%m-%d"
            ).date()

            days = (
                expiry_date - today
            ).days

            # Weekly (المفضل)
            if 5 <= days <= 10:

                if weekly_expiry is None:

                    weekly_expiry = expiry

            # Daily
            elif 0 <= days <= 3:

                if daily_expiry is None:

                    daily_expiry = expiry

            # Swing
            elif 14 <= days <= 30:

                if swing_expiry is None:

                    swing_expiry = expiry

        if weekly_expiry:

            return weekly_expiry

        if daily_expiry:

            return daily_expiry

        if swing_expiry:

            return swing_expiry

        return expiries[0]

    except Exception:

        return None


def get_best_option(symbol, signal_type):

    try:

        stock = yf.Ticker(symbol)

        expiry = get_option_expiry(symbol)

        if not expiry:
            return None

        current_price = float(
            stock.history(
                period="1d"
            )["Close"].iloc[-1]
        )

        chain = stock.option_chain(expiry)

        if "CALL" in signal_type:
            options = chain.calls
        else:
            options = chain.puts

        options = options[
            (options["openInterest"] > 0)
            & (options["volume"] > 0)
        ]

        if len(options) == 0:
            return None

        price_ranges = [
            (1, 3),
            (3, 6),
            (6, 10),
            (10, 15)
        ]

        for min_price, max_price in price_ranges:

            tier_options = options[
                (options["lastPrice"] >= min_price)
                & (options["lastPrice"] <= max_price)
            ]

            if len(tier_options) == 0:
                continue

            tier_options = tier_options.copy()

            tier_options["distance"] = (
                tier_options["strike"]
                - current_price
            ).abs()

            tier_options["score"] = (
                tier_options["openInterest"] * 0.30
                + tier_options["volume"] * 0.25
                - tier_options["distance"] * 10
            )

            tier_options = tier_options.sort_values(
                by="score",
                ascending=False
            )

            best = tier_options.iloc[0]

            return {
                "contract_symbol": str(
                    best["contractSymbol"]
                ),
                "strike": float(
                    best["strike"]
                ),
                "option_price": round(
                    float(best["lastPrice"]),
                    2
                ),
                "expiry": expiry
            }

        return None

    except Exception as e:

        print(
            "OPTION ERROR:",
            e
        )

        return None

        
   # ==================================================
# CREATE TRADE
# ==================================================

def create_trade(symbol):

    signal_type = get_trend(symbol)

    option_data = get_best_option(
        symbol,
        signal_type
    )

    if option_data is None:

        return None

    entry = option_data["option_price"]

    strike = option_data["strike"]

    expiry = option_data["expiry"]

    contract_symbol = option_data["contract_symbol"]

    score_data = get_signal_score(symbol)

    confidence = score_data["confidence"]

    score = score_data["score"]

    if confidence == "NO TRADE":

        return None

    return {

        "symbol": symbol,

        "entry": entry,

        "strike": strike,

        "contract_symbol": contract_symbol,

        "signal_type": signal_type,

        "score": score,

        "confidence": confidence,

        "trade_type": "Real Option",

        "expiry": expiry,

        "tp1": round(entry * 1.3, 2),

        "tp2": round(entry * 1.6, 2),

        "tp3": round(entry * 2.0, 2),

        "sl": round(entry * 0.7, 2),

        "status": "NEW",

        "profit": 0,

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

            stock = yf.Ticker(symbol)

            data = stock.history(period="1y")

            print(name, len(data))

            if len(data) < 200:
                continue

            close = float(data["Close"].iloc[-1])

            ema50 = data["Close"].ewm(span=50).mean().iloc[-1]

            ema200 = data["Close"].ewm(span=200).mean().iloc[-1]

            symbol_score = 0

            if close > ema50:
                symbol_score += 50

            if close > ema200:
                symbol_score += 50

            print(
                f"{name} SCORE =",
                symbol_score
            )

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
        vix = yf.Ticker("^VIX")

        vix_data = vix.history(period="1mo")

        if len(vix_data) > 0:

            vix_close = float(
                vix_data["Close"].iloc[-1]
            )

            if vix_close < 20:

                sentiment_score += 3

            elif vix_close > 25:

                sentiment_score -= 3

            print(
                "VIX =", round(vix_close, 2)
            )

        # GOLD
        gold = yf.Ticker("GLD")

        gold_data = gold.history(period="1mo")

        if len(gold_data) > 0:

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

            print(
                "GOLD =", round(gold_close, 2)
            )

        # BITCOIN
        btc = yf.Ticker("BTC-USD")

        btc_data = btc.history(period="1mo")

        if len(btc_data) > 0:

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

            print(
                "BTC =", round(btc_close, 2)
            )

        print(
            "SENTIMENT SCORE =",
            sentiment_score
        )

        score += sentiment_score

        score = round(score)

        if score >= 75:

            bias = "BULLISH 📈"

        elif score >= 50:

            bias = "NEUTRAL ⚖️"

        else:

            bias = "BEARISH 📉"

        print(
            "MARKET SCORE =",
            score
        )

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
# REAL SCORE ENGINE
# ==================================================

def get_signal_score(symbol):

    try:

        score = 0

        market = get_market_regime()

        print("START:", symbol)
        print("MARKET:", market)

        trend = get_trend(symbol)

        print("TREND:", trend)

        score += round(
            market["market_score"] * 0.35
        )

        print("AFTER MARKET =", score)

        stock = yf.Ticker(symbol)

        data = stock.history(period="6mo")

        print("LEN =", len(data))

        if len(data) < 100:

            print("NOT ENOUGH DATA")

            return {
                "score": 0,
                "confidence": "NO TRADE"
            }

        close = float(data["Close"].iloc[-1])

        ema20 = data["Close"].ewm(span=20).mean().iloc[-1]

        ema50 = data["Close"].ewm(span=50).mean().iloc[-1]

        ema200 = data["Close"].ewm(span=200).mean().iloc[-1]

        structure_score = 0

        if close > ema20:
            structure_score += 30

        if close > ema50:
            structure_score += 35

        if close > ema200:
            structure_score += 35

        print("STRUCTURE SCORE =", structure_score)

        score += round(
            structure_score * 0.30
        )

        print("AFTER STRUCTURE =", score)

     # ==================
        # MOMENTUM LAYER
        # ==================

        rsi_period = 14

        delta = data["Close"].diff()

        gain = delta.where(delta > 0, 0)

        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.rolling(rsi_period).mean()

        avg_loss = loss.rolling(rsi_period).mean()

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

        print("BULL FLAG SCORE =", bullflag_score)

        score += round(
            bullflag_score * 0.05
        )

        print("AFTER BULL FLAG =", score)

        # ==================
        # TREND BONUS
        # ==================

        if "CALL" in trend:

            score += 10

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


# ================= SIGNAL ENGINE =================

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
            signal["signal_type"]
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


if __name__ == "__main__":

    print("🚀 ADEL SMART BOT STARTED")

    while True:

        try:

            show_top_signals()

            print("⏳ Waiting 60 seconds...")

            time.sleep(60)

        except Exception as e:

            print("ERROR:", e)

            time.sleep(60)

            












