# TWS trading bots

Python trading bots for Interactive Brokers TWS, using `ib_async` (maintained fork of ib_insync). Several strategies share one IBKR connection setup and one cache of historical bars.

## Setup
- Python venv at `.venv`. Run everything from this folder as modules: `.\.venv\Scripts\python.exe -m <package>.<module>` (e.g. `-m common.data`), so the shared packages import.
- TWS paper trading on `127.0.0.1:7497` (account `DUR998420`). Settings in `common/config.py`, overridable via `.env`.
- Always connect through `common.connection.connect()`: it refuses non-paper accounts while `PAPER_ONLY=1`.
- Use a distinct `clientId` per concurrently running script (TWS rejects duplicates). Taken: 90 (`common.data`), 91 (`common.reference`).

## Layout
- `common/`: shared by all strategies.
  - `data.py`: downloads IBKR bars and caches them in `data/`. `load(symbol, tf)` returns cleaned bars indexed by bar end time (UTC), columns open/high/low/close/volume.
  - `reference.py`: sectors and verified leveraged ETFs → `data/reference.json` (`load_reference()`).
  - `universe.py`: the symbols in the cache (96: indexes, large caps, trend stocks, sector ETFs), `HISTORY_START`, leveraged ETF candidates.
  - `indicators.py`: SMA, EMA, ATR, RSI.
  - `config.py`, `connection.py`: TWS settings and the paper-only connect.
- `data/`: cached bars, `<SYMBOL>_<tf>.parquet` for 30m, 1h, 4h, 1d, 1w. History requested (`common.data.REQUESTS`): 1d/1w 20 years, 4h 5 years, 1h 4 years, 30m 2 years; younger symbols have less.
- `ema_touch/`: the EMA touch strategy (spec, backtests, results). See `ema_touch/CLAUDE.md`.
- `intraday_reversal/`, `premarket_trend/`: day-trading strategies and research, **abandoned 2026-10-29**. Kept for reference only; see their `RESEARCH.md` for what was tested.
- `tools/`: `smoke_test.py` (read-only: account, positions, quote, bars) and `test_order.py` (places a 1-share AAPL buy limit at 50% of last close, then cancels it). Run with `-m tools.smoke_test`.

## Adding a strategy
- Create a new package next to `ema_touch/` (with `__init__.py`), holding its own spec, code, `results/` and `CLAUDE.md`.
- Read bars with `from common.data import load`; don't copy the data. Indicators come from `common.indicators`.
- New symbols: add them to `common/universe.py`, then run `python -m common.data` (downloads only what isn't cached; `--symbols X Y` for specific ones).
- Keep strategy-specific code out of `common/`, and don't change `common/` behaviour without checking that `ema_touch` still gives the same results.

## Data
- `python -m common.data` downloads missing bars; `--refresh` re-downloads everything (slow).
- `python -m common.reference` refreshes sectors and leveraged ETFs.
- IBKR history quirks handled in `common/data.py`: zero-volume filler bars during trading halts are dropped, and `universe.HISTORY_START` cuts pre-SPAC-merger / pre-relisting history. Check new symbols for both.
- Error 162 "HMDS query returned no data" for young symbols on long durations is harmless; what exists is saved.
- Known issue, not fixed: IBKR's first hourly bar of the day is 9:30–10:00, but `_normalize` stamps it 10:30 (start + 1 hour). Signals on it come 30 minutes late, never early. Fixing it would change `ema_touch` 1h results.
- Halts can leave intraday bars at odd times (e.g. 12:05). Code that expects fixed bar times should drop them.

## IBKR notes
- No paid market data subscription: use `ib.reqMarketDataType(3)` (delayed, ~15 min lag). Historical bars work.
- Wait for an order to reach `Submitted`/`PreSubmitted` before cancelling: a cancel sent while still `PendingSubmit` can be lost and leave the order live (seen on the first order of a TWS session).
- Error 202 "Order Canceled" is the normal confirmation of a cancel, not a failure.
- Never place orders against a live account. Ask the user before changing `PAPER_ONLY` or the port.
