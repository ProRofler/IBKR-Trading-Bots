import numpy as np
import pandas as pd
from intraday_reversal.research.bars import RESULTS_DIR

p = pd.read_parquet(RESULTS_DIR / "daily_panel.parquet")
p["era"] = pd.cut(p.day.dt.year, [2005, 2011, 2016, 2021, 2027], labels=["07-11", "12-16", "17-21", "22-26"])
p["xoc"] = p.oc - p.groupby("day").oc.transform("mean")


def sort_table(d, sig, q=5):
    d = d.dropna(subset=[sig, "oc"]).copy()
    d = d[d.groupby("day").sym.transform("size") >= 20]
    d["b"] = d.groupby("day")[sig].transform(lambda x: pd.qcut(x.rank(method="first"), q, labels=False))
    t = d.groupby(["day", "b"]).oc.mean().unstack()
    ls = t[q - 1] - t[0]
    era = d.groupby("day").era.first()
    by_era = ls.groupby(era, observed=True).apply(lambda x: f"{x.mean()*1e4:5.1f}({x.mean()/x.std()*np.sqrt(len(x)):4.1f})")
    return (" ".join(f"{m:5.1f}" for m in t.mean() * 1e4)
            + f" | H-L {ls.mean()*1e4:5.1f}bp t={ls.mean()/ls.std()*np.sqrt(len(ls)):5.2f} | " + " ".join(by_era.values))


stk = p[~p.etf]
print("quintile mean open->close bp (low..high) | high-low spread | by era 07-11 12-16 17-21 22-26")
for sig in ["gap", "gap_atr", "oc1", "on1", "r5", "r20", "r250", "ibs1", "rsi2", "ma200", "a"]:
    print(f"{sig:8}", sort_table(stk, sig))
