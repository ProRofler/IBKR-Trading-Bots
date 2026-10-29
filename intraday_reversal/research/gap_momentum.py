"""Stocks in play: big gap / heavy opening volume. Trade in the direction of the move, hold to the close."""
import sys
import numpy as np
import pandas as pd
from common.universe import ALL_SYMBOLS
from intraday_reversal.research.bars import grid, stats
from intraday_reversal.research.orb import daily_atr
from intraday_reversal.research.intraday_panel import ETF


def trades(s, tf, entry_slot="10:00", stop="or", stop_atr=0.5, direction="gap", min_gap_atr=1.0, min_relvol=0.0,
           cost_bps=2.0, comm_ps=0.005, require_confirm=False, trail=None):
    g = grid(s, tf)
    O, H, L, C, V = (g[f].values for f in ["open", "high", "low", "close", "volume"])
    slots = list(g["close"].columns)
    k = slots.index(entry_slot)
    days = g["close"].index
    a = daily_atr(s).reindex(days).values
    pc = g["pclose"].values
    v_or = V[:, :k + 1].sum(axis=1)
    rv = v_or / pd.Series(v_or).rolling(14).mean().shift(1).values
    out = []
    for d in range(len(days)):
        if np.isnan(a[d]) or np.isnan(rv[d]) or np.isnan(pc[d]):
            continue
        gap = (O[d, 0] - pc[d]) / a[d]
        if abs(gap) < min_gap_atr or rv[d] < min_relvol:
            continue
        dirn = int(np.sign(gap)) if direction == "gap" else -int(np.sign(gap))
        if require_confirm and np.sign(C[d, k] - O[d, 0]) != dirn:
            continue  # first bars must move further in the gap direction
        entry = O[d, k + 1]
        orh, orl = H[d, :k + 1].max(), L[d, :k + 1].min()
        if stop == "or":
            sp = orl if dirn == 1 else orh
        elif stop == "pc":
            sp = pc[d]
        else:
            sp = entry - dirn * stop_atr * a[d]
        risk = (entry - sp) * dirn
        if risk <= 0:
            continue
        exit_px, how = C[d, -1], "close"
        for i in range(k + 1, len(slots)):
            if (dirn == 1 and L[d, i] <= sp) or (dirn == -1 and H[d, i] >= sp):
                exit_px = min(sp, O[d, i]) if dirn == 1 else max(sp, O[d, i])
                how = "stop"
                break
            if trail:  # move stop to trail x ATR behind the best close
                best = C[d, k + 1:i + 1].max() if dirn == 1 else C[d, k + 1:i + 1].min()
                ns = best - dirn * trail * a[d]
                sp = max(sp, ns) if dirn == 1 else min(sp, ns)
        gross = dirn * (exit_px / entry - 1)
        net = gross - 2 * (cost_bps / 1e4 + comm_ps / entry)
        out.append(dict(day=days[d], sym=s, dir=dirn, gap=gap, rv=rv[d], risk=risk / entry, gross=gross, net=net,
                        r=net * entry / risk, how=how, etf=s in ETF))
    return out


def book(t, risk_per_trade=0.0025, max_lev=4.0, max_pos=None):
    """Daily portfolio return: each trade risks risk_per_trade of equity, gross exposure capped at max_lev."""
    t = t.copy()
    t["w"] = risk_per_trade / t.risk
    if max_pos:
        t = t.sort_values("rv", ascending=False).groupby("day").head(max_pos)
    tot = t.groupby("day").w.transform("sum")
    t["w"] = t.w * np.minimum(1, max_lev / tot)
    return (t.w * t.net).groupby(t.day).sum()


if __name__ == "__main__":
    tf = sys.argv[1] if len(sys.argv) > 1 else "1h"
    all_days = grid("SPY", tf)["close"].index
    rows = []
    cfgs = {
        "gap1 or": dict(),
        "gap1 fade or": dict(direction="fade"),
        "gap1.5 or": dict(min_gap_atr=1.5),
        "gap0.75 or": dict(min_gap_atr=0.75),
        "gap1 rv2 or": dict(min_relvol=2),
        "gap1 confirm or": dict(require_confirm=True),
        "gap1 atr0.5": dict(stop="atr", stop_atr=0.5),
        "gap1 atr1": dict(stop="atr", stop_atr=1.0),
        "gap1 pc": dict(stop="pc"),
        "gap1 or trail1": dict(trail=1.0),
        "gap1 or 10:30": dict(entry_slot="10:30") if tf == "30m" else dict(entry_slot="11:00"),
    }
    for name, kw in cfgs.items():
        t = pd.DataFrame([x for s in ALL_SYMBOLS for x in trades(s, tf, **kw)])
        for lab, sub in [("stk", t[~t.etf]), ("etf", t[t.etf])]:
            if len(sub) == 0:
                continue
            daily = book(sub).reindex(all_days).fillna(0)
            yr = sub.groupby(sub.day.dt.year).r.mean().round(2).to_dict()
            rows.append(dict(cfg=name, set=lab, n=len(sub), avgR=round(sub.r.mean(), 3), net_bp=round(sub.net.mean() * 1e4, 1),
                             win=round((sub.r > 0).mean(), 2), stops=round((sub.how == "stop").mean(), 2),
                             tstat=round(sub.r.mean() / sub.r.std() * np.sqrt(len(sub)), 2))
                        | {k: v for k, v in stats(daily).items() if k in ("cagr", "sharpe", "maxdd", "win_months")} | {"byyear": yr})
    print(pd.DataFrame(rows).to_string(index=False))
