"""Strategy parameters. Values mirror STRATEGY.md; [proposed] ones are the defaults under review."""
from dataclasses import dataclass, field, replace

TIMEFRAMES = ["30m", "1h", "4h", "1d", "1w"]  # all the backtest supports; Params.timeframes are traded
MA_TYPES = ["EMA"]  # EMA only (user decision 2026-10-28); "SMA" is still supported by bot.indicators.ma
MA_PERIODS = [5, 10, 20, 50, 100, 200]
ENTRY_PERIODS = [10, 20, 50, 100, 200]  # EMAs that can be entry points (5 dropped 2026-10-28)


@dataclass(frozen=True)
class Params:
    # Touch definition (section 3.1)
    atr_period: int = 14
    band_k: float = 0.25           # band = MA +/- band_k * ATR
    break_k: float = 1.5           # a close below MA - break_k * ATR resets the touch count
    min_touch_gap: int = 5         # bars between counted touches
    touch_lookback: int = 500      # previous touches must be within this many bars (was 100 with resets)
    touches_required: int = 3      # prior held touches before a signal
    slope_bars: int = 5            # MA must be above its value this many bars ago
    reset_on_break: bool = False   # False: a break doesn't erase past touches (they age out of the lookback)
    min_hold_ratio: float = 0.0    # with reset_on_break=False: held / (held + breaks) in the lookback

    # Entry (section 7)
    # "next_bar": after the touch bar closes and held, limit buy at its close + entry_offset_atr * ATR,
    # valid one bar. "touch": resting limit at the top of the band (previous bar's MA + band_k * ATR)
    # fills on the touch itself, with the stop at MA - stop_ma_atr * ATR; if the bar then closes below
    # the band (not held), sell at the close.
    entry_mode: str = "next_bar"
    entry_offset_atr: float = 0.1  # limit = touch-bar close + offset * ATR, valid one bar

    # Exits (section 8)
    stop_ma_atr: float = 1.0       # stop candidate: MA - stop_ma_atr * ATR
    stop_low_atr: float = 0.25     # stop candidate: touch-bar low - stop_low_atr * ATR
    breakeven_pct: float = 0.01    # move stop to entry once price is +1%
    breakeven_r: float = 0.0       # if > 0: move it once price is entry + breakeven_r * R instead
    target_r: float = 3.0          # sell the first half at this R multiple (3R beat 2R, backtest 2026-10-28)
    target_fraction: float = 0.5   # 1.0 = sell everything at the target
    trail_mode: str = "break"      # exit for the rest: "break", "band" or "chandelier" (see backtest/simulate.py)
    trail_atr: float = 3.0         # chandelier: stop at highest high since entry - trail_atr * ATR
    # EMA ladder exit (section 8): on these timeframes the stop climbs to each shorter EMA that price
    # closes above, sitting ladder_wiggle_atr * ATR below it; no partial target
    ladder_tfs: tuple = ("4h", "1d", "1w")
    ladder_wiggle_atr: float = 1.0   # best of 0-1 ATR on 4h, 1d and 1w (run 10)
    ladder_min_period: int = 20      # shortest EMA the stop may climb to; 20 beat 10 on 4h, 1d and 1w (run 10)
    ladder_partial_r: float = 0.0    # if > 0: on ladder timeframes, sell ladder_partial_fraction at this R
    ladder_partial_fraction: float = 0.25
    lock_at_r: float = 0.0         # profit lock: once price reaches entry + lock_at_r * R (0 = off) ...
    lock_to_r: float = 0.0         # ... move the stop to entry + lock_to_r * R
    min_risk_atr: float = 0.5      # skip entries whose stop is closer than this (after a gap down)
    # Per-timeframe exit settings that replace the ones above (best tested per timeframe, runs 9-10)
    tf_overrides: dict = field(default_factory=lambda: {
        "30m": {"target_r": 4.0, "target_fraction": 1.0},  # sell everything at 4R
        # buy on the touch, sell at the close if it didn't hold (adopted 2026-10-29, run 12); 1w keeps
        # the next-bar entry: its touch entry was much worse on the original 34 since 2022 (run 13)
        "1d": {"entry_mode": "touch"},
    })

    # Trading costs per side, as a fraction of price (backtest only).
    # Percent-based because historical prices are split-adjusted, which distorts per-share fees.
    commission_pct: float = 0.0001  # ~IBKR fixed $0.005/share on a $50 stock
    slippage_pct: float = 0.0003
    # Portfolio replay only: minimum commission per order in dollars (IBKR Fixed $1, Tiered ~$0.35;
    # 0 = percentage only) and the starting balance it applies to
    commission_min: float = 0.0
    start_equity: float = 1_000_000.0

    # Index counter-signals (section 4.2), evaluated on daily bars.
    # stretched, below_200 and big_drop are still computed but don't block (backtest 2026-10-28).
    counter_signals: tuple = ("overbought", "squeeze", "breakdown")
    rsi_period: int = 14
    rsi_overbought: float = 70.0
    stretch_atr: float = 2.0       # close more than this many ATR from the 5 or 10 MA
    stretch_periods: tuple = (5, 10)
    breakdown_periods: tuple = (50, 100, 200)
    breakdown_lookback: int = 3
    big_drop_atr: float = 2.0
    big_drop_lookback: int = 2
    squeeze_bb_std: float = 2.0
    squeeze_kc_atr: float = 1.5
    squeeze_period: int = 20
    # Index confluence: SPY touching one of these MAs (5/10 are touched almost every day)
    confluence_periods: tuple = (20, 50, 100, 200)
    # Timeframes that only trade with SPY confluence (unprofitable after costs without it)
    confluence_required_tfs: tuple = ("30m", "1h")

    # Trend screen on the traded symbol's daily bars (section 10): "off", "above_200" (close above
    # the 200-day EMA) or "rising_200" (also the EMA above its value trend_slope_days ago)
    trend_filter: str = "off"
    trend_slope_days: int = 20

    # Signals arriving at the same time across symbols: "none" takes them in any order; "quality"
    # takes higher timeframes first, then longer EMAs (per-trade edge rises with both, run 11)
    signal_priority: str = "quality"  # adopted 2026-10-28: higher median and far narrower range (run 11)
    # EMAs that may open positions in the portfolio (signals on others are ignored)
    entry_periods: tuple = (10, 20, 50, 100, 200)
    # Timeframes that are simulated and traded (30m/1h/4h dropped 2026-10-29, run 13)
    timeframes: tuple = ("1d", "1w")

    # Sizing (section 6), as a fraction of equity
    size_base: float = 0.05
    size_confluence: float = 0.10

    # Adding rule (section 9)
    # "strict": every open position at breakeven; "count": up to max_at_risk positions below breakeven;
    # "buffer": open risk of existing positions <= buffer_ratio x profit locked in by stops above entry
    adding_rule: str = "buffer"    # adopted 2026-10-28 (was "strict")
    max_at_risk: int = 0
    buffer_ratio: float = 2.0

    # Adding to a symbol already held (pyramiding): a new signal on the symbol opens another lot
    # if every existing lot of it is at breakeven or better
    max_lots: int = 3              # 1 = no pyramiding
    max_symbol_exposure: float = 0.20

    # Margin and leveraged ETFs (section 5.2)
    max_gross: float = 2.0         # Reg T: positions up to 2x equity
    leverage_above: float = 1.0    # beyond this gross exposure, prefer leveraged ETFs
    no_leverage_tfs: tuple = ("1w",)

    def for_tf(self, tf: str) -> "Params":
        """These parameters with the timeframe's overrides applied."""
        return replace(self, **self.tf_overrides.get(tf, {}))


DEFAULT = Params()
