# Pre-market scanner, trend-following day trades: research log (started 2026-10-29)

**Status: abandoned by the user on 2026-10-29, before the out-of-sample test.** The rules below were
never tested on 2022-01 -> 2025-10. Intraday bars were downloaded back to 2025-08 only.

Goal from the user: a day-trading strategy built on pre-market analysis. Before the open, find the
candidates for the session; trade with the trend; flat at the close. Not aggressive, consistent.

## Data
- 156 symbols: the 96 in `common.universe.ALL_SYMBOLS` plus 60 liquid names in `DAYTRADE_EXTRA`,
  which deliberately include stocks that fell or went sideways since 2022 (INTC, PYPL, NKE, BA,
  RIVN, MRNA...). Survivorship bias remains: every symbol still trades today.
- 5-minute regular-hours bars and 30-minute bars with pre-market (`python -m common.intraday`),
  downloaded newest first back to 2022-01. IBKR serves about 190 bars/s, about 30 minutes per month
  for all symbols.
- Pre-market features use only data up to 9:30: the last pre-market price (close of the 9:00-9:30
  bar), pre-market volume 4:00-9:30, daily trend and ATR as of yesterday's close.

## Method
- Entry/exit rules (`simulate.py`): opening-range breakout with 5, 15 or 30-minute ranges, stop at
  the other side of the range (or a fraction of ATR), exit at the official close (MOC). Entry and
  stop inside one 5-minute bar count as a stop (conservative).
- Costs: $0.005/share plus 2 bp slippage per side.
- R = distance from entry to stop. Portfolio: 0.25% equity risked per trade, max 25% per position,
  max 100% gross.
- **Exploration vs out-of-sample.** Rules are chosen on 2025-11 -> 2026-10 (the first 12 months
  downloaded). Older months (2022-01 -> 2025-10) are not looked at until the rules below are
  frozen, then used once as the out-of-sample test.

## Findings on the exploration period (2025-11 -> 2026-10)

0. Daily proxy, 20 years (`research/daily_proxy.py`, log 00): open->close return in the direction of
   the daily trend is about zero for stocks; gaps in the trend's direction mostly fade. Only
   uptrend stocks gapping up > 1 ATR continued (+23 to +30 bp in 3 of 4 eras).
1. Scanner variants (`research/scanner.py`, log 01): trend-filtered gap scans with 2x pre-market
   volume give ~0 R after costs over 12 months. A first look at 6 months (May-Oct 2026) had shown
   +0.3 R for the strictest scans; November 2025 - April 2026 erased it.
2. Factor tables (`research/factors.py`, log 02), 15-min ORB, all stock-days: -0.04 R per trade on
   average. Only extreme pre-market activity is positive: relative volume > 8x (+0.08 R, t 2.3),
   gap > 2 ATR (+0.12 R, t 1.6). Trade direction relative to the daily trend barely matters.
3. Stocks in play (`research/in_play.py`, log 03): trade in the gap's direction, top 1-5 names by
   pre-market relative volume or turnover.
   - Tight ATR stops (0.25 ATR) lose heavily: -0.2 to -0.5 R. 5-minute bars can't resolve them, and
     they are inside normal noise.
   - 15-minute ORB is the best entry. Gap >= 1 ATR, top 3 by pre-market relative volume, any
     trend: +0.12 R, t 2.2, positive in 5 of 5 quarters.
   - **Against the daily trend works, with it does not.** Same scan, gap against the trend: +0.22 R,
     t 2.5, 5/5 quarters; with the trend: -0.07 R. Both long and short sides (log 04). A plausible
     reason: a big gap against the trend is news that changes the story (earnings, guidance), and
     the new move continues through the day; a gap in the trend's direction on an extended stock
     tends to fade.

## Rules frozen for the out-of-sample test
All: stocks only, price >= $5, gap measured from yesterday's close to the last pre-market price,
in ATR(14); trade in the gap's direction; 15-minute opening-range breakout, stop at the other side
of the range, exit at the close.

| Name | Gap | Rank by | Top | Daily trend |
|---|---|---|---|---|
| A (in play) | >= 1 ATR | pre-market relative volume | 3 | any |
| B (news against trend) | >= 1 ATR | pre-market relative volume | 3 | gap against the trend |
| C (user's hypothesis) | >= 1 ATR | pre-market relative volume | 3 | gap with the trend |
| D (turnover rank) | >= 1 ATR | pre-market $ volume / daily $ volume | 3 | any |
