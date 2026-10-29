"""Turn selected trades into daily portfolio returns, and summary statistics."""
import numpy as np
import pandas as pd


def select(t: pd.DataFrame, *, min_gap=0.3, max_gap=99.0, min_rvol=2.0, trend=True, top=5,
           stocks_only=True, min_price=5.0, side=None, rank="pm_rvol", trend_def="strict") -> pd.DataFrame:
    """The pre-market scan: per day, candidates whose pre-market gap in the trade's direction is
    min_gap..max_gap ATRs, with pre-market relative volume >= min_rvol, trading with the daily trend
    (trend=True), against it (trend=False) or regardless (trend=None). Keeps the top `top` by `rank`.
    trend_def: "strict" = close > SMA20 > SMA50 with SMA50 rising (or the mirror), "sma50" = close above
    (below) SMA50, "r20" = up (down) over the last 20 days."""
    q = t[(t["pm_gap_dir"] >= min_gap) & (t["pm_gap_dir"] < max_gap) & (t["pm_rvol"] >= min_rvol)
          & (t["prev_close"] >= min_price)]
    if stocks_only:
        q = q[~q["etf"]]
    if trend_def == "strict":
        agree = q["with_trend"]
    elif trend_def == "sma50":
        agree = np.where(q["above50"].astype(bool), 1, -1) * q["dir"]
    else:
        agree = np.sign(q["r20_atr"]) * q["dir"]
    if trend is True:
        q = q[agree == 1]
    elif trend is False:
        q = q[agree == -1]
    if side == "long":
        q = q[q["dir"] > 0]
    elif side == "short":
        q = q[q["dir"] < 0]
    q = q.sort_values(["day", rank], ascending=[True, False])
    return q.groupby("day").head(top)


def daily_returns(sel: pd.DataFrame, all_days, *, risk=0.0025, max_position=0.25, max_gross=1.0):
    """Each candidate risks `risk` of equity between entry and stop (position = risk / risk_pct),
    capped at max_position of equity; all candidates of a day together at most max_gross (scaled
    down equally). Candidates that never trigger an entry earn nothing."""
    s = sel.copy()
    s["w"] = np.minimum(risk / s["risk_pct"], max_position)
    gross = s.groupby("day")["w"].transform("sum")
    s["w"] *= np.minimum(1.0, max_gross / gross)
    s["pnl"] = np.where(s["filled"], s["w"] * s["net"], 0.0)
    r = s.groupby("day")["pnl"].sum().reindex(all_days, fill_value=0.0)
    return r, s


def stats(r: pd.Series, s: pd.DataFrame | None = None) -> dict:
    eq = (1 + r).cumprod()
    years = len(r) / 252
    out = {
        "CAGR%": round((eq.iloc[-1] ** (1 / years) - 1) * 100, 1) if years > 0 else np.nan,
        "vol%": round(r.std() * np.sqrt(252) * 100, 1),
        "Sharpe": round(r.mean() / r.std() * np.sqrt(252), 2) if r.std() > 0 else np.nan,
        "maxDD%": round((eq / eq.cummax() - 1).min() * 100, 1),
        "win_months%": round(((1 + r).resample("ME").prod() > 1).mean() * 100) if len(r) else np.nan,
    }
    if s is not None:
        f = s[s["filled"]]
        out.update({
            "trades": len(f),
            "per_day": round(len(f) / max(len(r), 1), 2),
            "net_R": round(f["net_R"].mean(), 3),
            "t": round(f["net_R"].mean() / f["net_R"].sem(), 1) if len(f) > 2 else np.nan,
            "net_bp": round(f["net"].mean() * 1e4, 1),
            "win%": round((f["net"] > 0).mean() * 100),
        })
    return out


def by_period(r: pd.Series, freq="QE") -> pd.Series:
    """Sharpe per period (quarters by default)."""
    return r.groupby(pd.Grouper(freq=freq)).apply(
        lambda x: x.mean() / x.std() * np.sqrt(252) if x.std() > 0 else np.nan).round(2)
