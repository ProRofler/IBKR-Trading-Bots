"""Simulate intraday trades on 5-minute bars: enter in a given direction, exit at a stop or the close.

Fills (conservative where the bars can't tell):
- entry "open": at the first bar's open (9:30).
- entry "orb": a stop order at the opening-range extreme, live from the end of the range until
  `last_entry`. Filled at the level, or at the bar's open if the bar opens beyond it.
- entry "orb_close": at the close of the first bar that closes beyond the range.
- The stop is checked from the entry bar on. If a bar opens through the stop, the fill is that open.
  When the entry and the stop fall inside the same bar, the trade counts as stopped (the order
  inside the bar is unknown). For "open" entries this is exact: the open comes first.
- Otherwise the exit is the session's last close (market-on-close order).
"""
import numpy as np
import pandas as pd

from premarket_trend.days import SLOTS

SLOT_INDEX = {s: i for i, s in enumerate(SLOTS)}


def simulate(g: dict, rows: np.ndarray, direction: np.ndarray, atr: np.ndarray, *, entry="orb",
             or_bars=1, stop="or", stop_atr=0.1, last_entry="15:00", trail_atr=None) -> pd.DataFrame:
    """g: grid(symbol); rows: day positions in the grid; direction: +1 long / -1 short per row;
    atr: daily ATR ($) per row. Returns one row per signal; `filled` is False when no entry came."""
    d = direction.astype(float)[:, None]
    long = d > 0
    # Mirror shorts so every trade is a long in price space p' = d * p
    O = g["o"][rows] * d
    H = np.where(long, g["h"][rows], -g["l"][rows])
    L = np.where(long, g["l"][rows], -g["h"][rows])
    C = g["c"][rows] * d
    n, m = O.shape
    i = np.arange(n)
    Hn = np.where(np.isnan(H), -np.inf, H)
    Ln = np.where(np.isnan(L), np.inf, L)
    last = SLOT_INDEX[last_entry] if last_entry else m - 1
    k = or_bars
    or_hi = np.nanmax(H[:, :k], axis=1)
    or_lo = np.nanmin(L[:, :k], axis=1)

    if entry == "open":
        j0 = np.zeros(n, dtype=int)
        px = O[:, 0]
        filled = ~np.isnan(px)
    elif entry in ("orb", "orb_close"):
        if entry == "orb":
            hit = Hn[:, k:last + 1] >= or_hi[:, None]
        else:
            hit = np.nan_to_num(C[:, k:last + 1], nan=-np.inf) > or_hi[:, None]
        filled = hit.any(axis=1)
        j0 = k + hit.argmax(axis=1)
        px = np.maximum(or_hi, O[i, j0]) if entry == "orb" else C[i, j0]
        if entry == "orb_close":
            j0 = j0 + 1          # the stop is live from the next bar
    else:
        raise ValueError(entry)

    if stop == "or":
        level = or_lo if entry != "open" else np.full(n, -np.inf)
    elif stop == "atr":
        level = px - stop_atr * atr
    elif stop == "none":
        level = np.full(n, -np.inf)
    else:
        raise ValueError(stop)
    level = np.minimum(level, px)

    cols = np.arange(m)[None, :]
    after = cols >= j0[:, None]
    if trail_atr is not None:
        # Trailing stop: highest high since entry (bars before the current one) minus trail_atr * ATR
        hh = np.where(after, Hn, -np.inf)
        run_max = np.maximum.accumulate(hh, axis=1)
        prev_max = np.concatenate([np.full((n, 1), -np.inf), run_max[:, :-1]], axis=1)
        prev_max = np.maximum(prev_max, px[:, None])
        stop_path = np.maximum(level[:, None], prev_max - trail_atr * atr[:, None])
    else:
        stop_path = np.repeat(level[:, None], m, axis=1)
    hit_stop = (Ln <= stop_path) & after
    stopped = hit_stop.any(axis=1)
    js = hit_stop.argmax(axis=1)
    stop_at = stop_path[i, js]
    gap_fill = np.where(js > j0, np.minimum(stop_at, np.nan_to_num(O[i, js], nan=np.inf)), stop_at)
    last_bar = m - 1 - np.argmax(~np.isnan(C[:, ::-1]), axis=1)
    close_px = C[i, last_bar]
    exit_px = np.where(stopped & (js <= last_bar), gap_fill, close_px)

    risk = px - level
    risk = np.where(np.isfinite(risk) & (risk > 0), risk, atr)
    filled = filled & np.isfinite(px) & (j0 <= last_bar)
    exit_px = np.where(filled, exit_px, np.nan)
    out = pd.DataFrame({
        "row": rows, "dir": direction.astype(int), "filled": filled,
        "entry_slot": np.array(SLOTS)[np.minimum(j0, m - 1)],
        "entry": np.abs(px), "stop": np.abs(level) if stop != "none" else np.nan, "exit": np.abs(exit_px),
        "stopped": stopped & (js <= last_bar),
        "ret": (exit_px - px) / np.abs(px),
        "R": (exit_px - px) / risk,
        "risk_pct": risk / np.abs(px),
    })
    return out
