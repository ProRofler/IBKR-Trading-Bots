# Intraday reversal strategy (day trading)

Buy index ETFs at the open after a big down day, short ETFs at the open after a big up day, close everything at the close. Signals come from daily bars; positions never stay open overnight.

## Layout
- `STRATEGY.md`: the rules (source of truth). `params.py` mirrors its numbers.
- `RESEARCH.md`: every day-trading idea tested to get here, with results (newest at the top).
- `signals.py`: the signal from daily bars. `backtest.py`: portfolio backtest, variants, leave-one-out.
- `research/`: exploratory scripts for all the candidate strategies (ORB, noise-area momentum, gap fade/momentum, pairs, open-to-close sorts). `research/bars.py` turns cached 30m/1h bars into day × slot grids.
- `results/`: parquet/csv outputs (git-ignored). `logs/`: printed outputs of the runs quoted in RESEARCH.md.

## Workflow (run from the project root)
- `python -m intraday_reversal.backtest` runs the default rules, variants and leave-one-out → `logs/backtest.txt` when redirected. `--quick` runs the default only.
- `bash intraday_reversal/research/run_all.sh` re-runs every research script into `logs/` (about 10 minutes; `pairs` is the slow one).

## Notes
- Intraday research used the cached 30m bars (2 years) and 1h bars (4 years). Tight-stop strategies such as a 5-minute ORB can't be tested on them: a stop inside a 30-minute bar is ambiguous. That needs 5-minute data (TWS running; see RESEARCH.md, next steps).
- Cached "1h" bars: the first bar of each day covers 9:30–10:00 but is stamped 10:30 (`common.data` adds one hour to the start). `research/bars.py` relabels it to 10:00.
- Costs: commission is per share on split-adjusted prices. Keep slippage at ≥1 bp per side: the edge is about 10 bp per trade.
