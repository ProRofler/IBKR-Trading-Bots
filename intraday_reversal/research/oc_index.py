import numpy as np
import pandas as pd
from intraday_reversal.research.bars import RESULTS_DIR
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 20)

p = pd.read_parquet(RESULTS_DIR / "daily_panel.parquet")
p["era"] = pd.cut(p.day.dt.year, [2005, 2011, 2016, 2021, 2027], labels=["07-11", "12-16", "17-21", "22-26"])
idx = p[p.sym.isin(["SPY", "QQQ", "DIA"])].copy()
idx["dow"] = idx.day.dt.day_of_week
# trading-day of month
idx["tdm"] = idx.groupby([idx.sym, idx.day.dt.to_period("M")]).cumcount() + 1
idx["tdm_rev"] = idx.groupby([idx.sym, idx.day.dt.to_period("M")]).cumcount(ascending=False) + 1


def tab(col, bins=None):
    d = idx.copy()
    d["b"] = pd.cut(d[col], bins) if bins is not None else d[col]
    t = d.groupby(["b", "era"], observed=True).oc.agg(lambda x: f"{x.mean()*1e4:5.1f}({x.mean()/x.std()*np.sqrt(len(x)):4.1f})").unstack()
    t["n"] = d.groupby("b", observed=True).size()
    t["all"] = d.groupby("b", observed=True).oc.agg(lambda x: f"{x.mean()*1e4:5.1f}({x.mean()/x.std()*np.sqrt(len(x)):4.1f})")
    print("---", col)
    print(t)


tab("gap_atr", [-20, -1.5, -1, -0.5, -0.2, 0.2, 0.5, 1, 1.5, 20])
tab("oc1", [-1, -0.02, -0.01, -0.005, 0, 0.005, 0.01, 0.02, 1])
tab("r5", [-1, -0.04, -0.02, 0, 0.02, 0.04, 1])
tab("ibs1", [0, 0.2, 0.4, 0.6, 0.8, 1.01])
tab("ma200", [-1, -0.05, 0, 0.05, 1])
tab("dow")
tab("tdm", [0, 1, 2, 3, 5, 10, 15, 25])
tab("tdm_rev", [0, 1, 2, 3, 5, 25])
