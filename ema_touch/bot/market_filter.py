"""Index counter-signals and confluence on daily bars (STRATEGY.md section 4)."""
import pandas as pd

from common.indicators import atr as calc_atr
from common.indicators import ma as calc_ma
from common.indicators import rsi as calc_rsi
from common.indicators import ema
from ema_touch.bot.params import DEFAULT, MA_TYPES, Params

# All flags are computed for reporting; only those in Params.counter_signals block entries
COUNTER_COLUMNS = ["overbought", "stretched", "squeeze", "breakdown", "below_200", "big_drop"]


def index_state(daily: pd.DataFrame, p: Params = DEFAULT) -> pd.DataFrame:
    """Per daily bar: each counter-signal flag, `counter` (any of them), and `touch` (confluence)."""
    close, low = daily["close"], daily["low"]
    atr = calc_atr(daily, p.atr_period)
    out = pd.DataFrame(index=daily.index)

    out["overbought"] = calc_rsi(close, p.rsi_period) > p.rsi_overbought

    stretched = pd.Series(False, index=daily.index)
    for n in p.stretch_periods:
        stretched |= (close - ema(close, n)).abs() > p.stretch_atr * atr
    out["stretched"] = stretched

    # Bollinger Bands inside Keltner Channels; with a shared midline this reduces to width comparison
    std = close.rolling(p.squeeze_period).std()
    out["squeeze"] = p.squeeze_bb_std * std < p.squeeze_kc_atr * atr

    crossed = pd.Series(False, index=daily.index)
    for kind in MA_TYPES:
        for n in p.breakdown_periods:
            lower = calc_ma(close, kind, n) - p.band_k * atr
            below = close < lower
            crossed |= below & ~below.shift(fill_value=False)
    out["breakdown"] = crossed.rolling(p.breakdown_lookback, min_periods=1).max().astype(bool)

    out["below_200"] = close < ema(close, 200)

    drop = close.diff() < -p.big_drop_atr * atr.shift()
    out["big_drop"] = drop.rolling(p.big_drop_lookback, min_periods=1).max().astype(bool)

    out["counter"] = out[list(p.counter_signals)].any(axis=1)

    touch = pd.Series(False, index=daily.index)
    for kind in MA_TYPES:
        for n in p.confluence_periods:
            m = calc_ma(close, kind, n)
            touch |= (low <= m + p.band_k * atr) & (close >= m - p.band_k * atr)
    out["touch"] = touch
    return out


def trend_state(daily: pd.DataFrame, p: Params = DEFAULT) -> pd.DataFrame:
    """Per daily bar of one symbol: the trend screen flags (STRATEGY.md section 10)."""
    close = daily["close"]
    e200 = ema(close, 200)
    out = pd.DataFrame(index=daily.index)
    out["above_200"] = close > e200
    out["rising_200"] = out["above_200"] & (e200 > e200.shift(p.trend_slope_days))
    return out


def attach(signals: pd.DataFrame, state: pd.DataFrame, prefix: str) -> pd.DataFrame:
    """Join the latest completed daily index state onto each signal by time (no lookahead)."""
    right = state.add_prefix(prefix + "_").reset_index().rename(columns={"end": "_t"})
    left = signals.sort_values("time")
    return pd.merge_asof(left, right, left_on="time", right_on="_t", direction="backward").drop(columns="_t")
