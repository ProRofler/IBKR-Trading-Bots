"""Strategy 1: intraday momentum out of the 'noise area' (Zarattini, Aziz, Barbon 2024)."""
import sys
import numpy as np
import pandas as pd
from intraday_reversal.research.bars import grid, stats, show


def noise_momentum(symbol, tf="30m", lookback=14, vm=1.0, cost_bps=1.0, stop="vwap", target_vol=0.02,
                   max_lev=4.0, long_only=False, first_slot=0, every=1, raw=False):
    g = grid(symbol, tf)
    C, O, PC, V = g["close"].values, g["open"].values, g["pclose"].values, g["vwap"].values
    dopen = g["dopen"].values
    move = np.abs(C / dopen[:, None] - 1)
    sigma = pd.DataFrame(move).rolling(lookback).mean().shift(1).values * vm
    ub = np.maximum(dopen, PC)[:, None] * (1 + sigma)
    lb = np.minimum(dopen, PC)[:, None] * (1 - sigma)
    dret = pd.Series(g["dclose"]).pct_change()
    dvol = dret.rolling(14).std().shift(1).values
    lev = np.minimum(max_lev, target_vol / dvol) if target_vol else np.ones(len(C))
    n_days, n_slots = C.shape
    out = np.zeros(n_days)
    trades = 0
    for d in range(n_days):
        if np.isnan(sigma[d]).any() or np.isnan(lev[d]) or np.isnan(PC[d]):
            continue
        pos, entry, r = 0, 0.0, 0.0
        for s in range(first_slot, n_slots - 1):
            c = C[d, s]
            want = pos
            if pos == 1 and c < (max(ub[d, s], V[d, s]) if stop == "vwap" else ub[d, s]):
                want = 0
            if pos == -1 and c > (min(lb[d, s], V[d, s]) if stop == "vwap" else lb[d, s]):
                want = 0
            if (s - first_slot) % every == 0:
                if c > ub[d, s]:
                    want = 1
                elif c < lb[d, s] and not long_only:
                    want = -1
            if want != pos:
                px = O[d, s + 1]
                if pos != 0:
                    r += pos * (px / entry - 1) - cost_bps / 1e4
                    trades += 1
                if want != 0:
                    entry = px
                    r -= cost_bps / 1e4
                pos = want
        if pos != 0:
            r += pos * (C[d, -1] / entry - 1) - cost_bps / 1e4
            trades += 1
        out[d] = r * (1 if raw else lev[d])
    res = pd.Series(out, index=g["close"].index)
    res.attrs["trades"] = trades
    return res


if __name__ == "__main__":
    tf = sys.argv[1] if len(sys.argv) > 1 else "30m"
    rows = []
    for sym in ["SPY", "QQQ", "DIA", "XLK", "XLF", "XLI", "SMH", "GLD", "SLV", "GDX"]:
        for kw in [dict(), dict(cost_bps=0), dict(stop="band"), dict(long_only=True)]:
            r = noise_momentum(sym, tf, **kw)
            rows.append(stats(r, f"{sym} {kw}") | dict(trades=r.attrs["trades"]))
    show(rows)
