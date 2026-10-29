import numpy as np
import pandas as pd
from intraday_reversal.research.reversal_variants import backtest, report, P

rows = []
base = dict(groups=("index", "etf"), sig="oc1", short_groups=("index", "etf"))
# long only on the index; short on index and other ETFs
def combo(k=0.75, k_short=None, gross=1.0, **kw):
    a = backtest(("index",), "oc1", k=k, short=False, gross=gross, **kw)
    b = backtest(("index", "etf"), "oc1", k=k_short or k, long=False, gross=gross, **kw)
    out = a.add(b, fill_value=0)
    out.attrs = dict(n=a.attrs["n"] + b.attrs["n"], avg_bp=(a.attrs["avg_bp"] * a.attrs["n"] + b.attrs["avg_bp"] * b.attrs["n"]) / (a.attrs["n"] + b.attrs["n"]),
                     exposure=a.attrs["exposure"] + b.attrs["exposure"])
    return out

for k in [0.5, 0.75, 1.0, 1.25]:
    rows.append(report(f"combo k={k}", combo(k)))
for stop in [0.5, 0.75, 1.0, 1.5]:
    rows.append(report(f"combo k=0.75 stop={stop}", combo(0.75, stop_atr=stop)))
for c in [0, 2, 3]:
    rows.append(report(f"combo k=0.75 cost={c}bp", combo(0.75, cost_bps=c)))
for sig in ["ibs", "both"]:
    a = backtest(("index",), sig, short=False); b = backtest(("index", "etf"), sig, long=False)
    out = a.add(b, fill_value=0); out.attrs = dict(n=a.attrs["n"] + b.attrs["n"], avg_bp=np.nan, exposure=a.attrs["exposure"] + b.attrs["exposure"])
    rows.append(report(f"combo sig={sig}", out))
for s in ["SPY", "QQQ", "DIA"]:
    rows.append(report(f"{s} long+short k=0.75", backtest(("index",), "oc1", syms=[s], k=0.75)))
    rows.append(report(f"{s} long k=0.75", backtest(("index",), "oc1", syms=[s], k=0.75, short=False)))
for s in ["SMH", "XLK", "XLF", "XLI", "GLD", "SLV", "GDX", "ITA", "URA", "SOXX"]:
    rows.append(report(f"{s} short k=0.75", backtest(("etf",), "oc1", syms=[s], k=0.75, long=False)))
print(pd.DataFrame(rows).to_string(index=False))
