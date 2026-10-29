"""Open-to-close research on 20 years of daily bars: signals known before the open, return from open to close."""
import numpy as np
import pandas as pd
from common.data import load
from common.indicators import atr, rsi
from common.universe import ALL_SYMBOLS
from intraday_reversal.research.intraday_panel import ETF
from intraday_reversal.research.bars import RESULTS_DIR


def daily_panel():
    rows = []
    for s in ALL_SYMBOLS:
        d = load(s, "1d").copy()
        d.index = d.index.tz_convert("America/New_York").normalize().tz_localize(None)
        o, h, l, c = d.open, d.high, d.low, d.close
        x = pd.DataFrame(index=d.index)
        x["sym"] = s
        x["etf"] = s in ETF
        x["oc"] = c / o - 1                                # target: today's open -> close
        x["gap"] = o / c.shift() - 1                        # known at the open
        x["a"] = atr(d, 14).shift() / c.shift()             # ATR as % of price, known
        x["gap_atr"] = x.gap / x.a
        x["oc1"] = (c / o - 1).shift()                      # yesterday's intraday return
        x["on1"] = x.gap.shift()                            # yesterday's overnight return
        x["r5"] = (c / c.shift(5) - 1).shift()
        x["r20"] = (c / c.shift(20) - 1).shift()
        x["r250"] = (c.shift(21) / c.shift(252) - 1).shift()
        x["ibs1"] = ((c - l) / (h - l)).shift()
        x["rsi2"] = rsi(c, 2).shift()
        x["ma200"] = (c / c.rolling(200).mean() - 1).shift()
        x["dv"] = (c * d.volume).rolling(20).mean().shift()
        x["px"] = o
        x["oc_hi"] = h / o - 1
        x["oc_lo"] = l / o - 1
        rows.append(x)
    p = pd.concat(rows).reset_index().rename(columns={"end": "day", "index": "day"})
    p = p[p.gap.abs() < 0.5]  # bad prints / splits not adjusted
    return p


if __name__ == "__main__":
    p = daily_panel()
    p.to_parquet(RESULTS_DIR / "daily_panel.parquet")
    print(len(p), p.day.min(), p.day.max(), p.sym.nunique())
