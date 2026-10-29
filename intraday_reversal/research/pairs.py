"""Intraday pairs mean reversion: when two highly correlated names diverge during the day, bet on convergence by the close."""
import itertools
import sys
import numpy as np
import pandas as pd
from common.universe import ALL_SYMBOLS
from intraday_reversal.research.bars import grid, stats

tf = sys.argv[1] if len(sys.argv) > 1 else "30m"
SKIP = {"SOXX", "MAGS", "DRAM"}  # near-duplicates of SMH / short history
syms = [s for s in ALL_SYMBOLS if s not in SKIP]
G = {s: grid(s, tf) for s in syms}
days = sorted(set.intersection(*[set(G[s]["close"].index) for s in ["SPY", "QQQ"]]))
days = pd.DatetimeIndex(days)
slots = list(G["SPY"]["close"].columns)

# log return from prev close to each slot close, and next-bar open (fill) and day close
def arrs(s):
    g = G[s]
    pc = g["pclose"].reindex(days).values[:, None]
    c = np.log(g["close"].reindex(days).values / pc)
    o = np.log(g["open"].reindex(days).values / pc)
    dc = np.log(g["dclose"].reindex(days).values / g["pclose"].reindex(days).values)
    v = g["volume"].reindex(days).values
    return c, o, dc, v

A = {s: arrs(s) for s in syms}
daily = pd.DataFrame({s: A[s][2] for s in syms}, index=days)


def run(corr_min=0.8, z_in=2.0, z_out=0.0, lookback=60, ref="pc", max_pairs=None, cost_bps=2.0,
        first="10:00", last_entry="15:00", relvol_max=None, beta_hedge=True):
    corr = daily.rolling(lookback, min_periods=lookback).corr()
    vol = daily.rolling(20).std()
    i_first, i_last = slots.index(first), slots.index(last_entry)
    pnl = np.zeros(len(days))
    ntr = 0
    trades = []
    for d in range(lookback + 1, len(days)):
        C = corr.loc[days[d - 1]]  # known before the day starts
        pairs = []
        for a, b in itertools.combinations(syms, 2):
            r = C.at[a, b]
            if r >= corr_min:
                pairs.append((r, a, b))
        pairs.sort(reverse=True)
        if max_pairs:
            pairs = pairs[:max_pairs]
        day_pnl, n_open = 0.0, 0
        for r, a, b in pairs:
            ca, oa, dca, _ = A[a]
            cb, ob, dcb, _ = A[b]
            va, vb = vol.iat[d - 1, syms.index(a)], vol.iat[d - 1, syms.index(b)]
            if not (va > 0 and vb > 0) or np.isnan(ca[d]).any() or np.isnan(cb[d]).any():
                continue
            # weights: vol-matched so each leg has the same risk; spread in units of 'a' vol
            hb = r * va / vb if beta_hedge else va / vb
            base_a = 0.0 if ref == "pc" else oa[d, 0]
            base_b = 0.0 if ref == "pc" else ob[d, 0]
            spread = (ca[d] - base_a) - hb * (cb[d] - base_b)
            sd = va * np.sqrt(max(1e-9, 1 - r * r))  # daily std of the hedged spread
            z = spread / sd
            pos, entry = 0, None
            for i in range(i_first, len(slots) - 1):
                if pos == 0 and i <= i_last and abs(z[i]) > z_in:
                    pos = -int(np.sign(z[i]))  # long spread if it's below
                    entry = (oa[d, i + 1], ob[d, i + 1])
                elif pos != 0 and (pos * z[i] >= -z_out):
                    xa, xb = oa[d, i + 1], ob[d, i + 1]
                    g = pos * ((xa - entry[0]) - hb * (xb - entry[1])) / (1 + hb)
                    day_pnl += g - 2 * cost_bps / 1e4
                    trades.append(g - 2 * cost_bps / 1e4)
                    n_open += 1
                    pos = 0
            if pos != 0:
                xa, xb = dca[d], dcb[d]
                g = pos * ((xa - entry[0]) - hb * (xb - entry[1])) / (1 + hb)
                day_pnl += g - 2 * cost_bps / 1e4
                trades.append(g - 2 * cost_bps / 1e4)
                n_open += 1
        pnl[d] = day_pnl / max(1, len(pairs)) if pairs else 0  # equal capital per eligible pair
        ntr += n_open
    res = pd.Series(pnl, index=days)
    t = np.array(trades)
    return res, dict(trades=ntr, avg_bp=t.mean() * 1e4 if len(t) else 0, win=(t > 0).mean() if len(t) else 0)


if __name__ == "__main__":
    rows = []
    for kw in [dict(), dict(z_in=1.5), dict(z_in=2.5), dict(corr_min=0.7), dict(corr_min=0.85), dict(ref="open"),
               dict(cost_bps=0), dict(z_out=-0.5), dict(beta_hedge=False)]:
        r, info = run(**kw)
        rows.append(stats(r, str(kw)) | info)
        print(rows[-1], flush=True)
