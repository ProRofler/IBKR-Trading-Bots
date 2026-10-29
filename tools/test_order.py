"""Order round-trip test: place a 1-share AAPL buy limit far below market, confirm TWS accepts it, then cancel."""
from ib_async import LimitOrder, Stock

from common.connection import connect

ib = connect(client_id=97)
ib.errorEvent += lambda reqId, code, msg, contract: print(f"  [TWS {code}] {msg}")

contract = Stock("AAPL", "SMART", "USD")
ib.qualifyContracts(contract)

# Price the limit at half of the last daily close so it can't fill
bars = ib.reqHistoricalData(
    contract, endDateTime="", durationStr="2 D", barSizeSetting="1 day",
    whatToShow="TRADES", useRTH=True,
)
limit_price = round(bars[-1].close * 0.5, 2)
print(f"Last close {bars[-1].close}, placing BUY 1 @ {limit_price}")

trade = ib.placeOrder(contract, LimitOrder("BUY", 1, limit_price, tif="DAY"))
# Wait for TWS to acknowledge before cancelling; a cancel sent while still PendingSubmit can be lost
for _ in range(60):
    ib.sleep(0.5)
    if trade.orderStatus.status in ("Submitted", "PreSubmitted") or trade.isDone():
        break
print(f"Order {trade.order.orderId} status: {trade.orderStatus.status}")

ib.cancelOrder(trade.order)
for _ in range(20):
    ib.sleep(0.5)
    if trade.isDone():
        break
print(f"After cancel: {trade.orderStatus.status}")
for entry in trade.log:
    print(f"  {entry.time:%H:%M:%S} {entry.status} {entry.message}")

ib.reqAllOpenOrders()
ib.sleep(1)
leftover = [(t.order.orderId, t.orderStatus.status) for t in ib.openTrades() if not t.isDone()]
print("Open orders left in TWS:", leftover or "none")

ib.disconnect()
