# EMA touch strategy

Buy the 4th touch of an EMA that price has touched and held 3 times (10/20/50/100/200 EMA, on 30m/1h/4h/1d/1w).

## Layout
- `STRATEGY.md`: the strategy spec (source of truth for rules). `bot/params.py` mirrors its numbers.
- `bot/`: touch signals, index filter, entry/sizing rules, parameters (shared by the backtest and the future live bot).
- `backtest/`: `run.py` per-trade simulation, `portfolio.py` portfolio replay, `exits.py` exit variants, `robust.py` repeated portfolio replays.
- `results/`: backtest outputs (parquet/csv). `logs/`: printed outputs of earlier runs.
- `BACKTEST_RESULTS.md`: findings so far (newest run at the top).

## Backtest workflow (run from the project root)
1. Data comes from the shared cache (`python -m common.data`, see the root CLAUDE.md).
2. `python -m ema_touch.backtest.run` simulates every signal with the current `bot/params.py` defaults → `results/default_trades.parquet`. Flags (e.g. `--reset`, `--lookback 250`) save under another name.
3. `python -m ema_touch.backtest.portfolio [--trades NAME]` replays trades through the portfolio rules and compares the default against strict / no-leverage / no-margin variants.
4. `python -m ema_touch.backtest.exits` compares exit variants on the same signals.
5. `python -m ema_touch.backtest.robust` replays portfolio setups 20 times each (shuffled same-time order, random symbol subsets). Use it to compare portfolio setups: a single `portfolio` run swings by ±10 points of CAGR from signal order alone.
