# ============================================================
# ADEL SMART BOT
# IBKR GATEWAY - FULL DATA SOURCE TEST
# ============================================================
#
# اختبار مستقل تمامًا عن ADEL SMART BOT
#
# لا يستورد:
#   - ADEL
#   - Telegram
#   - source_engine
#   - data_engine
#
# لا ينفذ:
#   - شراء
#   - بيع
#   - placeOrder
#
# الاختبارات:
#   1) الاتصال بـ IB Gateway
#   2) حالة الحساب
#   3) بيانات SPY
#   4) بيانات AAPL
#   5) بيانات تاريخية
#   6) VIX
#   7) SPX
#   8) معلومات خيارات SPY
#   9) بيانات سوق لعقد خيار
#
# IB Gateway:
#   LIVE  = 4001
#   PAPER = 4002
#
# ============================================================

import sys
import time
import threading
from datetime import datetime

from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract


# ============================================================
# SETTINGS
# ============================================================

HOST = "127.0.0.1"

# أنت تستخدم Live IB Gateway
PORT = 4001

CLIENT_ID = 77

# مهلة انتظار كل اختبار
TIMEOUT = 12

# هل نطلب بيانات السوق؟
REQUEST_MARKET_DATA = True


# ============================================================
# HELPERS
# ============================================================

def now():
    return datetime.now().strftime("%H:%M:%S")


def section(title):
    print()
    print("=" * 75)
    print(title)
    print("=" * 75)


def safe_float(value):
    try:
        if value is None:
            return None

        if value == "":
            return None

        value = float(value)

        # IBKR يستخدم أحيانًا -1 أو NaN
        if value != value:
            return None

        return value

    except Exception:
        return None


# ============================================================
# IBKR TEST CLIENT
# ============================================================

class IBKRTest(EWrapper, EClient):

    def __init__(self):
        EClient.__init__(self, self)

        self.connected_event = threading.Event()
        self.next_order_id_event = threading.Event()

        self.next_valid_id = None

        self.errors = []

        # ----------------------------------------------------
        # Market Data
        # ----------------------------------------------------

        self.market_data = {}

        self.market_data_events = {}

        # ----------------------------------------------------
        # Historical Data
        # ----------------------------------------------------

        self.historical_data = {}

        self.historical_events = {}

        # ----------------------------------------------------
        # Contract Details
        # ----------------------------------------------------

        self.contract_details_data = {}

        self.contract_details_events = {}

        # ----------------------------------------------------
        # Option Parameters
        # ----------------------------------------------------

        self.option_parameters = {}

        self.option_parameters_events = {}

        # ----------------------------------------------------
        # Request IDs
        # ----------------------------------------------------

        self.req_counter = 1000

    # ========================================================
    # REQUEST ID
    # ========================================================

    def new_req_id(self):
        self.req_counter += 1
        return self.req_counter

    # ========================================================
    # CONNECTION
    # ========================================================

    def connectAck(self):
        print(f"[{now()}] ✅ connectAck() received")

    def nextValidId(self, orderId):
        self.next_valid_id = orderId

        print(
            f"[{now()}] ✅ nextValidId received: {orderId}"
        )

        self.next_order_id_event.set()
        self.connected_event.set()

    # ========================================================
    # ERRORS
    # ========================================================

    def error(
        self,
        reqId,
        errorCode,
        errorString,
        advancedOrderRejectJson=""
    ):
        message = (
            f"reqId={reqId} | "
            f"code={errorCode} | "
            f"{errorString}"
        )

        print(f"[{now()}] ⚠️ IBKR: {message}")

        self.errors.append(
            {
                "reqId": reqId,
                "code": errorCode,
                "message": errorString,
            }
        )

    # ========================================================
    # MARKET DATA
    # ========================================================

    def tickPrice(
        self,
        reqId,
        tickType,
        price,
        attrib
    ):
        if reqId not in self.market_data:
            self.market_data[reqId] = {}

        data = self.market_data[reqId]

        # IBKR tick types
        #
        # 1  = BID
        # 2  = ASK
        # 4  = LAST
        # 6  = HIGH
        # 7  = LOW
        # 9  = CLOSE
        # 14 = OPEN
        # 37 = MARK

        if tickType == 1:
            data["bid"] = safe_float(price)

        elif tickType == 2:
            data["ask"] = safe_float(price)

        elif tickType == 4:
            data["last"] = safe_float(price)

        elif tickType == 6:
            data["high"] = safe_float(price)

        elif tickType == 7:
            data["low"] = safe_float(price)

        elif tickType == 9:
            data["close"] = safe_float(price)

        elif tickType == 14:
            data["open"] = safe_float(price)

        elif tickType == 37:
            data["mark"] = safe_float(price)

    def tickSize(
        self,
        reqId,
        tickType,
        size
    ):
        if reqId not in self.market_data:
            self.market_data[reqId] = {}

        data = self.market_data[reqId]

        # 0 = BID SIZE
        # 3 = ASK SIZE
        # 5 = LAST SIZE
        # 8 = VOLUME

        if tickType == 0:
            data["bid_size"] = size

        elif tickType == 3:
            data["ask_size"] = size

        elif tickType == 5:
            data["last_size"] = size

        elif tickType == 8:
            data["volume"] = size

    def tickString(
        self,
        reqId,
        tickType,
        value
    ):
        if reqId not in self.market_data:
            self.market_data[reqId] = {}

        # 45 = LAST_TIMESTAMP
        if tickType == 45:
            self.market_data[reqId]["last_timestamp"] = value

    def tickSnapshotEnd(self, reqId):
        print(
            f"[{now()}] Snapshot finished: reqId={reqId}"
        )

        event = self.market_data_events.get(reqId)

        if event:
            event.set()

    # ========================================================
    # HISTORICAL DATA
    # ========================================================

    def historicalData(
        self,
        reqId,
        bar
    ):
        if reqId not in self.historical_data:
            self.historical_data[reqId] = []

        self.historical_data[reqId].append(
            {
                "date": bar.date,
                "open": bar.open,
                "high": bar.high,
                "low": bar.low,
                "close": bar.close,
                "volume": bar.volume,
                "average": bar.average,
                "barCount": bar.barCount,
            }
        )

    def historicalDataEnd(
        self,
        reqId,
        start,
        end
    ):
        print(
            f"[{now()}] Historical data completed "
            f"reqId={reqId}"
        )

        event = self.historical_events.get(reqId)

        if event:
            event.set()

    # ========================================================
    # CONTRACT DETAILS
    # ========================================================

    def contractDetails(
        self,
        reqId,
        contractDetails
    ):
        if reqId not in self.contract_details_data:
            self.contract_details_data[reqId] = []

        self.contract_details_data[reqId].append(
            contractDetails
        )

    def contractDetailsEnd(self, reqId):
        print(
            f"[{now()}] Contract details completed "
            f"reqId={reqId}"
        )

        event = self.contract_details_events.get(reqId)

        if event:
            event.set()

    # ========================================================
    # OPTION PARAMETERS
    # ========================================================

    def securityDefinitionOptionParameter(
        self,
        reqId,
        exchange,
        underlyingConId,
        tradingClass,
        multiplier,
        expirations,
        strikes
    ):
        self.option_parameters[reqId] = {
            "exchange": exchange,
            "underlyingConId": underlyingConId,
            "tradingClass": tradingClass,
            "multiplier": multiplier,
            "expirations": sorted(list(expirations)),
            "strikes": sorted(list(strikes)),
        }

    def securityDefinitionOptionParameterEnd(
        self,
        reqId
    ):
        print(
            f"[{now()}] Option parameters completed "
            f"reqId={reqId}"
        )

        event = self.option_parameters_events.get(reqId)

        if event:
            event.set()


# ============================================================
# CONTRACT BUILDERS
# ============================================================

def stock_contract(symbol):
    contract = Contract()

    contract.symbol = symbol
    contract.secType = "STK"
    contract.exchange = "SMART"
    contract.currency = "USD"

    return contract


def index_contract(symbol):
    contract = Contract()

    contract.symbol = symbol
    contract.secType = "IND"

    # SMART is generally not appropriate for indexes.
    # Use CBOE for SPX/VIX where available.
    contract.exchange = "CBOE"

    contract.currency = "USD"

    return contract


# ============================================================
# MARKET DATA TEST
# ============================================================

def request_market_data(
    app,
    contract,
    name
):
    section(f"MARKET DATA TEST — {name}")

    req_id = app.new_req_id()

    app.market_data[req_id] = {}

    event = threading.Event()

    app.market_data_events[req_id] = event

    print(
        f"[{now()}] Requesting market data..."
    )

    try:
        app.reqMktData(
            req_id,
            contract,
            "",
            False,
            False,
            []
        )

    except Exception as error:
        print(
            f"[{now()}] ❌ reqMktData error: {error}"
        )
        return None

    event.wait(TIMEOUT)

    # Give asynchronous ticks a little time.
    time.sleep(1)

    try:
        app.cancelMktData(req_id)
    except Exception:
        pass

    data = app.market_data.get(
        req_id,
        {}
    )

    print()
    print("RESULT:")

    if not data:
        print("❌ No market data received")
        print(
            "قد تكون البيانات غير مشتركة أو العقد غير متاح."
        )

        return None

    for key, value in data.items():
        print(
            f"  {key:16}: {value}"
        )

    return data


# ============================================================
# HISTORICAL DATA TEST
# ============================================================

def request_historical_data(
    app,
    contract,
    name
):
    section(f"HISTORICAL DATA TEST — {name}")

    req_id = app.new_req_id()

    app.historical_data[req_id] = []

    event = threading.Event()

    app.historical_events[req_id] = event

    print(
        f"[{now()}] Requesting historical data..."
    )

    try:
        app.reqHistoricalData(
            req_id,
            contract,
            "",
            "5 D",
            "1 hour",
            "TRADES",
            1,
            1,
            False,
            []
        )

    except Exception as error:
        print(
            f"[{now()}] ❌ Historical request error: "
            f"{error}"
        )
        return []

    event.wait(TIMEOUT + 5)

    bars = app.historical_data.get(
        req_id,
        []
    )

    print()
    print(
        f"Received bars: {len(bars)}"
    )

    if bars:
        print()
        print("LAST 5 BARS:")

        for bar in bars[-5:]:
            print(
                f"{bar['date']} | "
                f"O={bar['open']} | "
                f"H={bar['high']} | "
                f"L={bar['low']} | "
                f"C={bar['close']} | "
                f"V={bar['volume']}"
            )
    else:
        print(
            "❌ No historical data received."
        )

    return bars


# ============================================================
# CONTRACT DETAILS
# ============================================================

def request_contract_details(
    app,
    contract,
    name
):
    section(f"CONTRACT DETAILS — {name}")

    req_id = app.new_req_id()

    app.contract_details_data[req_id] = []

    event = threading.Event()

    app.contract_details_events[req_id] = event

    try:
        app.reqContractDetails(
            req_id,
            contract
        )

    except Exception as error:
        print(
            f"[{now()}] ❌ Contract request error: "
            f"{error}"
        )
        return []

    event.wait(TIMEOUT)

    details = app.contract_details_data.get(
        req_id,
        []
    )

    print(
        f"Contracts received: {len(details)}"
    )

    for item in details[:5]:

        c = item.contract

        print()
        print(
            f"conId       : {c.conId}"
        )

        print(
            f"symbol      : {c.symbol}"
        )

        print(
            f"secType     : {c.secType}"
        )

        print(
            f"exchange    : {c.exchange}"
        )

        print(
            f"currency    : {c.currency}"
        )

        print(
            f"tradingClass: {c.tradingClass}"
        )

    return details


# ============================================================
# OPTION CHAIN TEST
# ============================================================

def request_option_chain(
    app,
    underlying_symbol
):
    section(
        f"OPTIONS CHAIN TEST — {underlying_symbol}"
    )

    # First resolve underlying contract.
    contract = stock_contract(
        underlying_symbol
    )

    details = request_contract_details(
        app,
        contract,
        underlying_symbol
    )

    if not details:
        print(
            "\n❌ Could not resolve underlying contract."
        )
        return None

    underlying = details[0].contract

    print()
    print(
        f"Underlying conId: {underlying.conId}"
    )

    req_id = app.new_req_id()

    app.option_parameters[req_id] = {}

    event = threading.Event()

    app.option_parameters_events[req_id] = event

    try:
        app.reqSecDefOptParams(
            req_id,
            underlying.symbol,
            "",
            underlying.secType,
            underlying.conId
        )

    except Exception as error:
        print(
            f"\n❌ Option chain request error: {error}"
        )
        return None

    event.wait(TIMEOUT + 5)

    result = app.option_parameters.get(
        req_id
    )

    if not result:
        print(
            "\n❌ No option chain data received."
        )

        return None

    print()
    print("OPTION CHAIN RESULT:")
    print(
        f"Exchange       : {result.get('exchange')}"
    )
    print(
        f"Trading Class  : {result.get('tradingClass')}"
    )
    print(
        f"Multiplier     : {result.get('multiplier')}"
    )

    expirations = result.get(
        "expirations",
        []
    )

    strikes = result.get(
        "strikes",
        []
    )

    print(
        f"Expirations    : {len(expirations)}"
    )

    print(
        f"Strikes        : {len(strikes)}"
    )

    if expirations:
        print()
        print("FIRST EXPIRATIONS:")

        for expiration in expirations[:10]:
            print(
                f"  {expiration}"
            )

    if strikes:
        print()
        print("FIRST STRIKES:")

        for strike in strikes[:20]:
            print(
                f"  {strike}"
            )

    return result


# ============================================================
# OPTION CONTRACT TEST
# ============================================================

def request_option_contract_data(
    app,
    underlying_symbol,
    expiration,
    strike,
    right
):
    section(
        "OPTION CONTRACT MARKET DATA TEST"
    )

    contract = Contract()

    contract.symbol = underlying_symbol
    contract.secType = "OPT"
    contract.exchange = "SMART"
    contract.currency = "USD"

    contract.lastTradeDateOrContractMonth = expiration
    contract.strike = float(strike)
    contract.right = right

    # Let IBKR resolve the contract.
    contract.multiplier = "100"

    print()
    print("OPTION CONTRACT:")
    print(
        f"Symbol     : {underlying_symbol}"
    )
    print(
        f"Expiration : {expiration}"
    )
    print(
        f"Strike     : {strike}"
    )
    print(
        f"Right      : {right}"
    )

    details = request_contract_details(
        app,
        contract,
        "OPTION"
    )

    if not details:
        print(
            "\n❌ Option contract could not be resolved."
        )
        return None

    resolved = details[0].contract

    print()
    print("RESOLVED OPTION:")
    print(
        f"conId       : {resolved.conId}"
    )
    print(
        f"symbol      : {resolved.symbol}"
    )
    print(
        f"expiry      : {resolved.lastTradeDateOrContractMonth}"
    )
    print(
        f"strike      : {resolved.strike}"
    )
    print(
        f"right       : {resolved.right}"
    )
    print(
        f"exchange    : {resolved.exchange}"
    )
    print(
        f"tradingClass: {resolved.tradingClass}"
    )

    return request_market_data(
        app,
        resolved,
        "OPTION"
    )


# ============================================================
# CONNECTION TEST
# ============================================================

def connect_to_ibkr():
    section(
        "IBKR GATEWAY CONNECTION TEST"
    )

    print(
        f"Host     : {HOST}"
    )

    print(
        f"Port     : {PORT}"
    )

    print(
        f"Client ID: {CLIENT_ID}"
    )

    app = IBKRTest()

    try:
        app.connect(
            HOST,
            PORT,
            CLIENT_ID
        )

    except Exception as error:
        print()
        print(
            f"❌ Connection attempt failed: {error}"
        )

        return None

    # Start IBKR network loop.
    thread = threading.Thread(
        target=app.run,
        daemon=True
    )

    thread.start()

    print()
    print(
        "Waiting for IBKR Gateway..."
    )

    connected = app.connected_event.wait(
        TIMEOUT
    )

    if not connected:

        print()
        print(
            "❌ IB Gateway did not complete API connection."
        )

        print()
        print(
            "Possible reasons:"
        )

        print(
            "1) Gateway is not fully logged in."
        )

        print(
            "2) API server is not connected."
        )

        print(
            "3) Port 4001 is not available."
        )

        print(
            "4) IBKR rejected the API session."
        )

        try:
            app.disconnect()
        except Exception:
            pass

        return None

    print()
    print(
        "✅ IBKR API CONNECTION SUCCESS"
    )

    return app


# ============================================================
# MAIN TEST
# ============================================================

def main():

    section(
        "ADEL SMART BOT — IBKR DATA SOURCE TEST"
    )

    print()
    print(
        "هذا الاختبار مستقل تمامًا عن ADEL."
    )

    print(
        "لا توجد أوامر شراء أو بيع."
    )

    print(
        "لا يوجد placeOrder()."
    )

    print(
        "لا يوجد Telegram."
    )

    print(
        "لا يتم تعديل أي ملف من المشروع."
    )

    # --------------------------------------------------------
    # CONNECTION
    # --------------------------------------------------------

    app = connect_to_ibkr()

    if app is None:

        section(
            "TEST STOPPED"
        )

        print(
            "❌ لم يتم إنشاء اتصال API."
        )

        return

    try:

        # ====================================================
        # STOCK DATA — SPY
        # ====================================================

        spy = stock_contract(
            "SPY"
        )

        request_market_data(
            app,
            spy,
            "SPY"
        )

        # ====================================================
        # STOCK DATA — AAPL
        # ====================================================

        aapl = stock_contract(
            "AAPL"
        )

        request_market_data(
            app,
            aapl,
            "AAPL"
        )

        # ====================================================
        # HISTORICAL SPY
        # ====================================================

        request_historical_data(
            app,
            spy,
            "SPY"
        )

        # ====================================================
        # CONTRACT DETAILS
        # ====================================================

        request_contract_details(
            app,
            spy,
            "SPY"
        )

        # ====================================================
        # VIX
        # ====================================================

        vix = index_contract(
            "VIX"
        )

        request_market_data(
            app,
            vix,
            "VIX"
        )

        # ====================================================
        # SPX
        # ====================================================

        spx = index_contract(
            "SPX"
        )

        request_market_data(
            app,
            spx,
            "SPX"
        )

        # ====================================================
        # OPTIONS
        # ====================================================

        option_chain = request_option_chain(
            app,
            "SPY"
        )

        # ====================================================
        # OPTION CONTRACT
        # ====================================================

        if option_chain:

            expirations = option_chain.get(
                "expirations",
                []
            )

            strikes = option_chain.get(
                "strikes",
                []
            )

            if expirations and strikes:

                # نختار أقرب expiry موجود في البيانات.
                expiration = expirations[0]

                # نختار strike قريبًا من السعر الحالي.
                spy_price_data = None

                # نبحث عن آخر طلبات SPY.
                for req_id, data in app.market_data.items():

                    if data.get("last"):

                        spy_price_data = data
                        break

                if spy_price_data:

                    reference_price = (
                        spy_price_data.get("last")
                        or spy_price_data.get("close")
                    )

                else:

                    reference_price = None

                selected_strike = None

                if reference_price:

                    selected_strike = min(
                        strikes,
                        key=lambda x: abs(
                            float(x) -
                            float(reference_price)
                        )
                    )

                else:

                    selected_strike = strikes[
                        len(strikes) // 2
                    ]

                request_option_contract_data(
                    app,
                    "SPY",
                    expiration,
                    selected_strike,
                    "C"
                )

        # ====================================================
        # FINAL REPORT
        # ====================================================

        section(
            "FINAL IBKR DATA SOURCE REPORT"
        )

        print()
        print(
            "إذا نجحت الاختبارات أعلاه فهذا يعني أن"
        )

        print(
            "IBKR يستطيع توفير جزء من البيانات المطلوبة."
        )

        print()
        print(
            "سنحدد بعد النتيجة:"
        )

        print(
            "1) Stock data"
        )

        print(
            "2) Historical data"
        )

        print(
            "3) Index/VIX data"
        )

        print(
            "4) Options chain"
        )

        print(
            "5) Option market data"
        )

        print()
        print(
            "⚠️ ظهور Delayed أو عدم ظهور السعر لا يعني "
            "أن IBKR لا يدعم البيانات."
        )

        print(
            "قد يعني فقط أن الاشتراك المناسب غير موجود."
        )

    finally:

        print()
        print(
            "Disconnecting from IBKR..."
        )

        try:
            app.disconnect()
        except Exception:
            pass

        print(
            "✅ Test finished."
        )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    try:
        main()

    except KeyboardInterrupt:

        print()
        print(
            "⚠️ Test interrupted by user."
        )

    except Exception as error:

        print()
        print(
            "❌ UNEXPECTED ERROR"
        )

        print(
            repr(error)
        )