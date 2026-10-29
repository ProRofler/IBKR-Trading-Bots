"""Download historical bars from IBKR and cache them as parquet files in data/.

Usage:
    python -m common.data              # all symbols, all timeframes (skips cached files)
    python -m common.data --refresh    # re-download everything
"""
import argparse
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
from ib_async import Stock, util

from common.connection import connect
from common.universe import ALL_SYMBOLS, HISTORY_START

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
NY = ZoneInfo("America/New_York")

# timeframe -> (IBKR bar size, duration per request, number of requests going back in time)
REQUESTS = {
    "30m": ("30 mins", "1 Y", 2),
    "1h": ("1 hour", "2 Y", 2),
    "4h": ("4 hours", "5 Y", 1),
    "1d": ("1 day", "20 Y", 1),
    "1w": ("1 week", "20 Y", 1),
}
BAR_LENGTH = {"30m": timedelta(minutes=30), "1h": timedelta(hours=1), "4h": timedelta(hours=4)}


def cache_path(symbol: str, tf: str) -> Path:
    return DATA_DIR / f"{symbol}_{tf}.parquet"


def load(symbol: str, tf: str) -> pd.DataFrame:
    """Cached bars indexed by bar end time (UTC). Columns: open, high, low, close, volume."""
    df = clean(pd.read_parquet(cache_path(symbol, tf)))
    if symbol in HISTORY_START:
        df = df[df.index >= pd.Timestamp(HISTORY_START[symbol], tz="UTC")]
    return df


def clean(df: pd.DataFrame, max_wick: float = 10.0) -> pd.DataFrame:
    """Drop filler bars and clip bad prints.

    IBKR fills trading halts with zero-volume bars at a frozen price (e.g. NBIS 2022-2024); nothing
    traded, so they are dropped. A wick longer than max_wick x the typical bar range is cut back to
    the body: older history has occasional broken ticks (e.g. AMZN 2007-10-04 low 0.95 vs ~4.60).
    """
    df = df[~((df["volume"] <= 0) & (df["high"] == df["low"]))].copy()
    body_low = df[["open", "close"]].min(axis=1)
    body_high = df[["open", "close"]].max(axis=1)
    typical = (df["high"] - df["low"]).rolling(20, min_periods=5, center=True).median()
    bad_low = body_low - df["low"] > max_wick * typical
    bad_high = df["high"] - body_high > max_wick * typical
    df.loc[bad_low, "low"] = body_low[bad_low]
    df.loc[bad_high, "high"] = body_high[bad_high]
    return df


def _session_close(day) -> datetime:
    return datetime.combine(day, time(16, 0), NY).astimezone(timezone.utc)


def _normalize(df: pd.DataFrame, tf: str) -> pd.DataFrame:
    """Add the time each bar completed, so signals never use a bar before it closed."""
    if tf in BAR_LENGTH:
        start = pd.to_datetime(df["date"], utc=True)
        close_of_day = start.map(lambda ts: _session_close(ts.tz_convert(NY).date()))
        end = pd.concat([start + BAR_LENGTH[tf], close_of_day], axis=1).min(axis=1)
    else:
        # Daily and weekly bars are labeled with their last trading day
        end = df["date"].map(_session_close)
    out = df[["open", "high", "low", "close", "volume"]].copy()
    out.index = pd.DatetimeIndex(end, name="end")
    return out[~out.index.duplicated(keep="last")].sort_index()


def download(ib, symbol: str, tf: str) -> pd.DataFrame:
    contract = Stock(symbol, "SMART", "USD")
    ib.qualifyContracts(contract)
    bar_size, duration, chunks = REQUESTS[tf]
    frames, end_dt = [], ""
    for _ in range(chunks):
        bars = ib.reqHistoricalData(
            contract, endDateTime=end_dt, durationStr=duration, barSizeSetting=bar_size,
            whatToShow="TRADES", useRTH=True, formatDate=2, timeout=180,
        )
        if not bars:
            break
        frames.append(util.df(bars))
        first = bars[0].date
        end_dt = first if isinstance(first, datetime) else datetime.combine(first, time(0), timezone.utc)
    if not frames:
        return pd.DataFrame()
    df = _normalize(pd.concat(frames, ignore_index=True), tf)
    # Drop the bar still in progress
    return df[df.index <= pd.Timestamp.now(tz="UTC")]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--symbols", nargs="*", default=ALL_SYMBOLS)
    parser.add_argument("--timeframes", nargs="*", default=list(REQUESTS))
    args = parser.parse_args()

    DATA_DIR.mkdir(exist_ok=True)
    ib = connect(client_id=90)
    try:
        for symbol in args.symbols:
            for tf in args.timeframes:
                path = cache_path(symbol, tf)
                if path.exists() and not args.refresh:
                    continue
                df = download(ib, symbol, tf)
                if df.empty:
                    print(f"{symbol:6} {tf:4} no data")
                    continue
                df.to_parquet(path)
                print(f"{symbol:6} {tf:4} {len(df):6} bars  {df.index[0]:%Y-%m-%d} -> {df.index[-1]:%Y-%m-%d}")
    finally:
        ib.disconnect()


if __name__ == "__main__":
    main()
