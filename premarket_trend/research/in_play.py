"""Stocks in play: trade in the direction of the pre-market gap, only the names with the most
unusual pre-market activity, with and without the daily trend filter.

Exploration period: 2025-11 -> 2026-10 (the first 12 months downloaded). Older months are kept
for an out-of-sample check of whatever is chosen here (--period oos).

Usage: python -m premarket_trend.research.in_play [--period explore|oos|all] [--rules ...]
"""
import argparse
import itertools

import numpy as np
import pandas as pd

from premarket_trend.days import grid
from premarket_trend.portfolio import by_period, daily_returns, select, stats
from premarket_trend.research.common import RULES, load_trades

EXPLORE_START = "2025-11-01"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rules", nargs="*", default=["orb5_or", "orb15_or", "orb5_atr25", "orb15_or_trail"])
    ap.add_argument("--period", default="explore", choices=["explore", "oos", "all"])
    ap.add_argument("--refresh", action="store_true")
    args = ap.parse_args()
    pd.set_option("display.width", 220)
    pd.set_option("display.max_rows", 500)
    days = pd.DatetimeIndex(grid("SPY")["days"])
    if args.period == "explore":
        days = days[days >= EXPLORE_START]
    elif args.period == "oos":
        days = days[days < EXPLORE_START]
    print(f"Period {args.period}: {days[0]:%Y-%m-%d} -> {days[-1]:%Y-%m-%d}")

    for rule in args.rules:
        t = load_trades(rule, refresh=args.refresh)
        t = t[t["day"].isin(days)]
        rows = {}
        for rank, (min_gap, top, trend) in itertools.product(
                ["pm_rvol", "pm_turnover"], itertools.product([0.5, 1.0, 2.0], [1, 3, 5], [None, True, False])):
            sel = select(t, min_gap=min_gap, min_rvol=0, top=top, trend=trend, rank=rank)
            r, s = daily_returns(sel, days)
            st = stats(r, s)
            q = by_period(r)
            st["Q+"] = f"{(q > 0).sum()}/{q.notna().sum()}"
            trend_name = {None: "any", True: "with", False: "against"}[trend]
            rows[(rank, min_gap, top, trend_name)] = st
        out = pd.DataFrame(rows).T
        out.index.names = ["rank", "gap>=", "top", "trend"]
        print(f"\n== {rule}: {RULES[rule]}")
        print(out[["trades", "net_R", "t", "net_bp", "win%", "Sharpe", "maxDD%", "Q+"]])


if __name__ == "__main__":
    main()
