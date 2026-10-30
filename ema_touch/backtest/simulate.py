"""Simulate one trade per signal using the entry and exit rules (STRATEGY.md sections 7-8).

Intrabar order is unknown, so ties are resolved pessimistically: on a bar that reaches both the
stop and the target, the stop is assumed to hit first. Commissions and slippage are charged per
side as a percentage of price (Params.commission_pct + slippage_pct) and deducted from R.

Exit for the part left after the partial target (Params.trail_mode):
- "break":      close below MA - break_k * ATR
- "band":       close below MA - band_k * ATR (the touch band)
- "chandelier": stop trails at highest high since entry - trail_atr * ATR, checked intrabar

On Params.ladder_tfs the EMA ladder replaces all of that (no partial target unless
Params.ladder_partial_r): when a bar closes above
a shorter EMA than the current support, that EMA becomes the support and the stop moves to
EMA - ladder_wiggle_atr * ATR, updated every bar and never lowered. The entry EMA itself only acts as
support once the stop has reached breakeven.

Params.entry_mode "touch" buys on the touch bar itself (see bot.signals.find_touch_signals) and sells at
its close if the touch didn't hold; the close stands in for the check shortly before the close.
"""
import pandas as pd

from common.indicators import atr as calc_atr
from common.indicators import ma as calc_ma
from ema_touch.bot.params import DEFAULT, MA_PERIODS, Params


def _stop_label(stop: float, entry: float) -> str:
    return "stop" if stop < entry else "breakeven" if stop == entry else "trail"


def simulate(df: pd.DataFrame, signals: pd.DataFrame, kind: str, period: int, p: Params = DEFAULT,
             tf: str = "") -> pd.DataFrame:
    p = p.for_tf(tf)
    o, h, l, c = (df[col].to_numpy() for col in ("open", "high", "low", "close"))
    ma = calc_ma(df["close"], kind, period).to_numpy()
    atr = calc_atr(df, p.atr_period).to_numpy()
    ladder = tf in p.ladder_tfs
    if ladder:
        # shorter EMAs, shortest first; the entry EMA is the last rung
        rungs = [q for q in MA_PERIODS if p.ladder_min_period <= q < period] + [period]
        rung_ema = {q: calc_ma(df["close"], "EMA", q).to_numpy() for q in rungs}
    if ladder:
        close_exit = None
    elif p.trail_mode == "break":
        close_exit = ma - max(p.break_k, p.band_k) * atr
    elif p.trail_mode == "band":
        close_exit = ma - p.band_k * atr
    else:
        close_exit = None
    n = len(df)
    touch = p.entry_mode == "touch"

    trades = []
    busy_until = -1  # one open trade per symbol/MA/timeframe at a time
    for sig in signals.itertuples():
        i = sig.i
        if touch:
            # Filled on the touch bar itself; its low and close aren't known yet when the order rests
            if i <= busy_until:
                continue
            j = i
            stop = sig.ma - p.stop_ma_atr * sig.atr
            if o[j] <= stop:
                continue  # opened below the stop: the bracket would exit at once
            entry = min(o[j], sig.level)
            risk_atr = sig.atr
        else:
            if i <= busy_until or i + 1 >= n:
                continue
            limit = c[i] + p.entry_offset_atr * atr[i]
            j = i + 1
            if o[j] <= limit:
                entry = o[j]
            elif l[j] <= limit:
                entry = limit
            else:
                continue  # gapped above the limit: signal expires
            stop = min(ma[i] - p.stop_ma_atr * atr[i], l[i] - p.stop_low_atr * atr[i])
            risk_atr = atr[i]
        risk = entry - stop
        if risk < p.min_risk_atr * risk_atr:
            continue  # gapped down to just above the stop: R would be meaningless
        target_r, target_fraction = (p.ladder_partial_r, p.ladder_partial_fraction) if ladder else (p.target_r, p.target_fraction)
        target = entry + target_r * risk
        be_trigger = entry + p.breakeven_r * risk if p.breakeven_r else entry * (1 + p.breakeven_pct)

        partial_done = ladder and not p.ladder_partial_r
        remaining, realized_r, hit_1r, be_k = 1.0, 0.0, False, None
        partial_k = None
        peak = entry
        support = period  # current ladder rung (EMA period)
        # stop history as (time it takes effect, stop / entry), for the portfolio's risk accounting
        # (touch entries start from the signal time, the previous bar's end; earlier lookups use the first
        # level anyway)
        stop_times, stop_levels = [df.index[i - 1 if touch else i].value], [stop / entry]
        exit_reason, k = "open", j
        first = j
        intraday = p.breakeven_intraday != "off"

        def be_stamp(bar: int) -> int:
            # when the breakeven counts for the portfolio's risk accounting: from the bar's start (the
            # previous bar's end) or its end
            return max(df.index[bar - 1 if p.breakeven_frees_same_bar else bar].value, stop_times[-1])

        if touch:
            # The touch bar after the fill: its high may have come before the fill, so only the stop and
            # the close count, unless the high clearly came after the fill (intraday breakeven)
            first = j + 1
            high_after_fill = intraday and h[j] >= be_trigger and (c[j] >= o[j] or o[j] <= sig.level)
            if high_after_fill and c[j] < o[j]:
                # filled at the open, then open-high-low-close: breakeven before the low
                stop, be_k = entry, j
                stop_times.append(be_stamp(j))
                stop_levels.append(1.0)
                if l[j] <= entry:
                    remaining, exit_reason = 0.0, "breakeven"
            elif high_after_fill and l[j] > stop:
                # open-low-high-close: filled on the way down, breakeven on the way up, then the close
                stop, be_k = entry, j
                stop_times.append(be_stamp(j))
                stop_levels.append(1.0)
                if c[j] <= entry:
                    remaining, exit_reason = 0.0, "breakeven"
            elif l[j] <= stop:
                realized_r, remaining, exit_reason = (stop - entry) / risk, 0.0, "stop"
            elif not sig.held:
                realized_r, remaining, exit_reason = (c[j] - entry) / risk, 0.0, "not_held"
            elif c[j] >= be_trigger:
                stop, be_k = entry, j
                stop_times.append(df.index[j].value)
                stop_levels.append(1.0)
        for k in range(first, n if remaining > 0 else first):
            if o[k] <= stop and k > j:
                realized_r += remaining * (o[k] - entry) / risk
                exit_reason = _stop_label(stop, entry) + "_gap"
                remaining = 0.0
                break
            if intraday and stop < entry and h[k] >= be_trigger:
                high_first = o[k] >= be_trigger or (p.breakeven_intraday == "path" and c[k] < o[k])
                if high_first or l[k] > stop:
                    stop, be_k = entry, k
                    stop_times.append(be_stamp(k))
                    stop_levels.append(1.0)
                    # after the trigger, price came back to entry: the low if the high came first, else
                    # the close ("worst" always assumes the low came after)
                    back = l[k] if high_first or p.breakeven_intraday == "worst" else c[k]
                    if back <= entry:
                        exit_reason, remaining = "breakeven", 0.0
                        break
            if l[k] <= stop:
                realized_r += remaining * (stop - entry) / risk
                exit_reason = _stop_label(stop, entry)
                remaining = 0.0
                break
            peak = max(peak, h[k])
            if h[k] >= entry + risk:
                hit_1r = True
            if not partial_done and h[k] >= target:
                fill = max(target, o[k]) if k > j else target
                realized_r += target_fraction * (fill - entry) / risk
                remaining -= target_fraction
                partial_done = True
                partial_k = k
                if remaining <= 1e-9:
                    exit_reason = "target"
                    break
            if close_exit is not None and c[k] < close_exit[k]:
                realized_r += remaining * (c[k] - entry) / risk
                exit_reason = "ma_break"
                remaining = 0.0
                break
            # Stop updates take effect from the next bar
            prev_stop = stop
            if h[k] >= be_trigger and stop < entry:
                stop = entry
                be_k = k
            if p.lock_at_r and peak >= entry + p.lock_at_r * risk:
                stop = max(stop, entry + p.lock_to_r * risk)
            if ladder:
                for q in rungs:
                    if q >= support:
                        break
                    if c[k] > rung_ema[q][k]:
                        support = q
                        break
                if support < period or stop >= entry:
                    stop = max(stop, rung_ema[support][k] - p.ladder_wiggle_atr * atr[k])
            elif p.trail_mode == "chandelier":
                stop = max(stop, peak - p.trail_atr * atr[k])
            if be_k is None and stop >= entry:
                be_k = k
            if stop != prev_stop:
                stop_times.append(df.index[k].value)
                stop_levels.append(stop / entry)
        if remaining > 0:
            realized_r += remaining * (c[k] - entry) / risk
        busy_until = k
        # Entry plus exit(s); exits happen near entry price in R terms, so cost both sides at entry
        cost_r = 2 * (p.commission_pct + p.slippage_pct) * entry / risk

        trades.append({
            "time": sig.time, "entry_time": df.index[j], "exit_time": df.index[k],
            "entry": entry, "risk_pct": risk / entry, "r": realized_r - cost_r,
            "r_gross": realized_r, "cost_r": cost_r,
            "peak_r": (peak - entry) / risk,  # best price reached while open
            "hit_1r": hit_1r, "exit_reason": exit_reason, "bars_held": k - j + 1,
            # when the stop reached entry (position out of risk), NaT if it never did
            "be_time": df.index[be_k] if be_k is not None else pd.NaT,
            "took_partial": partial_k is not None,
            "partial_fraction": target_fraction if partial_k is not None else 0.0,
            "partial_time": df.index[partial_k] if partial_k is not None else pd.NaT,
            "stop_times": stop_times, "stop_levels": stop_levels,
            "final_support": support if ladder else None,
            "prior_touches": sig.prior_touches,
        })
    return pd.DataFrame(trades)
