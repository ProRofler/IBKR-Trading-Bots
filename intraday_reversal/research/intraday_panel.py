"""Stock-day feature panel: what happens early in the day vs the rest of the day."""
import sys
import numpy as np
import pandas as pd
from common.data import load
from common.indicators import atr
from common.universe import ALL_SYMBOLS
from intraday_reversal.research.bars import grid, RESULTS_DIR

ETF = {"SPY", "QQQ", "DIA", "SMH", "SOXX", "XLK", "XLI", "XLF", "ITA", "URA", "GLD", "SLV", "GDX", "MAGS", "DRAM", "IBIT"}


def build(tf="30m", entry_slot="10:00"):
    rows = []
    spy = grid("SPY", tf)
    for s in ALL_SYMBOLS:
        try:
            g = grid(s, tf)
        except Exception as e:
            print(s, e)
            continue
        slots = list(g["close"].columns)
        i = slots.index(entry_slot)
        C, O, V, H, L = g["close"], g["open"], g["volume"], g["high"], g["low"]
        d = pd.DataFrame(index=C.index)
        d["sym"] = s
        d["etf"] = s in ETF
        d["pc"] = g["pclose"]
        d["open"] = g["dopen"]
        d["px"] = C[entry_slot]
        d["gap"] = g["dopen"] / g["pclose"] - 1
        d["r_early"] = C[entry_slot] / g["dopen"] - 1           # open -> entry slot
        d["r_pc"] = C[entry_slot] / g["pclose"] - 1              # prev close -> entry slot
        nxt = slots[i + 1]
        d["entry"] = O[nxt]                                     # fill at next bar open
        d["rest"] = g["dclose"] / O[nxt] - 1                     # entry -> close
        d["hi_rest"] = H.loc[:, nxt:].max(axis=1) / O[nxt] - 1
        d["lo_rest"] = L.loc[:, nxt:].min(axis=1) / O[nxt] - 1
        d["or_hi"] = H.loc[:, :entry_slot].max(axis=1)
        d["or_lo"] = L.loc[:, :entry_slot].min(axis=1)
        v_early = V.loc[:, :entry_slot].sum(axis=1)
        d["relvol"] = v_early / v_early.rolling(14).mean().shift(1)
        dret = g["dclose"].pct_change()
        d["dvol"] = dret.rolling(20).std().shift(1)
        daily = load(s, "1d")
        a = atr(daily, 14)
        a.index = a.index.tz_convert("America/New_York").normalize().tz_localize(None)
        d["atr"] = a.shift(1).reindex(d.index)
        d["dollar_vol"] = (daily["close"] * daily["volume"]).rolling(20).mean().shift(1).set_axis(a.index).reindex(d.index)
        # 20-day trend
        dc = pd.Series(daily["close"].values, index=a.index)
        d["mom20"] = (dc / dc.shift(20) - 1).shift(1).reindex(d.index)
        rows.append(d)
    p = pd.concat(rows).reset_index().rename(columns={"index": "day"})
    m = p[p.sym == "SPY"].set_index("day")
    for c in ["gap", "r_early", "r_pc", "rest"]:
        p["mkt_" + c] = p["day"].map(m[c])
        p["x_" + c] = p[c] - p["mkt_" + c]
    return p


if __name__ == "__main__":
    tf = sys.argv[1] if len(sys.argv) > 1 else "30m"
    slot = sys.argv[2] if len(sys.argv) > 2 else "10:00"
    p = build(tf, slot)
    p.to_parquet(RESULTS_DIR / f"panel_{tf}_{slot.replace(':', '')}.parquet")
    print(len(p), p.day.min(), p.day.max())
