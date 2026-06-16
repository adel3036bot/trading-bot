from config import (
    GRADE_A_PLUS,
    GRADE_A,
    GRADE_B_PLUS,
    HOT_SIGNAL_SCORE,
    ELITE_SIGNAL_SCORE
)


class SignalEngine:

    def __init__(self):
        pass

    def get_grade(self, score):

        if score >= ELITE_SIGNAL_SCORE:
            return "ELITE"

        if score >= GRADE_A_PLUS:
            return "A+"

        if score >= GRADE_A:
            return "A"

        if score >= GRADE_B_PLUS:
            return "B+"

        return "NO TRADE"

    def is_hot_signal(self, score):
        return score >= HOT_SIGNAL_SCORE

    def create_signal(self, symbol, score):

        grade = self.get_grade(score)

        signal = {
            "symbol": symbol,
            "score": score,
            "grade": grade,
            "hot_signal": self.is_hot_signal(score)
        }

        return signal


if __name__ == "__main__":

    engine = SignalEngine()

    signal = engine.create_signal(
        symbol="NVDA",
        score=96
    )

    print(signal)