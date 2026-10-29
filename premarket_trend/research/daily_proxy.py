"""First check on 20 years of daily bars: does the open->close return follow the daily trend,
and does a gap in the trend's direction help? The gap here is the official open vs the prior close,
a stand-in for the pre-market price at 9:25."""
import numpy as np
import pandas as pd

from common.data import load
from common.indicators import atr, sma
from common.universe import DAYTRADE_SYMBOLS

ETFS = {"SPY", "QQQ", "DIA", "IWM", "SMH", "SOXX", "XLK", "XLI", "XLF", "ITA", "URA", "GLD", "SLV", "GDX",
        "MAGS", "DRAM", "IBIT", "XLE", "XLV", "TLT", "XBI"}


def panel():
    rows = []
    for s in DAYTRADE_SYMBOLS:
        d = load(s, "1d").copy()
        d.index = d.index.tz_convert("America/New_York").normalize().tz_localize(None)
        c, o = d.close, d.open
        a = atr(d, 14)
        x = pd.DataFrame(index=d.index)
        x["sym"], x["etf"] = s, s in ETFS
        x["oc"] = c / o - 1
        x["gap_atr"] = (o - c.shift()) / a.shift()
        x["a_pct"] = (a / c).shift()
        s20, s50, s200 = sma(c, 20), sma(c, 50), sma(c, 200)
        up = (c > s20) & (s20 > s50) & (s50 > s50.shift(10))
        dn = (c < s20) & (s20 < s50) & (s50 < s50.shift(10))
        x["trend"] = (up.astype(int) - dn.astype(int)).shift()
        x["r20_atr"] = ((c - c.shift(20)) / a).shift()          # 20-day move in ATRs
        x["hi20"] = (c >= c.rolling(20).max()).shift().astype(float)
        x["lo20"] = (c <= c.rolling(20).min()).shift().astype(float)
        rows.append(x)
    p = pd.concat(rows).dropna()
    p = p[p.gap_atr.abs() < 8]
    p["era"] = pd.cut(p.index.year, [2006, 2011, 2016, 2021, 2026], labels=["07-11", "12-16", "17-21", "22-26"])
    return p


def table(p, by):
    p = p.assign(r=p.oc * p.trend * 1e4)
    g = p.groupby(by + ["era"], observed=True).r
    out = g.mean().unstack().round(1)
    out["n"] = g.size().groupby(level=list(range(len(by)))).sum()
    out["t_all"] = (p.groupby(by, observed=True).r.mean() / p.groupby(by, observed=True).r.sem()).round(1)
    return out


if __name__ == "__main__":
    pd.set_option("display.width", 200)
    p = panel()
    t = p[p.trend != 0].copy()
    t["side"] = np.where(t.trend > 0, "long", "short")
    t["gap_dir"] = pd.cut(t.gap_atr * t.trend, [-9, -0.5, -0.1, 0.1, 0.5, 1, 9],
                          labels=["against>0.5", "against", "flat", "with 0.1-0.5", "with 0.5-1", "with>1"])
    print("Open->close return in the trend's direction, bp (no costs). Trend = close>SMA20>SMA50 rising (or mirror).")
    for etf in (False, True):
        print("\n==", "ETFs" if etf else "Stocks")
        q = t[t.etf == etf]
        print(table(q, ["side"]))
        print(table(q, ["gap_dir"]))
        print(table(q, ["side", "gap_dir"]))
    print("\nStocks at a 20-day high (long) / low (short) with the trend:")
    q = t[~t.etf & (((t.trend > 0) & (t.hi20 == 1)) | ((t.trend < 0) & (t.lo20 == 1)))]
    print(table(q, ["side", "gap_dir"]))
