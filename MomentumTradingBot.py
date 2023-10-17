import threading
import time
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import Order
from ibapi.scanner import ScannerSubscription
from ta import momentum, trend

class IBApi(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.nextOrderId = 1
        self.order_filled = False  # Flag to track if an order has been filled

    def nextValidId(self, orderId: int):
        super().nextValidId(orderId)
        self.nextOrderId = orderId

    def error(self, reqId: int, errorCode: int, errorString: str):
        print("Error:", errorCode, errorString)

    def orderStatus(
        self,
        orderId: int,
        status: str,
        filled: float,
        remaining: float,
        avgFillPrice: float,
        permId: int,
        parentId: int,
        lastFillPrice: float,
        clientId: int,
        whyHeld: str,
    ):
        if filled > 0:
            self.order_filled = True  # Set the order_filled flag to True when the order is filled

class Bot:
    ib = None
    reqId = 1
    shares = 200
    profit_target = 0.05  # 5%
    stop_loss = -0.03  # -3%
    positions = {}  # Dictionary to track positions
    buy_prices = {}  # Dictionary to track buy prices

    def __init__(self):
        self.ib = IBApi()
        self.ib.connect("127.0.0.1", 7497, clientId=1)  # Connect to the Interactive Brokers TWS or IB Gateway
        ib_thread = threading.Thread(target=self.ib.run, daemon=True)
        ib_thread.start()
        time.sleep(1)

    def run(self):
        while True:
            self.scan_stocks()  # Perform stock scanning
            self.show_positions()  # Display holding positions
            time.sleep(15)  # Scan interval set to every 15 seconds

    def scan_stocks(self):
        self.scan_filter_stocks()  # Perform stock scanning with filtering

    def scan_filter_stocks(self):
        subscription = ScannerSubscription()
        subscription.instrument = "STK"
        subscription.locationCode = "STK.US.MAJOR"
        subscription.currency = "USD"
        subscription.scanCode = "TOP_PERC_GAIN"  # Scan code for Top Gainners
        subscription.numberOfRows = 50
        subscription.abovePrice = 1
        subscription.belowPrice = 10
        subscription.aboveVolume = 1000000
        subscription.marketCapBelow = 20000000
        subscription.marketCapAbove = 5000000

        self.ib.reqScannerSubscription(self.reqId, subscription, [], [])  # Request scanner subscription

        self.reqId += 1  # Increment the request ID after each request

    def scannerData(self, reqId, rank, contractDetails, distance, benchmark, projection, legsStr):
        symbol = contractDetails.contract.symbol
        market_cap = contractDetails.contract.longName.split('|')[2]  # Assuming the market cap is included in the longName field

        # Create contract for scanning
        contract = Contract()
        contract.symbol = symbol
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"

        # Request market data for the stock
        self.ib.reqMktData(self.reqId, contract, "", False, False, [])

        self.reqId += 1  # Increment the request ID after each request

    def historicalData(self, reqId, bar):
        # Process the scanned stock data
        symbol = bar.contract.symbol  # Retrieve the symbol of the scanned stock
        close_prices = [b.close for b in bar]

        # Calculate RSI
        rsi = momentum.RSIIndicator(close_prices)
        current_rsi = rsi.rsi().iloc[-1]

        # Calculate MACD
        macd = trend.MACD(close_prices)
        is_macd_green = macd.macd_diff()[-1] > 0

        # Calculate price change percentage over the past 5 minutes
        price_change_pct = (bar.close - close_prices[0]) / close_prices[0] * 100

        # Calculate 200 EMA
        ema200 = trend.EMAIndicator(close_prices, window=200)
        is_above_ema200 = bar.close > ema200.ema_indicator().iloc[-1]

        # Check Criteria
        if (
            bar.close <= 10
            and (30 <= current_rsi <= 70)
            and is_macd_green
            and price_change_pct >= 10
            and is_above_ema200
        ):
            print("Scanned stock:", symbol)
            self.buy_stock(symbol)  # Buy the stock if it meets the conditions

    def buy_stock(self, symbol):
        # Create contract for the stock to be bought
        contract = Contract()
        contract.symbol = symbol
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"

        # Create order for buying the stock
        order = Order()
        order.action = "BUY"
        order.orderType = "MKT"
        order.totalQuantity = self.shares

        # Place the order
        self.ib.placeOrder(self.ib.nextOrderId, contract, order)

        # Wait for the order to be filled
        self.ib.order_filled = False
        while not self.ib.order_filled:
            time.sleep(1)

        self.positions[symbol] = True
        self.buy_prices[symbol] = self.ib.last_trade_price
        print("Bought", symbol, "at", self.ib.last_trade_price)

    def on_bar_update(self, reqId, time, open_, high, low, close, volume, wap, count):
        for symbol in list(self.positions.keys()):
            if reqId == self.reqId and self.positions[symbol]:
                last_trade_price = close
                if symbol in self.buy_prices:
                    buy_price = self.buy_prices[symbol]
                    if last_trade_price >= buy_price * (1 + self.profit_target):  # Check profit target
                        self.sell_stock(symbol)
                    elif last_trade_price <= buy_price * (1 + self.stop_loss):  # Check stop loss
                        self.sell_stock(symbol)

    def sell_stock(self, symbol):
        # Create contract for the stock to be sold
        contract = Contract()
        contract.symbol = symbol
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"

        # Create order for selling the stock
        order = Order()
        order.action = "SELL"
        order.orderType = "MKT"
        order.totalQuantity = self.shares

        # Place the order
        self.ib.placeOrder(self.ib.nextOrderId, contract, order)

        # Wait for the order to be filled
        self.ib.order_filled = False
        while not self.ib.order_filled:
            time.sleep(1)

        sold_price = self.ib.last_trade_price
        profit = (sold_price - self.buy_prices[symbol]) * self.shares
        print("Sold", symbol, "at", sold_price)
        print("Profit:", profit)
        print()

        del self.positions[symbol]
        del self.buy_prices[symbol]

    def show_positions(self):
        if self.positions:
            print("Holding Positions:")
            print("Symbol\t\tPurchased Price\t\tShares\t\tProfit/Loss ($)")

            for symbol, buy_price in self.buy_prices.items():
                current_price = self.ib.reqMktData(
                    self.reqId,
                    Contract(symbol=symbol, exchange="SMART", currency="USD"),
                    "",
                    False,
                    False,
                    [],
                )
                current_price = current_price.marketPrice()
                shares = self.shares
                pnl = (current_price - buy_price) * shares

                print(f"{symbol}\t\t{buy_price}\t\t\t{shares}\t\t\t{pnl}")

            print()
        else:
            print("No positions currently held.")
            print()

    def disconnect(self):
        self.ib.disconnect()


if __name__ == "__main__":
    bot = Bot()
    bot.run()
