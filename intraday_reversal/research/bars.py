"""Shared helpers for the research scripts: intraday bars as day x slot grids, and return stats."""
from pathlib import Path

import numpy as np
import pandas as pd

from common.data import load

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
RESULTS_DIR.mkdir(exist_ok=True)

NY = "America/New_York"
_cache = {}


def grid(symbol, tf="30m"):
    """Dict of day x slot DataFrames (open/high/low/close/volume), slot = bar end time ET."""
    key = (symbol, tf)
    if key in _cache:
        return _cache[key]
    df = load(symbol, tf)
    t = df.index.tz_convert(NY)
    slot = pd.Index(t.strftime("%H:%M"))
    if tf == "1h":
        slot = slot.where(slot != "10:30", "10:00")  # first IBKR hourly bar is 9:30-10:00
    df = df.assign(day=t.normalize().tz_localize(None), slot=slot)
    std = (["10:00"] + [f"{h}:00" for h in range(11, 17)]) if tf == "1h" else \
        [f"{h}:{m:02d}" for h in range(10, 17) for m in (0, 30)][:-1]
    df = df[df.slot.isin(std)]  # halts leave odd bar times; drop them
    g = {f: df.pivot(index="day", columns="slot", values=f).reindex(columns=std) for f in ["open", "high", "low", "close", "volume"]}
    full = g["close"].notna().all(axis=1)  # keep full sessions only
    g = {f: v[full] for f, v in g.items()}
    g["dopen"] = g["open"].iloc[:, 0]
    g["dclose"] = g["close"].iloc[:, -1]
    g["pclose"] = g["dclose"].shift()
    # previous day's close may come from a half-day we dropped; use the daily file instead
    d = load(symbol, "1d")
    dd = pd.Series(d["close"].values, index=d.index.tz_convert(NY).normalize().tz_localize(None))
    g["pclose"] = dd.shift().reindex(g["close"].index)
    tp = (g["high"] + g["low"] + g["close"]) / 3
    g["vwap"] = (tp * g["volume"]).cumsum(axis=1) / g["volume"].cumsum(axis=1)
    _cache[key] = g
    return g


def stats(daily: pd.Series, name="", periods=252):
    daily = daily.fillna(0)
    eq = (1 + daily).cumprod()
    yrs = len(daily) / periods
    cagr = eq.iloc[-1] ** (1 / yrs) - 1
    vol = daily.std() * np.sqrt(periods)
    sharpe = daily.mean() / daily.std() * np.sqrt(periods) if daily.std() > 0 else np.nan
    dd = (eq / eq.cummax() - 1).min()
    active = daily[daily != 0]
    monthly = (1 + daily).groupby(daily.index.to_period("M")).prod() - 1
    return dict(name=name, cagr=round(cagr * 100, 1), vol=round(vol * 100, 1), sharpe=round(sharpe, 2),
                maxdd=round(dd * 100, 1), days_active=round(len(active) / len(daily) * 100),
                win_days=round((active > 0).mean() * 100), win_months=round((monthly > 0).mean() * 100),
                calmar=round(cagr / -dd, 2) if dd < 0 else np.nan)


def show(rows):
    print(pd.DataFrame(rows).to_string(index=False))
