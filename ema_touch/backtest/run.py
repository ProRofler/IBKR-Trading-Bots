"""Phase-1 backtest: every MA/timeframe combination, one trade per signal, measured in R.

Usage:
    python -m ema_touch.backtest.run                 # default parameters (break level 1.5 ATR)
    python -m ema_touch.backtest.run --break-k 0.25  # strict: any close below the band resets
Writes results/<name>_trades.parquet and results/<name>_by_combo.csv, prints a summary.
"""
import argparse
from dataclasses import replace
from pathlib import Path

import pandas as pd

from common.data import cache_path, load
from common.reference import load_reference
from common.universe import ALL_SYMBOLS
from ema_touch.backtest.simulate import simulate
from ema_touch.bot.market_filter import COUNTER_COLUMNS, attach, index_state, trend_state
from ema_touch.bot.params import DEFAULT, ENTRY_PERIODS, MA_TYPES, TIMEFRAMES, Params
from ema_touch.bot.rules import entry_allowed
from ema_touch.bot.signals import find_touch_signals

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"


def metrics(t: pd.DataFrame) -> pd.Series:
    wins, losses = t.loc[t.r > 0, "r"].sum(), -t.loc[t.r < 0, "r"].sum()
    return pd.Series({
        "trades": len(t),
        "win_rate": (t.r > 0).mean(),
        "hit_1r": t.hit_1r.mean(),
        "avg_r": t.r.mean(),
        "avg_r_cap10": t.r.clip(upper=10).mean(),  # robust to a few multi-year runners
        "gross_cap10": t.r_gross.clip(upper=10).mean(),
        "avg_cost_r": t.cost_r.mean(),
        "median_r": t.r.median(),
        "total_r": t.r.sum(),
        "profit_factor": wins / losses if losses else float("inf"),
        "median_bars": t.bars_held.median(),
    })


def run(p: Params, exit_variants: dict[str, Params] | None = None) -> pd.DataFrame | dict[str, pd.DataFrame]:
    """Simulate every signal. With exit_variants, signals are found once using p and each variant's
    exit rules are simulated on them; returns {variant name: trades}."""
    variants = exit_variants or {"": p}
    collected = {name: [] for name in variants}
    for symbol in ALL_SYMBOLS:
        for tf in TIMEFRAMES:
            if not cache_path(symbol, tf).exists():
                print(f"missing data: {symbol} {tf}")
                continue
            df = load(symbol, tf)
            for kind in MA_TYPES:
                for period in ENTRY_PERIODS:
                    sig = find_touch_signals(df, kind, period, p)
                    if sig.empty:
                        continue
                    for name, vp in variants.items():
                        trades = simulate(df, sig, kind, period, vp, tf)
                        if trades.empty:
                            continue
                        trades[["symbol", "tf", "ma_type", "period"]] = symbol, tf, kind, period
                        collected[name].append(trades)
    out = {name: add_context(pd.concat(parts, ignore_index=True), p) for name, parts in collected.items()}
    return out if exit_variants else out[""]


def add_context(trades: pd.DataFrame, p: Params) -> pd.DataFrame:
    """Attach index filter state (SPY, QQQ, DIA) and the tech flag to each trade."""
    trades = attach(trades, index_state(load("SPY", "1d"), p), "spy")
    for index in ("QQQ", "DIA"):
        trades = attach(trades, index_state(load(index, "1d"), p)[["counter"]], index.lower())
    sectors = load_reference()["sectors"]
    trades["is_tech"] = trades["symbol"].map(sectors).eq("Technology")
    return add_trend(trades, p)


def add_trend(trades: pd.DataFrame, p: Params) -> pd.DataFrame:
    """Attach each symbol's own daily trend screen flags (trend_above_200, trend_rising_200)."""
    states = [trend_state(load(s, "1d"), p).add_prefix("trend_").assign(symbol=s) for s in trades.symbol.unique()]
    right = pd.concat(states).reset_index().rename(columns={"end": "_t"}).sort_values("_t")
    left = trades.drop(columns=[c for c in trades if c.startswith("trend_")]).sort_values("time")
    return pd.merge_asof(left, right, left_on="time", right_on="_t", by="symbol", direction="backward").drop(columns="_t")


def report(trades: pd.DataFrame, name: str) -> None:
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 20)
    pd.set_option("display.float_format", lambda x: f"{x:.3f}")
    filtered = trades[entry_allowed(trades)]

    print("\n=== Overall ===")
    print(pd.DataFrame({"all signals": metrics(trades), "entry rules on": metrics(filtered)}).T)

    print("\n=== By timeframe (entry rules on) ===")
    print(filtered.groupby("tf").apply(metrics, include_groups=False).reindex(TIMEFRAMES))

    print("\n=== Each SPY counter-signal: avg R when active vs not (all signals) ===")
    rows = {}
    for col in COUNTER_COLUMNS:
        flag = trades[f"spy_{col}"]
        capped = trades.r.clip(upper=10)
        rows[col] = {"active_share": flag.mean(), "avg_r_cap10_active": capped[flag].mean(),
                     "avg_r_cap10_inactive": capped[~flag].mean(), "trades_active": flag.sum()}
    print(pd.DataFrame(rows).T)

    print("\n=== SPY confluence (SPY touching an MA), entry rules on ===")
    print(filtered.groupby("spy_touch").apply(metrics, include_groups=False))

    print("\n=== Exit reasons (entry rules on) ===")
    print(filtered.groupby("exit_reason").agg(trades=("r", "size"), avg_r=("r", "mean"), avg_peak_r=("peak_r", "mean"),
                                              took_partial=("took_partial", "mean")))

    combos = filtered.groupby(["tf", "ma_type", "period"]).apply(metrics, include_groups=False)
    combos = combos[combos.trades >= 30].sort_values("avg_r_cap10", ascending=False)
    combos.to_csv(RESULTS_DIR / f"{name}_by_combo.csv")
    print("\n=== Best 15 MA/timeframe combinations (entry rules on, >= 30 trades) ===")
    print(combos.head(15))
    print("\n=== Worst 10 ===")
    print(combos.tail(10))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--break-k", type=float, default=DEFAULT.break_k)
    parser.add_argument("--touches", type=int, default=DEFAULT.touches_required,
                        help="prior held touches required; 0 trades every touch (control group)")
    parser.add_argument("--reset", action="store_true", help="breaks reset the touch count (old rule)")
    parser.add_argument("--lookback", type=int, default=DEFAULT.touch_lookback)
    parser.add_argument("--min-hold-ratio", type=float, default=DEFAULT.min_hold_ratio)
    args = parser.parse_args()
    params = replace(DEFAULT, break_k=args.break_k, touches_required=args.touches,
                     reset_on_break=args.reset or DEFAULT.reset_on_break,
                     touch_lookback=args.lookback, min_hold_ratio=args.min_hold_ratio)
    changed = [
        f"break{args.break_k:g}" if args.break_k != DEFAULT.break_k else "",
        f"touches{args.touches}" if args.touches != DEFAULT.touches_required else "",
        "reset" if params.reset_on_break != DEFAULT.reset_on_break else "",
        f"lb{args.lookback}" if args.lookback != DEFAULT.touch_lookback else "",
        f"ratio{args.min_hold_ratio:g}" if args.min_hold_ratio != DEFAULT.min_hold_ratio else "",
    ]
    name = "_".join(x for x in changed if x) or "default"

    RESULTS_DIR.mkdir(exist_ok=True)
    trades = run(params)
    trades.to_parquet(RESULTS_DIR / f"{name}_trades.parquet")
    print(f"##### {name} #####")
    report(trades, name)
