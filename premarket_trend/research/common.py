"""Entry/exit rules tested in the research, and a cache of their trade tables in results/."""
from pathlib import Path

import pandas as pd

from premarket_trend.trades import all_trades

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"

RULES = {
    "open": dict(entry="open", stop="none"),
    "open_atr50": dict(entry="open", stop="atr", stop_atr=0.5),
    "orb5_or": dict(entry="orb", or_bars=1, stop="or"),
    "orb5_atr10": dict(entry="orb", or_bars=1, stop="atr", stop_atr=0.1),
    "orb5_atr25": dict(entry="orb", or_bars=1, stop="atr", stop_atr=0.25),
    "orb15_or": dict(entry="orb", or_bars=3, stop="or"),
    "orb30_or": dict(entry="orb", or_bars=6, stop="or"),
    "orb15_or_trail": dict(entry="orb", or_bars=3, stop="or", trail_atr=0.75),
}


def load_trades(rule: str, start=None, refresh=False) -> pd.DataFrame:
    """Trade table for a rule; cached until refresh (rerun with refresh after new data arrives)."""
    RESULTS_DIR.mkdir(exist_ok=True)
    path = RESULTS_DIR / f"trades_{rule}.parquet"
    if path.exists() and not refresh:
        t = pd.read_parquet(path)
    else:
        t = all_trades(**RULES[rule])
        t.to_parquet(path)
    return t[t["day"] >= start] if start else t
