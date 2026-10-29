"""Signals from daily bars, known before the open."""
import pandas as pd

from common.data import load
from common.indicators import atr
from intraday_reversal.params import DEFAULT, Params


def daily_bars(symbol: str) -> pd.DataFrame:
    """Daily bars indexed by trading date (America/New_York)."""
    d = load(symbol, "1d").copy()
    d.index = d.index.tz_convert("America/New_York").normalize().tz_localize(None)
    d.index.name = "day"
    return d


def add_signal(d: pd.DataFrame, p: Params = DEFAULT) -> pd.DataFrame:
    """Columns for each day: move = yesterday's (close - open) / yesterday's ATR, and the trade
    direction for today (+1 long, -1 short, 0 none), before the long/short symbol lists apply."""
    d = d.copy()
    a = atr(d, p.atr_period)
    d["atr"] = a.shift()                                   # as of yesterday's close
    d["move"] = ((d["close"] - d["open"]) / a).shift()     # yesterday's intraday move in ATRs
    d["direction"] = 0
    d.loc[d["move"] < -p.threshold_atr, "direction"] = 1    # big down day -> buy today's open
    d.loc[d["move"] > p.threshold_atr, "direction"] = -1    # big up day -> short today's open
    return d

