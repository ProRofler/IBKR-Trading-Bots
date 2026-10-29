#!/usr/bin/env bash
# Re-run every research script in order and save the printed output to intraday_reversal/logs/.
# Run from the project root: bash intraday_reversal/research/run_all.sh
set -e
PY=.venv/Scripts/python.exe
[ -x "$PY" ] || PY=.venv/bin/python
LOG=intraday_reversal/logs
mkdir -p "$LOG"
run() { name=$1; shift; echo "== $name"; "$PY" -m "intraday_reversal.research.$@" > "$LOG/$name.txt" 2>&1; }

run intraday_panel_30m intraday_panel 30m 10:00
run intraday_panel_1h intraday_panel 1h 10:00
run 01_noise_momentum_30m noise_momentum 30m
run 01_noise_momentum_1h noise_momentum 1h
run 02_early_signals_30m early_signals 30m
run 02_early_signals_1h early_signals 1h
run 03_time_of_day_30m time_of_day 30m
run 03_time_of_day_1h time_of_day 1h
run 04_orb_30m orb 30m
run 04_orb_1h orb 1h
run 05_gap_fade_30m gap_fade 30m
run 05_gap_fade_1h gap_fade 1h
run 06_pairs_30m pairs 30m
run 07_gap_momentum_30m gap_momentum 30m
run 07_gap_momentum_1h gap_momentum 1h
run daily_panel daily_panel
run 08_oc_cross_section oc_cross_section
run 09_oc_index oc_index
run 10_oc_groups oc_groups
run 11_reversal_variants reversal_variants
run 12_reversal_combo reversal_combo
