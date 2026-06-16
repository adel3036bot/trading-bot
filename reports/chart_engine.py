import matplotlib.pyplot as plt


class ChartEngine:

    def __init__(self):

        self.chart_color = "blue"

    # ==================================================
    # OPTION CHART
    # ==================================================

    def create_option_chart(self):

        return True

    # ==================================================
    # STOCK CHART
    # ==================================================

    def create_stock_chart(self):

        return True


# ==================================================
# TEST
# ==================================================

if __name__ == "__main__":

    chart_engine = ChartEngine()

    print("Chart Engine Ready")