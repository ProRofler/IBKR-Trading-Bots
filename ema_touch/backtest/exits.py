"""Compare take-profit / trailing-exit variants on the same signals.

Usage:
    python -m ema_touch.backtest.exits
Saves results/exit_<name>_trades.parquet per variant (usable with ema_touch.backtest.portfolio --trades exit_<name>).
"""
from dataclasses import replace

import pandas as pd

from ema_touch.backtest.run import RESULTS_DIR, run
from ema_touch.bot.params import DEFAULT, TIMEFRAMES
from ema_touch.bot.rules import entry_allowed

ROUND_1 = {
    # rules at the time: 50% at 2R, rest exits on a close below MA - 1.5 ATR
    "current": replace(DEFAULT, target_r=2.0),
    "half1R_break": replace(DEFAULT, target_r=1.0),
    "half3R_break": replace(DEFAULT, target_r=3.0),
    "half2R_band": replace(DEFAULT, trail_mode="band"),
    "half1R_chand2": replace(DEFAULT, target_r=1.0, trail_mode="chandelier", trail_atr=2.0),
    "half2R_chand2": replace(DEFAULT, trail_mode="chandelier", trail_atr=2.0),
    "half2R_chand3": replace(DEFAULT, trail_mode="chandelier", trail_atr=3.0),
    "chand3_only": replace(DEFAULT, target_fraction=0.0, trail_mode="chandelier", trail_atr=3.0),
    "all_at_2R": replace(DEFAULT, target_fraction=1.0, trail_mode="none"),
    "all_at_3R": replace(DEFAULT, target_r=3.0, target_fraction=1.0, trail_mode="none"),
}
# Round 2: keep the wide trail (it earns most of the profit), add a profit lock
ROUND_2 = {
    "current": replace(DEFAULT, target_r=2.0),
    "half3R_break": replace(DEFAULT, target_r=3.0),
    "lock1_025": replace(DEFAULT, target_r=2.0, lock_at_r=1.0, lock_to_r=0.25),
    "lock15_05": replace(DEFAULT, target_r=2.0, lock_at_r=1.5, lock_to_r=0.5),
    "half3R_lock1_025": replace(DEFAULT, target_r=3.0, lock_at_r=1.0, lock_to_r=0.25),
    "half3R_lock15_05": replace(DEFAULT, target_r=3.0, lock_at_r=1.5, lock_to_r=0.5),
}
# Round 3 (EMA only): EMA ladder on 4h/1d/1w vs R targets; 30m/1h keep half at 3R in all variants
ROUND_3 = {
    "r_targets": replace(DEFAULT, ladder_tfs=()),
    "ladder_w0": replace(DEFAULT, ladder_wiggle_atr=0.0),
    "ladder_w025": replace(DEFAULT, ladder_wiggle_atr=0.25),
    "ladder_w05": replace(DEFAULT, ladder_wiggle_atr=0.5),
    "ladder_w1": replace(DEFAULT, ladder_wiggle_atr=1.0),
}
# Round 4: ladder that stops climbing at the 10 or 20 EMA
ROUND_4 = {
    "r_targets": replace(DEFAULT, ladder_tfs=()),
    "ladder_min10_w05": replace(DEFAULT, ladder_min_period=10, ladder_wiggle_atr=0.5),
    "ladder_min10_w1": replace(DEFAULT, ladder_min_period=10, ladder_wiggle_atr=1.0),
    "ladder_min20_w05": replace(DEFAULT, ladder_min_period=20, ladder_wiggle_atr=0.5),
    "ladder_min20_w1": replace(DEFAULT, ladder_min_period=20, ladder_wiggle_atr=1.0),
}
# Round 5: 30m/1h sell the whole position at the target instead of half (4h/1d/1w keep the ladder).
# Ran before Params.tf_overrides existed; clear it to reproduce.
ROUND_5 = {
    "half3R_trail": replace(DEFAULT, tf_overrides={}),
    "whole_at_2R": replace(DEFAULT, target_r=2.0, target_fraction=1.0, tf_overrides={}),
    "whole_at_3R": replace(DEFAULT, target_r=3.0, target_fraction=1.0, tf_overrides={}),
    "whole_at_4R": replace(DEFAULT, target_r=4.0, target_fraction=1.0, tf_overrides={}),
}
# Round 6: ladder settings on 4h/1d/1w, to pick the best per timeframe (30m/1h unaffected)
VARIANTS = {
    "ladder_min10_w1": replace(DEFAULT, ladder_min_period=10, ladder_wiggle_atr=1.0),
    "ladder_min10_w05": replace(DEFAULT, ladder_min_period=10, ladder_wiggle_atr=0.5),
    "ladder_min20_w1": replace(DEFAULT, ladder_min_period=20, ladder_wiggle_atr=1.0),
    "ladder_min20_w05": replace(DEFAULT, ladder_min_period=20, ladder_wiggle_atr=0.5),
}


def summarize(t: pd.DataFrame) -> dict:
    wins, losses = t.loc[t.r > 0, "r"].sum(), -t.loc[t.r < 0, "r"].sum()
    big = t[t.peak_r >= 2]
    return {
        "trades": len(t),
        "win_rate": (t.r > 0).mean(),
        "avg_r": t.r.mean(),
        "avg_r_cap10": t.r.clip(upper=10).mean(),
        "profit_factor": wins / losses,
        "median_bars": t.bars_held.median(),
        # of trades that were at least +2R at some point, how much of the peak was kept
        "kept_of_peak": (big.r_gross / big.peak_r).median(),
        "reached_be": t.be_time.notna().mean(),
        "total_r_cap10": t.r.clip(upper=10).sum(),
    }


def main():
    results = run(DEFAULT, VARIANTS)
    rows, by_tf = {}, {}
    for name, trades in results.items():
        trades.to_parquet(RESULTS_DIR / f"exit_{name}_trades.parquet")
        t = trades[entry_allowed(trades)]
        rows[name] = summarize(t)
        by_tf[name] = t.groupby("tf").r.apply(lambda r: r.clip(upper=10).mean()).reindex(TIMEFRAMES)

    pd.set_option("display.width", 250)
    print("=== Exit variants (entry rules on, after costs) ===")
    print(pd.DataFrame(rows).T.to_string(float_format=lambda x: f"{x:.3f}"))
    print("\n=== Avg R (cap 10) by timeframe ===")
    print(pd.DataFrame(by_tf).T.to_string(float_format=lambda x: f"{x:.3f}"))


if __name__ == "__main__":
    main()
