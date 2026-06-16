from config import MARKET_INDEXES


class MarketEngine:

    def __init__(self):
        self.market_score = 0
        self.market_direction = "NEUTRAL"

    def calculate_market_score(self):
        """
        سيتم تطويرها لاحقاً
        """
        return self.market_score

    def get_market_direction(self):
        """
        سيتم تطويرها لاحقاً
        """
        return self.market_direction


if __name__ == "__main__":

    engine = MarketEngine()

    print("ADEL SMART BOT")
    print("Market Direction:", engine.get_market_direction())
    print("Market Score:", engine.calculate_market_score())