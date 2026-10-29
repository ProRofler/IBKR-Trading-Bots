"""Opening range breakout trade simulation on 30m/1h bars. One trade per stock-day max."""
import sys
import numpy as np
import pandas as pd
from common.data import load
from common.indicators import atr
from common.universe import ALL_SYMBOLS
from intraday_reversal.research.intraday_panel import ETF
from intraday_reversal.research.bars import grid, RESULTS_DIR


def daily_atr(s):
    d = load(s, "1d")
    a = atr(d, 14).shift(1)
    a.index = a.index.tz_convert("America/New_York").normalize().tz_localize(None)
    return a


def orb_trades(s, tf="30m", n_or=1, mode="break", stop="or", stop_atr=0.1, target_r=None, last_entry="12:00",
               cost_bps=2.0, comm_ps=0.005):
    g = grid(s, tf)
    O, H, L, C, V = (g[f].values for f in ["open", "high", "low", "close", "volume"])
    slots = list(g["close"].columns)
    days = g["close"].index
    a = daily_atr(s).reindex(days).values
    v_or = V[:, :n_or].sum(axis=1)
    relvol = pd.Series(v_or).rolling(14).mean().shift(1).values
    relvol = v_or / relvol
    orh, orl = H[:, :n_or].max(axis=1), L[:, :n_or].min(axis=1)
    last_i = slots.index(last_entry)
    out = []
    for d in range(len(days)):
        if np.isnan(a[d]) or np.isnan(relvol[d]):
            continue
        dirn, entry, ei = 0, np.nan, None
        if mode == "candle":  # direction of the opening range candle, enter at its close
            o0, c0 = O[d, 0], C[d, n_or - 1]
            if c0 == o0:
                continue
            dirn = 1 if c0 > o0 else -1
            ei = n_or
            entry = O[d, ei]
            same_bar_check = False
        else:
            for i in range(n_or, last_i + 1):
                up, dn = H[d, i] > orh[d], L[d, i] < orl[d]
                if up and dn:
                    break  # ambiguous bar: skip the day
                if up:
                    dirn, entry, ei = 1, max(orh[d], O[d, i]), i
                    break
                if dn:
                    dirn, entry, ei = -1, min(orl[d], O[d, i]), i
                    break
            same_bar_check = True
        if dirn == 0:
            continue
        if stop == "or":
            sp = orl[d] if dirn == 1 else orh[d]
        elif stop == "mid":
            sp = (orl[d] + orh[d]) / 2
        else:
            sp = entry - dirn * stop_atr * a[d]
        risk = (entry - sp) * dirn
        if risk <= 0:
            continue
        tp = entry + dirn * target_r * risk if target_r else None
        exit_px, how = C[d, -1], "close"
        for i in range(ei, len(slots)):
            lo, hi = L[d, i], H[d, i]
            if i == ei and not same_bar_check:
                pass
            # stop first (conservative)
            if (dirn == 1 and lo <= sp) or (dirn == -1 and hi >= sp):
                exit_px = sp if i == ei else (min(sp, O[d, i]) if dirn == 1 else max(sp, O[d, i]))
                how = "stop"
                break
            if tp is not None and i > ei and ((dirn == 1 and hi >= tp) or (dirn == -1 and lo <= tp)):
                exit_px = max(tp, O[d, i]) if dirn == 1 else min(tp, O[d, i])
                how = "target"
                break
        gross = dirn * (exit_px / entry - 1)
        cost = 2 * (cost_bps / 1e4 + comm_ps / entry)
        out.append(dict(day=days[d], sym=s, dir=dirn, entry=entry, risk_pct=risk / entry, gross=gross,
                        net=gross - cost, r=(gross - cost) * entry / risk, how=how, relvol=relvol[d],
                        or_atr=(orh[d] - orl[d]) / a[d], slot=slots[ei]))
    return out


if __name__ == "__main__":
    tf = sys.argv[1] if len(sys.argv) > 1 else "30m"
    configs = {
        "break_or": dict(),
        "break_mid": dict(stop="mid"),
        "break_or_2R": dict(target_r=2),
        "break_atr0.1": dict(stop="atr", stop_atr=0.1),
        "break_atr0.25": dict(stop="atr", stop_atr=0.25),
        "candle_or": dict(mode="candle"),
        "candle_atr0.1": dict(mode="candle", stop="atr", stop_atr=0.1),
        "candle_atr0.25": dict(mode="candle", stop="atr", stop_atr=0.25),
        "break_or_n2": dict(n_or=2, last_entry="13:00") if tf == "30m" else dict(n_or=2, last_entry="13:00"),
    }
    rows = []
    for name, kw in configs.items():
        t = pd.DataFrame([x for s in ALL_SYMBOLS for x in orb_trades(s, tf, **kw)])
        t["etf"] = t.sym.isin(ETF)
        t.to_parquet(RESULTS_DIR / f"orb_{tf}_{name}.parquet")
        for lab, sub in [("all", t), ("etf", t[t.etf]), ("stk", t[~t.etf]), ("stk rv>1.5", t[~t.etf & (t.relvol > 1.5)]),
                         ("stk rv>2.5", t[~t.etf & (t.relvol > 2.5)])]:
            rows.append(dict(cfg=name, set=lab, n=len(sub), avgR=sub.r.mean(), net_bp=sub.net.mean() * 1e4,
                             gross_bp=sub.gross.mean() * 1e4, win=(sub.r > 0).mean(), risk_bp=sub.risk_pct.median() * 1e4,
                             t=sub.r.mean() / sub.r.std() * np.sqrt(len(sub))))
    print(pd.DataFrame(rows).round(3).to_string(index=False))
