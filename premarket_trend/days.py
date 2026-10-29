"""Per symbol and day: what the pre-market scanner knows before 9:30, and the session's 5-minute path.

days(symbol) -> DataFrame indexed by NY trading date with
    prev_close, atr (ATR(14) as of yesterday, $), trend (+1 up / -1 down / 0, as of yesterday),
    r20_atr (20-day move in ATRs), dollar_vol (20-day average, $),
    pm_last (last pre-market price, 9:00-9:30 bar close), pm_gap_atr ((pm_last - prev_close) / atr),
    pm_vol (shares traded 4:00-9:30), pm_rvol (pm_vol / its 20-day average),
    pm_turnover (pre-market $ volume / 20-day average daily $ volume),
    open (official open), gap_atr ((open - prev_close) / atr).
grid(symbol) -> dict of day x slot arrays (o, h, l, c, v) for the 78 regular-hours 5-minute bars.
"""
from functools import lru_cache

import numpy as np
import pandas as pd

from common.data import load
from common.indicators import atr, sma
from common.intraday import load_intraday

NY = "America/New_York"
SLOTS = pd.date_range("09:35", "16:00", freq="5min").strftime("%H:%M")   # bar end times


def _by_day(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    local = df.index.tz_convert(NY)
    df["day"] = local.normalize().tz_localize(None)
    df["slot"] = local.strftime("%H:%M")
    return df


@lru_cache(maxsize=None)
def daily(symbol: str) -> pd.DataFrame:
    """Daily features known before today's open (all shifted by one day)."""
    d = load(symbol, "1d").copy()
    d.index = d.index.tz_convert(NY).normalize().tz_localize(None)
    c = d["close"]
    a = atr(d, 14)
    s20, s50 = sma(c, 20), sma(c, 50)
    up = (c > s20) & (s20 > s50) & (s50 > s50.shift(10))
    dn = (c < s20) & (s20 < s50) & (s50 < s50.shift(10))
    x = pd.DataFrame(index=d.index)
    x["prev_close"] = c.shift()
    x["atr"] = a.shift()
    x["trend"] = (up.astype(int) - dn.astype(int)).shift()
    x["r20_atr"] = ((c - c.shift(20)) / a).shift()
    x["above50"] = (c > s50).shift()
    x["dollar_vol"] = (c * d["volume"]).rolling(20).mean().shift()
    x["d_open"], x["d_close"] = d["open"], d["close"]
    return x


@lru_cache(maxsize=None)
def premarket(symbol: str) -> pd.DataFrame:
    """Pre-market volume and last price per day from 30-minute extended-hours bars."""
    b = load_intraday(symbol, "30m_ext")
    if b.empty:
        return pd.DataFrame(columns=["pm_last", "pm_vol"])
    b = _by_day(b)
    pm = b[(b["slot"] > "04:00") & (b["slot"] <= "09:30")]
    out = pm.groupby("day").agg(pm_vol=("volume", "sum"))
    last = pm[pm["slot"] == "09:30"].set_index("day")["close"]
    out["pm_last"] = last
    return out


@lru_cache(maxsize=None)
def grid(symbol: str) -> dict:
    """Day x slot arrays of the regular-hours 5-minute bars (NaN where a bar is missing)."""
    b = _by_day(load_intraday(symbol, "5m"))
    b = b[b["slot"].isin(SLOTS)]
    out = {}
    for col, key in [("open", "o"), ("high", "h"), ("low", "l"), ("close", "c"), ("volume", "v")]:
        out[key] = b.pivot_table(index="day", columns="slot", values=col).reindex(columns=SLOTS)
    out["days"] = out["o"].index
    out = {k: (v.to_numpy() if isinstance(v, pd.DataFrame) else v) for k, v in out.items()}
    return out


@lru_cache(maxsize=None)
def days(symbol: str) -> pd.DataFrame:
    g = grid(symbol)
    if len(g["days"]) == 0:
        return pd.DataFrame()
    x = daily(symbol).reindex(g["days"])
    pm = premarket(symbol).reindex(g["days"])
    x["pm_vol"] = pm["pm_vol"]
    x["pm_last"] = pm["pm_last"]
    # Average over the previous 20 days that had pre-market data
    x["pm_rvol"] = x["pm_vol"] / x["pm_vol"].rolling(20, min_periods=10).mean().shift()
    x["pm_gap_atr"] = (x["pm_last"] - x["prev_close"]) / x["atr"]
    # Pre-market dollar volume as a fraction of a normal day's dollar volume
    x["pm_turnover"] = x["pm_vol"] * x["pm_last"] / x["dollar_vol"]
    x["open"] = g["o"][:, 0]
    x["gap_atr"] = (x["open"] - x["prev_close"]) / x["atr"]
    # First 5-minute bar volume relative to the previous 14 days (Zarattini et al. "stocks in play")
    v0 = pd.Series(g["v"][:, 0], index=g["days"])
    x["rvol5"] = v0 / v0.rolling(14, min_periods=10).mean().shift()
    x["first_bar"] = np.sign(g["c"][:, 0] - g["o"][:, 0])
    x["row"] = np.arange(len(x))      # position in grid(symbol)
    return x
