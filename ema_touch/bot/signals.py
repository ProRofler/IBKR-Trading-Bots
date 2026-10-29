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

    With Params.entry_mode "touch", rows are instead every bar whose low reaches the entry level (top of
    the band from the previous bar's MA and ATR, known before the bar opens) while the touch count, slope
    and gap conditions already hold, whether or not the touch then holds. "held" says if it did (close
    inside or above the band); "time" is the previous bar's end, when the resting order is placed.
    """
    touch_mode = p.entry_mode == "touch"
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
        if touch_mode and not in_band and i > p.slope_bars and not np.isnan(atr[i - 1]):
            level = ma[i - 1] + p.band_k * atr[i - 1]
            recent = [t for t in touches if i - t <= p.touch_lookback]
            recent_breaks = [b for b in breaks if i - b <= p.touch_lookback]
            if (low[i] <= level and len(recent) >= p.touches_required
                    and (not touches or i - touches[-1] >= p.min_touch_gap)
                    and ma[i - 1] > ma[i - 1 - p.slope_bars]
                    and (not recent_breaks or len(recent) / (len(recent) + len(recent_breaks)) >= p.min_hold_ratio)):
                rows.append((i, len(recent), ma[i - 1], atr[i - 1], level, close[i] >= lower[i]))
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
        if not touch_mode and len(touches) >= p.touches_required and slope_ok and ratio_ok:
            rows.append((i, len(touches), ma[i], atr[i]))
        touches.append(i)

    columns = ["i", "prior_touches", "ma", "atr"] + (["level", "held"] if touch_mode else [])
    out = pd.DataFrame(rows, columns=columns)
    decided = out["i"] - 1 if touch_mode else out["i"]
    out["time"] = df.index[decided] if len(out) else pd.DatetimeIndex([], tz="UTC")
    return out
