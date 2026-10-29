import sys
import numpy as np
import pandas as pd
from intraday_reversal.research.bars import RESULTS_DIR

p = pd.read_parquet(RESULTS_DIR / f"panel_{sys.argv[1] if len(sys.argv) > 1 else '30m'}_1000.parquet")
p = p[~p.etf & p.relvol.notna() & p.atr.notna()].copy()
print(len(p), "stock-days")


def sort_table(p, sig, tgt="x_rest", q=5, cond=None):
    d = p if cond is None else p[cond]
    d = d.copy()
    d["b"] = d.groupby("day")[sig].transform(lambda x: pd.qcut(x.rank(method="first"), q, labels=False))
    t = d.groupby(["day", "b"])[tgt].mean().unstack()
    mean = t.mean() * 1e4
    ls = (t[q - 1] - t[0])
    tstat = ls.mean() / ls.std() * np.sqrt(len(ls))
    return " ".join(f"{m:6.1f}" for m in mean) + f" | top-bot {ls.mean()*1e4:6.1f}bp t={tstat:5.2f} n={len(ls)}"


for sig in ["x_gap", "x_r_early", "x_r_pc", "relvol", "mom20"]:
    print(f"{sig:10}", sort_table(p, sig))
print("--- high relvol only (top 30% of day)")
p["rv_rank"] = p.groupby("day").relvol.rank(pct=True)
for sig in ["x_gap", "x_r_early", "x_r_pc"]:
    print(f"{sig:10}", sort_table(p, sig, cond=p.rv_rank > 0.7))
print("--- low relvol only")
for sig in ["x_gap", "x_r_early", "x_r_pc"]:
    print(f"{sig:10}", sort_table(p, sig, cond=p.rv_rank < 0.3))

# Time-series: does the sign of the early move predict the rest (raw, per stock)?
print("--- time series, raw: rest-of-day return by early move in ATR units")
p["early_atr"] = (p.px - p.open) / p.atr
p["bucket"] = pd.cut(p.early_atr, [-9, -1, -0.5, -0.25, 0, 0.25, 0.5, 1, 9])
p["rest_atr"] = (p.rest * p.entry) / p.atr
print(p.groupby("bucket", observed=True).agg(n=("rest", "size"), rest_bp=("rest", lambda x: x.mean() * 1e4),
                                             x_rest_bp=("x_rest", lambda x: x.mean() * 1e4),
                                             rest_atr=("rest_atr", "mean")).round(2))
print("--- same, relvol > 2")
hv = p[p.relvol > 2]
print(hv.groupby("bucket", observed=True).agg(n=("rest", "size"), rest_bp=("rest", lambda x: x.mean() * 1e4),
                                              x_rest_bp=("x_rest", lambda x: x.mean() * 1e4)).round(2))
print("--- gap buckets (ATR units), rest from entry")
p["gap_atr"] = (p.open - p.pc) / p.atr
p["gb"] = pd.cut(p.gap_atr, [-9, -1, -0.5, -0.2, 0.2, 0.5, 1, 9])
print(p.groupby("gb", observed=True).agg(n=("rest", "size"), early_bp=("r_early", lambda x: x.mean() * 1e4),
                                         rest_bp=("rest", lambda x: x.mean() * 1e4),
                                         x_rest_bp=("x_rest", lambda x: x.mean() * 1e4)).round(2))
