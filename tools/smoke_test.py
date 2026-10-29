"""Smoke test: connect to TWS paper, read account data, fetch market data. Places no orders."""
from ib_async import Stock, util

from common.connection import connect

ib = connect(client_id=99)
print("Connected:", ib.isConnected(), "| server version:", ib.client.serverVersion())
print("Accounts:", ib.managedAccounts())

summary = {v.tag: v.value for v in ib.accountSummary() if v.currency in ("USD", "BASE", "")}
for tag in ("NetLiquidation", "TotalCashValue", "BuyingPower", "AvailableFunds"):
    print(f"{tag}: {summary.get(tag)}")

print("Positions:", ib.positions() or "none")
print("Open orders:", ib.openOrders() or "none")

contract = Stock("AAPL", "SMART", "USD")
ib.qualifyContracts(contract)

# 3 = delayed data, so this works without a paid market data subscription
ib.reqMarketDataType(3)
ticker = ib.reqMktData(contract)
ib.sleep(3)
print(f"AAPL quote: bid={ticker.bid} ask={ticker.ask} last={ticker.last} close={ticker.close}")
ib.cancelMktData(contract)

bars = ib.reqHistoricalData(
    contract, endDateTime="", durationStr="5 D", barSizeSetting="1 hour",
    whatToShow="TRADES", useRTH=True,
)
df = util.df(bars)
print(f"Historical bars: {len(df)} rows")
print(df.tail())

ib.disconnect()
