"""Time-series intraday momentum/reversal by decision time: sign(move so far) -> move to close."""
import sys
import numpy as np
import pandas as pd
from common.universe import ALL_SYMBOLS
from intraday_reversal.research.bars import grid
from intraday_reversal.research.intraday_panel import ETF

tf = sys.argv[1] if len(sys.argv) > 1 else "30m"
groups = {"ETF": [s for s in ALL_SYMBOLS if s in ETF], "STK": [s for s in ALL_SYMBOLS if s not in ETF]}
for gname, syms in groups.items():
    res = {}
    for s in syms:
        g = grid(s, tf)
        slots = list(g["close"].columns)
        for i, k in enumerate(slots[:-1]):
            nxt = slots[i + 1]
            fwd = g["dclose"] / g["open"][nxt] - 1
            for base, ref in [("open", g["dopen"]), ("pc", g["pclose"])]:
                sig = np.sign(g["close"][k] / ref - 1)
                res.setdefault((k, base), []).append((sig * fwd).rename(s))
            # last bar only (Gao): sign(pc->k) -> last bar return
            last = g["close"].iloc[:, -1] / g["open"].iloc[:, -1] - 1
            sig = np.sign(g["close"][k] / g["pclose"] - 1)
            res.setdefault((k, "pc->lastbar"), []).append((sig * last).rename(s))
    rows = []
    for (k, base), lst in res.items():
        daily = pd.concat(lst, axis=1).mean(axis=1).dropna()
        rows.append(dict(slot=k, base=base, bp=daily.mean() * 1e4, t=daily.mean() / daily.std() * np.sqrt(len(daily))))
    t = pd.DataFrame(rows).pivot(index="slot", columns="base", values=["bp", "t"]).round(2)
    print(gname, tf)
    print(t)
