"""Scanner variants x entry rules as portfolios.

Usage: python -m premarket_trend.research.scanner [--rules orb5_or orb15_or ...] [--start 2024-01-01]
"""
import argparse

import pandas as pd

from premarket_trend.days import grid
from premarket_trend.portfolio import by_period, daily_returns, select, stats
from premarket_trend.research.common import RULES, load_trades

SCANS = {
    "trend+gap0.3+rvol2 top5": dict(),
    "no trend filter": dict(trend=None),
    "against trend": dict(trend=False),
    "trend, gap>=1": dict(min_gap=1.0),
    "trend, gap 0.3-1": dict(max_gap=1.0),
    "trend, gap>=0 (any)": dict(min_gap=0.0),
    "trend, rvol>=1": dict(min_rvol=1.0),
    "trend, rvol>=4": dict(min_rvol=4.0),
    "trend, top 2": dict(top=2),
    "trend, top 10": dict(top=10),
    "trend, long only": dict(side="long"),
    "trend, short only": dict(side="short"),
    "trend, rank by gap": dict(rank="pm_gap_dir"),
    "trend=SMA50 side": dict(trend_def="sma50"),
    "trend=20-day move": dict(trend_def="r20"),
    "SMA50 trend, rvol>=4": dict(trend_def="sma50", min_rvol=4.0),
    "no trend, rvol>=4": dict(trend=None, min_rvol=4.0),
    "no trend, top 2": dict(trend=None, top=2),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rules", nargs="*", default=["open", "orb5_or", "orb15_or", "orb30_or"])
    ap.add_argument("--scans", nargs="*", default=list(SCANS))
    ap.add_argument("--start")
    ap.add_argument("--refresh", action="store_true", help="rebuild the cached trade tables")
    ap.add_argument("--periods", action="store_true", help="also print Sharpe per half-year")
    args = ap.parse_args()
    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", 30)
    all_days = pd.DatetimeIndex(grid("SPY")["days"])
    if args.start:
        all_days = all_days[all_days >= args.start]
    for rule in args.rules:
        t = load_trades(rule, args.start, args.refresh)
        rows, periods = {}, {}
        for name in args.scans:
            r, s = daily_returns(select(t, **SCANS[name]), all_days)
            rows[name] = stats(r, s)
            periods[name] = by_period(r)
        print(f"\n== {rule}: {RULES[rule]}   {all_days[0]:%Y-%m-%d} -> {all_days[-1]:%Y-%m-%d}")
        print(pd.DataFrame(rows).T)
        if args.periods:
            p = pd.DataFrame(periods).T
            p.columns = [f"{c:%Y-%m}" for c in p.columns]
            print(p)


if __name__ == "__main__":
    main()
