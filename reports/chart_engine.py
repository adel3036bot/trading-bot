import matplotlib.pyplot as plt


# ==================================================
# CHART ENGINE
# ==================================================

class ChartEngine:

    def __init__(self):

        self.chart_color = "blue"

    # ==================================================
    # OPTION CHART
    # ==================================================

    def create_option_chart(self):

        print(
            "OPTION CHART CREATED"
        )

        return True

    # ==================================================
    # STOCK CHART
    # ==================================================

    def create_stock_chart(self):

        print(
            "STOCK CHART CREATED"
        )

        return True


# ==================================================
# TEST
# ==================================================

if __name__ == "__main__":

    chart_engine = ChartEngine()

    chart_engine.create_option_chart()

    chart_engine.create_stock_chart()

    print(
        "📈 CHART ENGINE READY"
    )


    