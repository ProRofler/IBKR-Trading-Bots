"""Intraday mean reversion (IMR) portfolio backtest on daily bars: enter at the open, exit at the close."""
import numpy as np
import pandas as pd
from intraday_reversal.research.bars import stats, RESULTS_DIR

pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
P = pd.read_parquet(RESULTS_DIR / "daily_panel.parquet")
P["grp"] = np.where(P.sym.isin(["SPY", "QQQ", "DIA"]), "index", np.where(P.etf, "etf", "stock"))
P["oc1_atr"] = P.oc1 / P.a
P = P.dropna(subset=["oc1_atr", "ibs1", "oc", "a"])
SPY_OC = P[P.sym == "SPY"].set_index("day").oc


def backtest(groups=("index", "etf", "stock"), sig="ibs", lo=0.15, hi=0.85, k=0.75, long=True, short=True,
             short_groups=None, gross=1.0, max_w=0.2, cost_bps=1.0, comm_ps=0.005, stop_atr=None, hedge=False,
             start=None, end=None, syms=None, min_px=5, rank=False, max_n=None, vol_target=None):
    d = P[P.grp.isin(groups) & (P.px >= min_px)]
    if syms is not None:
        d = d[d.sym.isin(syms)]
    if start:
        d = d[d.day >= start]
    if end:
        d = d[d.day < end]
    if sig == "ibs":
        lsig, ssig = d.ibs1 < lo, d.ibs1 > hi
        score = 0.5 - d.ibs1
    elif sig == "oc1":
        lsig, ssig = d.oc1_atr < -k, d.oc1_atr > k
        score = -d.oc1_atr
    else:  # both must agree
        lsig = (d.ibs1 < lo) & (d.oc1_atr < -k)
        ssig = (d.ibs1 > hi) & (d.oc1_atr > k)
        score = (0.5 - d.ibs1) - d.oc1_atr
    sg = short_groups if short_groups is not None else groups
    d = d.assign(dir=np.where(lsig & long, 1, np.where(ssig & short & d.grp.isin(sg), -1, 0)), score=score.abs())
    d = d[d.dir != 0].copy()
    if max_n:
        d = d.sort_values("score", ascending=False).groupby("day").head(max_n)
    # inverse-volatility weights so each position carries similar risk, scaled to the gross budget
    d["raw"] = 1 / d.a
    n = d.groupby("day").raw.transform("sum")
    d["w"] = np.minimum(max_w, gross * d.raw / n)
    if vol_target:  # cap each position's daily risk instead of filling the gross budget
        d["w"] = np.minimum(d.w, vol_target / d.a)
    r = d.dir * d.oc
    if stop_atr:
        stop = stop_atr * d.a
        hit = np.where(d.dir == 1, d.oc_lo <= -stop, d.oc_hi >= stop)
        r = np.where(hit, -stop - cost_bps / 1e4, r)  # extra slippage on the stop
    cost = 2 * (cost_bps / 1e4 + comm_ps / d.px)
    d["pnl"] = d.w * (r - cost)
    if hedge:  # offset the net dollar exposure with SPY open->close
        net = (d.w * d.dir).groupby(d.day).sum()
        h = -net * SPY_OC.reindex(net.index) - net.abs() * 2 * cost_bps / 1e4
    daily = d.groupby("day").pnl.sum()
    if hedge:
        daily = daily.add(h, fill_value=0)
    days = P[(P.sym == "SPY")].day
    if start:
        days = days[days >= start]
    if end:
        days = days[days < end]
    daily = daily.reindex(days.values).fillna(0)
    daily.attrs["n"] = len(d)
    daily.attrs["avg_bp"] = (r - cost).mean() * 1e4
    daily.attrs["exposure"] = d.groupby("day").w.sum().reindex(days.values).fillna(0).mean()
    return daily


def eras(daily):
    out = {}
    for a, b in [("2007", "2012"), ("2012", "2017"), ("2017", "2022"), ("2022", "2027")]:
        x = daily[(daily.index >= a) & (daily.index < b)]
        out[a[2:] + "-" + str(int(b) - 1)[2:]] = round(x.mean() / x.std() * np.sqrt(252), 2) if x.std() > 0 else np.nan
    return out


def report(name, daily):
    s = stats(daily, name)
    return {k: s[k] for k in ["name", "cagr", "vol", "sharpe", "maxdd", "win_months", "calmar"]} | \
        dict(n=daily.attrs["n"], bp=round(daily.attrs["avg_bp"], 1), expo=round(daily.attrs["exposure"], 2)) | eras(daily)


if __name__ == "__main__":
    rows = []
    for g in [("index",), ("etf",), ("stock",), ("index", "etf"), ("index", "etf", "stock")]:
        for sig in ["ibs", "oc1", "both"]:
            for side in [dict(), dict(short=False), dict(long=False)]:
                rows.append(report(f"{'+'.join(g)} {sig} {side}", backtest(g, sig, **side)))
    print(pd.DataFrame(rows).to_string(index=False))
