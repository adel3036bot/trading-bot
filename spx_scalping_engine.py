# ==============================================================================
# SPX SCALPING ENGINE - FINAL PRODUCTION READY (V2.3 - ELITE LOCKED)
# ==============================================================================

class SPXScalpingEngine:
    # جدول الأوزان المركزية
    WEIGHTS = {
        "bos": 10, "order_block": 10, "institutional": 10, "fvg": 8,
        "liquidity_sweep": 8, "mitigation": 5, "ema9": 5, "ema20": 5, "ema50": 5,
        "vwap": 5, "volume_conf": 10, "momentum": 7, "retest": 8,
        "pullback": 8, "orb": 7, "zero_reversal": 7, "mtf_conf": 15
    }

    def __init__(self):
        self.reset()

    def reset(self):
        self.state = {"signal": "NO TRADE", "score": 0, "grade": "C", "bias": "NEUTRAL"}

    def evaluate(self, d):
        self.reset()
        
        # استخراج المتغيرات مرة واحدة
        p, ema9, ema20, ema50, vwap = d.get('price', 0), d.get('ema9', 0), d.get('ema20', 0), d.get('ema50', 0), d.get('vwap', 0)
        
        # 1. تحديد الانحياز (Bias) - معتمد على EMA20 و EMA50
        self.state['bias'] = "BULLISH" if (p > ema20 and p > ema50) else ("BEARISH" if (p < ema20 and p < ema50) else "NEUTRAL")
        
        # 2. حساب الدرجات
        w = self.WEIGHTS
        score = 0
        score += w["bos"] if d.get('bos') else 0
        score += w["order_block"] if d.get('order_block') else 0
        score += w["institutional"] if d.get('institutional_candle') else 0
        score += w["fvg"] if d.get('fvg') else 0
        score += w["liquidity_sweep"] if d.get('liquidity_sweep') else 0
        score += w["mitigation"] if d.get('mitigation') else 0
        score += w["ema9"] if p > ema9 else 0
        score += w["ema20"] if p > ema20 else 0
        score += w["ema50"] if p > ema50 else 0
        score += w["vwap"] if (p > vwap if self.state['bias'] == "BULLISH" else p < vwap) else 0
        score += w["volume_conf"] if d.get('volume_confirmation') else 0
        score += w["momentum"] if d.get('momentum_candle') else 0
        score += w["retest"] if d.get('retest') else 0
        score += w["pullback"] if d.get('pullback') else 0
        score += w["orb"] if d.get('orb_breakout') else 0
        score += w["zero_reversal"] if d.get('zero_reversal') else 0
        score += w["mtf_conf"] if d.get('mtf_confirmation') else 0
        
        self.state['score'] = score
        self.state['grade'] = self._get_grade(score)
        self.state['signal'] = self._finalize_signal()
        
        return self.state

    def _get_grade(self, score):
        if score >= 90: return "A+"
        if score >= 80: return "A"
        return "B" if score >= 60 else "C"

    def _finalize_signal(self):
        if self.state['bias'] == "NEUTRAL" or self.state['score'] < 80:
            return "NO TRADE"
        return "CALL" if self.state['bias'] == "BULLISH" else "PUT"

        