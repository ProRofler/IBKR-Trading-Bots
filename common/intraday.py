"""Intraday bars for day trading research, downloaded month by month into data/intraday/.

Two kinds per symbol:
- "5m": 5-minute bars, regular hours only (9:30-16:00 ET).
- "30m_ext": 30-minute bars with pre-market (from 4:00 ET) and after-hours (to 20:00 ET).

IBKR serves roughly 300 bars a second, whatever the number of parallel requests, so a symbol-year
of both kinds takes about 1.5 minutes. Months are fetched newest first for all symbols, so an
interrupted run still leaves a complete recent period.

Usage:
    python -m common.intraday                       # DAYTRADE_SYMBOLS, back to START
    python -m common.intraday --start 2024-01 --symbols SPY QQQ
Files: data/intraday/<kind>/<SYMBOL>/<YYYY-MM>.parquet. Finished months are skipped on later runs;
the current month is always downloaded again.
"""
import argparse
import time
from datetime import datetime, timedelta, timezone

import pandas as pd
from ib_async import Stock, util

from common.connection import connect
from common.data import DATA_DIR, NY, clean, load
from common.universe import DAYTRADE_SYMBOLS, HISTORY_START

INTRADAY_DIR = DATA_DIR / "intraday"
START = "2022-01"
# kind -> (IBKR bar size, regular hours only, bar length)
KINDS = {"5m": ("5 mins", True, timedelta(minutes=5)), "30m_ext": ("30 mins", False, timedelta(minutes=30))}


def month_path(kind: str, symbol: str, month: str):
    return INTRADAY_DIR / kind / symbol / f"{month}.parquet"


def load_intraday(symbol: str, kind: str = "5m") -> pd.DataFrame:
    """Cached bars indexed by bar end time (UTC). Columns: open, high, low, close, volume."""
    files = sorted((INTRADAY_DIR / kind / symbol).glob("*.parquet"))
    frames = [f for f in (pd.read_parquet(p) for p in files) if len(f)]
    if not frames:
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
    df = clean(pd.concat(frames).sort_index())
    if symbol in HISTORY_START:
        df = df[df.index >= pd.Timestamp(HISTORY_START[symbol], tz="UTC")]
    return df


def months(start: str) -> list[str]:
    """Months from the current one back to start, newest first, as YYYY-MM."""
    now = pd.Timestamp.now(tz=NY)
    return [p.strftime("%Y-%m") for p in pd.period_range(start, now.strftime("%Y-%m"), freq="M")[::-1]]


def download_month(ib, contract, kind: str, month: str) -> pd.DataFrame | None:
    """Bars whose start falls in the month. None when the request failed (retry on the next run)."""
    bar_size, rth, length = KINDS[kind]
    first = pd.Timestamp(f"{month}-01", tz=NY)
    nxt = first + pd.offsets.MonthBegin()
    current = nxt > pd.Timestamp.now(tz=NY)
    end = "" if current else nxt.strftime("%Y%m%d %H:%M:%S US/Eastern")
    # IBKR counts "D" durations in trading days
    days = int((min(nxt, pd.Timestamp.now(tz=NY)) - first).days * 5 / 7) + 3
    bars = ib.reqHistoricalData(
        contract, endDateTime=end, durationStr=f"{days} D", barSizeSetting=bar_size,
        whatToShow="TRADES", useRTH=rth, formatDate=2, timeout=600,
    )
    if not bars:
        return None
    df = util.df(bars)
    start = pd.to_datetime(df["date"], utc=True)
    keep = (start >= first) & (start < nxt)
    out = df.loc[keep, ["open", "high", "low", "close", "volume"]].astype(float)
    out.index = pd.DatetimeIndex(start[keep] + length, name="end")
    out = out[~out.index.duplicated(keep="last")].sort_index()
    if current:
        # Drop the bar still in progress
        out = out[out.index <= pd.Timestamp.now(tz="UTC")]
    return out


def traded_in(daily: pd.DataFrame, month: str) -> bool:
    """Whether the daily cache has bars in the month (otherwise an empty answer is final)."""
    idx = daily.index.tz_convert(NY)
    return bool(((idx >= pd.Timestamp(f"{month}-01", tz=NY)) &
                 (idx < pd.Timestamp(f"{month}-01", tz=NY) + pd.offsets.MonthBegin())).any())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbols", nargs="*", default=DAYTRADE_SYMBOLS)
    parser.add_argument("--kinds", nargs="*", default=list(KINDS))
    parser.add_argument("--start", default=START)
    args = parser.parse_args()

    ib = connect(client_id=93)
    contracts = {}
    daily = {s: load(s, "1d") for s in args.symbols}
    this_month = months(args.start)[0]
    t0, bars_done = time.time(), 0
    try:
        for month in months(args.start):
            for symbol in args.symbols:
                if not traded_in(daily[symbol], month):
                    continue
                for kind in args.kinds:
                    path = month_path(kind, symbol, month)
                    if path.exists() and month != this_month:
                        continue
                    if symbol not in contracts:
                        contracts[symbol] = Stock(symbol, "SMART", "USD")
                        ib.qualifyContracts(contracts[symbol])
                    df = download_month(ib, contracts[symbol], kind, month)
                    if df is None:
                        print(f"{month} {symbol:6} {kind:7} no data (will retry next run)", flush=True)
                        continue
                    path.parent.mkdir(parents=True, exist_ok=True)
                    df.to_parquet(path)
                    bars_done += len(df)
            rate = bars_done / max(time.time() - t0, 1)
            print(f"{month} done  {datetime.now(timezone.utc):%H:%M} UTC  {rate:.0f} bars/s", flush=True)
    finally:
        ib.disconnect()


if __name__ == "__main__":
    main()
