"""Time-series: next-day open->close after oversold/overbought conditions, by instrument group and era."""
import numpy as np
import pandas as pd
from intraday_reversal.research.bars import RESULTS_DIR
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 20)

p = pd.read_parquet(RESULTS_DIR / "daily_panel.parquet")
p["era"] = pd.cut(p.day.dt.year, [2005, 2011, 2016, 2021, 2027], labels=["07-11", "12-16", "17-21", "22-26"])
p["grp"] = np.where(p.sym.isin(["SPY", "QQQ", "DIA"]), "index", np.where(p.etf, "etf", "stock"))
p["oc1_atr"] = p.oc1 / p.a
p["r5_atr"] = p.r5 / (p.a * np.sqrt(5))
f = lambda x: f"{x.mean()*1e4:5.1f}({x.mean()/x.std()*np.sqrt(len(x)):4.1f})"


def tab(col, bins):
    d = p.copy()
    d["b"] = pd.cut(d[col], bins)
    for grp, g in d.groupby("grp"):
        t = g.groupby(["b", "era"], observed=True).oc.agg(f).unstack()
        t["n"] = g.groupby("b", observed=True).size()
        t["all"] = g.groupby("b", observed=True).oc.agg(f)
        print(f"--- {col} | {grp}")
        print(t)


tab("oc1_atr", [-20, -1.5, -1, -0.5, 0, 0.5, 1, 1.5, 20])
tab("r5_atr", [-20, -2, -1.5, -1, 0, 1, 1.5, 2, 20])
tab("ibs1", [0, 0.1, 0.2, 0.8, 0.9, 1.01])
