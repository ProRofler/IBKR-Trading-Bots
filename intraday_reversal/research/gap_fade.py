import sys
import numpy as np
import pandas as pd
from intraday_reversal.research.bars import RESULTS_DIR

p = pd.read_parquet(RESULTS_DIR / f"panel_{sys.argv[1] if len(sys.argv) > 1 else '30m'}_1000.parquet")
p = p[p.atr.notna() & p.relvol.notna()].copy()
p["gap_atr"] = (p.open - p.pc) / p.atr
p["early_atr"] = (p.px - p.open) / p.atr
p["mkt_gap_abs"] = p.mkt_gap.abs()
p["x_gap_atr"] = p.x_gap * p.pc / p.atr
p["fade"] = -np.sign(p.gap)  # trade direction: against the gap
p["fade_rest"] = p.fade * p.rest
p["fade_xrest"] = p.fade * p.x_rest
p["year"] = p.day.dt.year
p["agap"] = p.gap_atr.abs()
p["gb"] = pd.cut(p.agap, [0, 0.2, 0.35, 0.5, 0.75, 1, 1.5, 9])
f = lambda x: x.mean() * 1e4
agg = dict(n=("fade_rest", "size"), fade_bp=("fade_rest", f), fade_x_bp=("fade_xrest", f),
           t=("fade_rest", lambda x: x.mean() / x.std() * np.sqrt(len(x))))
for lab, sub in [("stocks", p[~p.etf]), ("etfs", p[p.etf])]:
    print("=====", lab)
    print(sub.groupby("gb", observed=True).agg(**agg).round(2))
s = p[~p.etf]
print("--- stocks, gap 0.35-1.0 ATR by relvol")
m = s[(s.agap > 0.35) & (s.agap < 1.0)]
print(m.groupby(pd.cut(m.relvol, [0, 0.8, 1.2, 1.6, 2.5, 99]), observed=True).agg(**agg).round(2))
print("--- by whether first 30m extended the gap (+) or faded it (-)")
m = m.assign(ext=np.sign(m.r_early) == np.sign(m.gap))
print(m.groupby("ext").agg(**agg).round(2))
print("--- by market gap size (abs SPY gap %)")
print(m.groupby(pd.cut(m.mkt_gap_abs * 100, [-0.01, 0.2, 0.5, 1, 9]), observed=True).agg(**agg).round(2))
print("--- same direction as market gap?")
print(m.groupby(np.sign(m.gap) == np.sign(m.mkt_gap)).agg(**agg).round(2))
print("--- by gap direction")
print(m.groupby(np.sign(m.gap)).agg(**agg).round(2))
print("--- by year")
print(m.groupby("year").agg(**agg).round(2))
print("--- per-day portfolio (avg across qualifying stocks)")
dd = m.groupby("day").fade_rest.mean()
print(len(dd), "days", round(dd.mean() * 1e4, 2), "bp/day", "sharpe", round(dd.mean() / dd.std() * np.sqrt(252), 2))
