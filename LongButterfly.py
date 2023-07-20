import ibapi
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import *
import threading
import time

# Contract Samples
class ContractSamples:
    @staticmethod
    def USStockAtSmart(symbol):
        contract = Contract()
        contract.symbol = symbol
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"
        return contract

# Interactive Brokers Connection
class IBApi(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.nextValidOrderId = None

    def nextValidId(self, orderId: int):
        super().nextValidId(orderId)
        self.nextValidOrderId = orderId

    def error(self, reqId: int, errorCode: int, errorString: str):
        print("Error:", errorCode, errorString)

    def orderStatus(self, orderId: int, status: str, filled: float,
                    remaining: float, avgFillPrice: float, permId: int,
                    parentId: int, lastFillPrice: float, clientId: int,
                    whyHeld: str):
        print("Order Status:", status)

# Butterfly Strategy
class LongButterfly:
    def __init__(self, symbol, lower_strike, middle_strike, higher_strike, quantity):
        self.symbol = symbol
        self.lower_strike = lower_strike
        self.middle_strike = middle_strike
        self.higher_strike = higher_strike
        self.quantity = quantity
        self.ib = IBApi()
        self.ib.connect("127.0.0.1", 7497, 0)
        ib_thread = threading.Thread(target=self.ib.run, daemon=True)
        ib_thread.start()
        time.sleep(1)
        self.next_order_id = self.ib.nextValidOrderId  # Assign the next valid order ID

    def create_contract(self, strike):
        contract = ContractSamples.USStockAtSmart(self.symbol)
        contract.strike = strike
        contract.right = "C"  # Call option
        contract.lastTradeDateOrContractMonth = ""  # Specify expiration date if desired
        contract.secType = "OPT"
        contract.exchange = "SMART"
        contract.currency = "USD"
        return contract

    def create_order(self, action, quantity):
        order = Order()
        order.action = action
        order.totalQuantity = quantity
        order.orderType = "LMT"
        order.lmtPrice = 0.0  # Set your desired limit price
        return order

    def place_butterfly_order(self):
        # Create contracts
        lower_contract = self.create_contract(self.lower_strike)
        middle_contract = self.create_contract(self.middle_strike)
        higher_contract = self.create_contract(self.higher_strike)

        # Create orders
        buy_lower = self.create_order("BUY", self.quantity)
        sell_middle = self.create_order("SELL", 2 * self.quantity)
        buy_higher = self.create_order("BUY", self.quantity)

        # Place orders
        self.ib.placeOrder(self.next_order_id, lower_contract, buy_lower)
        self.next_order_id += 1
        self.ib.placeOrder(self.next_order_id, middle_contract, sell_middle)
        self.next_order_id += 1
        self.ib.placeOrder(self.next_order_id, higher_contract, buy_higher)

        # Increment order ID
        self.next_order_id += 1

    def cancel_open_orders(self):
        self.ib.reqGlobalCancel()

    def close_connection(self):
        self.ib.disconnect()

# Usage Example
if __name__ == "__main__":
    # Create a long butterfly strategy object
    butterfly = LongButterfly("AAPL", 140, 150, 160, 1)

    # Place the butterfly order
    butterfly.place_butterfly_order()

    # Wait for some time to allow the order to be executed
    time.sleep(30)

    # Cancel any open orders (if needed)
    butterfly.cancel_open_orders()

    # Close the connection
    butterfly.close_connection()
