"""Robustness test: replay the portfolio many times instead of once.

A single portfolio run is one path. Signals that arrive at the same time (all daily bars close at
16:00) are taken first-come-first-served, so their order decides which symbols get the capital, and
that compounds over years. Each experiment here is run with many seeds:
- shuffled order: same-time signals in a random symbol order
- subsets: a random 75% of the symbols, also in a shuffled order (does it depend on a few names?)

Usage:
    python -m ema_touch.backtest.robust              # all experiments, 20 seeds each
    python -m ema_touch.backtest.robust --seeds 5
Writes results/robust_runs.csv (one row per run) and prints percentiles per experiment.
"""
import argparse
from dataclasses import replace
from multiprocessing import Pool

import numpy as np
import pandas as pd

from ema_touch.backtest.portfolio import UNIVERSES, WINDOWS, avg_exposure, simulate_portfolio, stats
from ema_touch.backtest.run import RESULTS_DIR, add_trend
from ema_touch.bot.params import DEFAULT, TIMEFRAMES

TRADES = {"run8_exits": "exit_half3R_trail", "run10_exits": "exit_next_bar",  # next-bar entry everywhere
          "touch_1d_1w": "exit_touch_1d_1w", "touch_1d": "exit_touch_1d", "current": "default",
          **{f"exit_{v}": f"exit_{v}" for v in ("base", "be_05R", "be_1R", "be_2R", "be_3R", "be_off",
                                                 "p25_2R", "be_1R_p25_2R")}}
# Rules use the current defaults, so earlier rounds rerun today trade only Params.timeframes
RULES = {
    "default": DEFAULT,
    "all_timeframes": replace(DEFAULT, timeframes=tuple(TIMEFRAMES)),
    "no_leveraged_etfs": replace(DEFAULT, leverage_above=99.0),
    "no_margin": replace(DEFAULT, max_gross=1.0),
    "strict": replace(DEFAULT, adding_rule="strict", max_lots=1),
    "quality_first": replace(DEFAULT, signal_priority="quality"),
    "no_ema10": replace(DEFAULT, entry_periods=(20, 50, 100, 200)),
    "no_ema10_20": replace(DEFAULT, entry_periods=(50, 100, 200)),
    "quality_first_no_lev": replace(DEFAULT, signal_priority="quality", leverage_above=99.0),
    "quality_first_no_margin": replace(DEFAULT, signal_priority="quality", max_gross=1.0),
    "10k_fixed": replace(DEFAULT, start_equity=10_000.0, commission_min=1.0),   # IBKR Fixed: $1 minimum per order
    "10k_tiered": replace(DEFAULT, start_equity=10_000.0, commission_min=0.35),  # IBKR Tiered: ~$0.35 minimum
}
TRENDS = ["off", "above_200", "rising_200"]

# name -> (trades, universe, rules, trend screen, symbol subset share)
EXPERIMENTS = {
    "run8 exits, all": ("run8_exits", "all", "default", "off", 1.0),
    "run10 exits, all": ("run10_exits", "all", "default", "off", 1.0),
    "run8 exits, original": ("run8_exits", "original", "default", "off", 1.0),
    "run10 exits, original": ("run10_exits", "original", "default", "off", 1.0),
    "run10, all, above 200": ("run10_exits", "all", "default", "above_200", 1.0),
    "run10, all, rising 200": ("run10_exits", "all", "default", "rising_200", 1.0),
    "run10, original, rising 200": ("run10_exits", "original", "default", "rising_200", 1.0),
    "run10, all, no leveraged ETFs": ("run10_exits", "all", "no_leveraged_etfs", "off", 1.0),
    "run10, all, no margin": ("run10_exits", "all", "no_margin", "off", 1.0),
    "run10, all, strict": ("run10_exits", "all", "strict", "off", 1.0),
    "run10, all, rising 200, no lev": ("run10_exits", "all", "no_leveraged_etfs", "rising_200", 1.0),
    "run10, all, rising 200, no margin": ("run10_exits", "all", "no_margin", "rising_200", 1.0),
    "run10, 75% subsets": ("run10_exits", "all", "default", "off", 0.75),
    "run10, 75% subsets, rising 200": ("run10_exits", "all", "default", "rising_200", 0.75),
    # Round 2: which signals get the capital
    "run10, all, quality first": ("run10_exits", "all", "quality_first", "off", 1.0),
    "run10, all, no 10 EMA": ("run10_exits", "all", "no_ema10", "off", 1.0),
    "run10, all, no 10/20 EMA": ("run10_exits", "all", "no_ema10_20", "off", 1.0),
    "run10, original, quality first": ("run10_exits", "original", "quality_first", "off", 1.0),
    "run10, 75% subsets, quality first": ("run10_exits", "all", "quality_first", "off", 0.75),
    "run10, all, quality first, no lev": ("run10_exits", "all", "quality_first_no_lev", "off", 1.0),
    "run10, all, quality first, no margin": ("run10_exits", "all", "quality_first_no_margin", "off", 1.0),
    # Round 3: entry on the touch itself (sell at the close if it didn't hold) vs the next bar
    "entry next bar": ("run10_exits", "all", "default", "off", 1.0),
    "entry touch 1d+1w": ("touch_1d_1w", "all", "default", "off", 1.0),
    "entry touch 1d": ("touch_1d", "all", "default", "off", 1.0),
    "entry next bar, 75% subsets": ("run10_exits", "all", "default", "off", 0.75),
    "entry touch 1d, 75% subsets": ("touch_1d", "all", "default", "off", 0.75),
    # Round 4: trade only 1d and 1w (touch entry on both)
    "all timeframes": ("touch_1d_1w", "all", "all_timeframes", "off", 1.0),
    "1d+1w": ("touch_1d_1w", "all", "default", "off", 1.0),
    "1d+1w, no leveraged ETFs": ("touch_1d_1w", "all", "no_leveraged_etfs", "off", 1.0),
    "1d+1w, no margin": ("touch_1d_1w", "all", "no_margin", "off", 1.0),
    "1d+1w, original 34": ("touch_1d_1w", "original", "default", "off", 1.0),
    "1d+1w, 75% subsets": ("touch_1d_1w", "all", "default", "off", 0.75),
    "1d+1w, strict": ("touch_1d_1w", "all", "strict", "off", 1.0),
    "all timeframes, original 34": ("touch_1d_1w", "original", "all_timeframes", "off", 1.0),
    "1d+1w next-bar entry, original 34": ("run10_exits", "original", "default", "off", 1.0),
    "1d+1w next-bar entry": ("run10_exits", "all", "default", "off", 1.0),
    "1d touch + 1w next-bar": ("touch_1d", "all", "default", "off", 1.0),
    "1d touch + 1w next-bar, original 34": ("touch_1d", "original", "default", "off", 1.0),
    "1d touch + 1w next-bar, 75% subsets": ("touch_1d", "all", "default", "off", 0.75),
    # Round 5: 56 steady large caps added (current default trades)
    "all 152": ("current", "all", "default", "off", 1.0),
    "previous 96": ("current", "previous", "default", "off", 1.0),
    "steady 56 only": ("current", "steady", "default", "off", 1.0),
    "original 34": ("current", "original", "default", "off", 1.0),
    "all 152, 75% subsets": ("current", "all", "default", "off", 0.75),
    "all 152, no margin": ("current", "all", "no_margin", "off", 1.0),
    # Round 6: later breakeven / partial profit (previous 96), at $1M with % costs and at $10k with
    # IBKR's minimum commission per order
    **{f"{v}{label}": (f"exit_{v}", "previous", rules, "off", 1.0)
       for v in ("base", "be_05R", "be_1R", "be_2R", "be_3R", "be_off", "p25_2R", "be_1R_p25_2R")
       for label, rules in ((", $1M", "default"), (", $10k fixed", "10k_fixed"), (", $10k tiered", "10k_tiered"))},
}

_trades: dict[str, pd.DataFrame] = {}


def _init():
    for key, name in TRADES.items():
        _trades[key] = add_trend(pd.read_parquet(RESULTS_DIR / f"{name}_trades.parquet"), DEFAULT)


def _one(job) -> list[dict]:
    exp, seed = job
    trades_key, universe, rules, trend, share = EXPERIMENTS[exp]
    trades = _trades[trades_key]
    symbols = list(UNIVERSES[universe])
    if share < 1:
        symbols = list(np.random.default_rng(1000 + seed).choice(symbols, int(len(symbols) * share), replace=False))
    trades = trades[trades.symbol.isin(symbols)]
    p = replace(RULES[rules], trend_filter=trend)
    rows = []
    for window, start in WINDOWS.items():
        log, equity = simulate_portfolio(trades, pd.Timestamp(start, tz="UTC"), p, seed=seed)
        rows.append({"experiment": exp, "seed": seed, "window": window, **stats(equity),
                     "avg_exposure": avg_exposure(log, equity),
                     "positions": int(log.action.isin(["enter", "add"]).sum())})
    return rows


def summarize(runs: pd.DataFrame) -> pd.DataFrame:
    g = runs.groupby(["window", "experiment"], sort=False)
    return pd.DataFrame({
        "CAGR p10": g.CAGR.quantile(0.1), "CAGR median": g.CAGR.median(), "CAGR p90": g.CAGR.quantile(0.9),
        "maxDD median": g.max_drawdown.median(), "maxDD worst": g.max_drawdown.min(),
        "sharpe median": g.sharpe.median(), "exposure": g.avg_exposure.median(), "runs": g.size(),
    })


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=20)
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--only", nargs="*", default=list(EXPERIMENTS))
    parser.add_argument("--match", help="run the experiments whose name contains this text")
    parser.add_argument("--out", default="robust_runs", help="results/<out>.csv")
    args = parser.parse_args()
    if args.match:
        args.only = [e for e in EXPERIMENTS if args.match in e]
    jobs = [(exp, seed) for exp in args.only for seed in range(args.seeds)]
    with Pool(args.workers, initializer=_init) as pool:
        runs = pd.DataFrame([row for rows in pool.imap_unordered(_one, jobs) for row in rows])
    runs.to_csv(RESULTS_DIR / f"{args.out}.csv", index=False)

    pd.set_option("display.width", 250)
    summary = summarize(runs)
    for window in WINDOWS:
        print(f"\n===== {window} =====")
        print(summary.loc[window].reindex(args.only).to_string(float_format=lambda x: f"{x:.3f}"))


if __name__ == "__main__":
    main()
