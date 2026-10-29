"""Which pre-market features predict an intraday trade's result?

For one entry/exit rule, every stock-day is simulated long and short. Tables show the average
net R (after costs) and net bp per filled trade, split by the daily trend relative to the trade's
direction, the pre-market gap in the trade's direction, and pre-market relative volume.

Usage: python -m premarket_trend.research.factors orb5_or [--start 2025-01-01]
"""
import argparse

import numpy as np
import pandas as pd

from premarket_trend.research.common import RULES, load_trades


def summary(t: pd.DataFrame, by: list) -> pd.DataFrame:
    f = t[t["filled"]]
    g = f.groupby(by, observed=True)
    out = pd.DataFrame({
        "signals": t.groupby(by, observed=True).size(),
        "fill%": (g.size() / t.groupby(by, observed=True).size() * 100).round(0),
        "net_R": g["net_R"].mean().round(3),
        "t": (g["net_R"].mean() / g["net_R"].sem()).round(1),
        "net_bp": (g["net"].mean() * 1e4).round(1),
        "win%": (g["net"].apply(lambda r: (r > 0).mean()) * 100).round(0),
    })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rule", choices=list(RULES))
    ap.add_argument("--start")
    ap.add_argument("--refresh", action="store_true", help="rebuild the cached trade table")
    args = ap.parse_args()
    pd.set_option("display.width", 200)
    pd.set_option("display.max_rows", 200)
    t = load_trades(args.rule, args.start, args.refresh)
    t = t[~t["etf"] & (t["prev_close"] >= 5) & t["pm_rvol"].notna()]
    print(f"Rule {args.rule}: {RULES[args.rule]}  stocks, {t['day'].min():%Y-%m-%d} -> {t['day'].max():%Y-%m-%d}, "
          f"{t['sym'].nunique()} symbols, {len(t) // 2} stock-days")
    t["trend_rel"] = t["with_trend"].map({1: "with", 0: "none", -1: "against"})
    t["pm_gap"] = pd.cut(t["pm_gap_dir"], [-99, -1, -0.3, 0.3, 1, 2, 99],
                         labels=["<-1", "-1..-0.3", "-0.3..0.3", "0.3..1", "1..2", ">2"])
    t["rvol"] = pd.cut(t["pm_rvol"], [0, 1, 2, 4, 8, 1e9], labels=["<1", "1-2", "2-4", "4-8", ">8"])

    print("\n== All stock-days by trend relative to the trade")
    print(summary(t, ["trend_rel"]))
    print("\n== By pre-market gap in the trade's direction (ATRs)")
    print(summary(t, ["pm_gap"]))
    print("\n== By pre-market relative volume")
    print(summary(t, ["rvol"]))
    print("\n== Gap with the trade >= 0.3 ATR: relative volume x trend")
    print(summary(t[t["pm_gap_dir"] >= 0.3], ["rvol", "trend_rel"]))
    print("\n== Gap with the trade >= 0.3 ATR and relative volume >= 2: by side and trend")
    q = t[(t["pm_gap_dir"] >= 0.3) & (t["pm_rvol"] >= 2)].assign(side=lambda x: np.where(x["dir"] > 0, "long", "short"))
    print(summary(q, ["side", "trend_rel"]))
    print("\n== Same, by half-year (with trend only)")
    q = q[q["with_trend"] == 1]
    print(summary(q.assign(half=q["day"].dt.year.astype(str) + "H" + ((q["day"].dt.month > 6) + 1).astype(str)), ["half"]))


if __name__ == "__main__":
    main()
