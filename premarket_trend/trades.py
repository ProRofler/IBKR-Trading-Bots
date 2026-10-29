"""All candidate trades: every symbol-day simulated long and short with a given entry/exit rule,
joined with the pre-market features. Selection rules (the scanner) then pick rows from this table."""
import numpy as np
import pandas as pd

from common.universe import DAYTRADE_SYMBOLS
from premarket_trend.days import days, grid
from premarket_trend.simulate import simulate

ETFS = {"SPY", "QQQ", "DIA", "IWM", "SMH", "SOXX", "XLK", "XLI", "XLF", "ITA", "URA", "GLD", "SLV", "GDX",
        "MAGS", "DRAM", "IBIT", "XLE", "XLV", "TLT", "XBI"}
FEATURES = ["prev_close", "atr", "trend", "r20_atr", "above50", "dollar_vol", "pm_vol", "pm_rvol",
            "pm_turnover", "pm_gap_atr", "open", "gap_atr", "rvol5", "first_bar"]

# Costs per side: commission per share and slippage as a fraction of price
COMMISSION = 0.005
SLIPPAGE = 0.0002


def all_trades(symbols=DAYTRADE_SYMBOLS, start=None, **rule) -> pd.DataFrame:
    frames = []
    for s in symbols:
        x = days(s)
        if x.empty:
            continue
        x = x[x["atr"].notna() & x["open"].notna()]
        if start:
            x = x[x.index >= start]
        if x.empty:
            continue
        g = grid(s)
        for direction in (1, -1):
            t = simulate(g, x["row"].to_numpy(), np.full(len(x), direction), x["atr"].to_numpy(), **rule)
            t.index = x.index
            # A market-on-close exit fills at the official close (the daily bar), not the last 5-min trade
            moc = t["filled"] & ~t["stopped"] & x["d_close"].notna()
            t.loc[moc, "exit"] = x.loc[moc, "d_close"]
            t["ret"] = t["dir"] * (t["exit"] - t["entry"]) / t["entry"]
            t["R"] = t["ret"] / t["risk_pct"]
            t = pd.concat([t.drop(columns="row"), x[FEATURES]], axis=1)
            t["sym"] = s
            frames.append(t)
    t = pd.concat(frames)
    t.index.name = "day"
    t["etf"] = t["sym"].isin(ETFS)
    t["cost"] = 2 * (COMMISSION / t["entry"] + SLIPPAGE)
    t["net"] = t["ret"] - t["cost"]
    t["net_R"] = t["net"] / t["risk_pct"]
    # Features signed by the trade's direction
    t["with_trend"] = t["trend"] * t["dir"]
    t["pm_gap_dir"] = t["pm_gap_atr"] * t["dir"]
    t["gap_dir"] = t["gap_atr"] * t["dir"]
    return t.reset_index()
