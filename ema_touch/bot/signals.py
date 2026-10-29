"""MA touch signal detection (STRATEGY.md section 3)."""
import numpy as np
import pandas as pd

from common.indicators import atr as calc_atr
from common.indicators import ma as calc_ma
from ema_touch.bot.params import DEFAULT, Params


def find_touch_signals(df: pd.DataFrame, kind: str, period: int, p: Params = DEFAULT) -> pd.DataFrame:
    """Return one row per signal bar: the 4th (or later) held touch of the MA band.

    A touch episode starts when a bar's low enters the band after a bar that stayed fully above it.
    A close below the band is not a held touch, and price must clear the band again before the next
    touch counts. A close below the break level is a break: with Params.reset_on_break it resets the
    count; otherwise it is only recorded, and Params.min_hold_ratio can require that held touches make
    up at least that share of held touches + breaks within the lookback.
    """
    ma = calc_ma(df["close"], kind, period).to_numpy()
    atr = calc_atr(df, p.atr_period).to_numpy()
    low = df["low"].to_numpy()
    close = df["close"].to_numpy()
    upper = ma + p.band_k * atr
    lower = ma - p.band_k * atr
    break_level = ma - max(p.break_k, p.band_k) * atr

    rows = []
    touches: list[int] = []
    breaks: list[int] = []
    in_band = True  # don't count a touch until price has been fully above the band
    in_break = False  # consecutive closes below the break level count as one break
    for i in range(len(df)):
        if np.isnan(ma[i]) or np.isnan(atr[i]):
            continue
        if close[i] < break_level[i]:
            if p.reset_on_break:
                touches = []
            elif not in_break:
                breaks.append(i)
            in_band, in_break = True, True
            continue
        if close[i] < lower[i]:
            in_band = True
            continue
        if low[i] > upper[i]:
            in_band, in_break = False, False
            continue
        if in_band:
            continue
        in_band = True
        if touches and i - touches[-1] < p.min_touch_gap:
            continue
        touches = [t for t in touches if i - t <= p.touch_lookback]
        breaks = [b for b in breaks if i - b <= p.touch_lookback]
        slope_ok = i >= p.slope_bars and ma[i] > ma[i - p.slope_bars]
        ratio_ok = not breaks or len(touches) / (len(touches) + len(breaks)) >= p.min_hold_ratio
        if len(touches) >= p.touches_required and slope_ok and ratio_ok:
            rows.append((i, len(touches), ma[i], atr[i]))
        touches.append(i)

    out = pd.DataFrame(rows, columns=["i", "prior_touches", "ma", "atr"])
    out["time"] = df.index[out["i"]] if len(out) else pd.DatetimeIndex([], tz="UTC")
    return out
