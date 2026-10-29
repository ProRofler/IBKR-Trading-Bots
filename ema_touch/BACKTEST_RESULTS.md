# Backtest results (2026-10-28)

## Run 11: robustness test (each portfolio replayed 20 times) and the recommended setup

**Why:** a single portfolio run is one path. Signals that arrive at the same time (all daily bars close at 16:00) were taken in whatever order the data happened to be in, and that decides which symbols get the capital. The same trades and rules gave 25.7%, 20.6% or 14.3% CAGR depending only on that order. From now on, compare portfolio setups with `python -m ema_touch.backtest.robust`. It replays each setup 20 times with same-time signals in a random order (or on a random 75% of the symbols) and reports the range. Results: `results/robust_runs_round1.csv`, `robust_runs_round2.csv`.

**Portfolio, 20 replays each: CAGR median (10th–90th percentile) / median max DD / median Sharpe**

| Setup | 2007–2026 | 2022–2026 | Last 2 years |
|---|---|---|---|
| Run 8 exits, all 96 | 14.6% (13–19) / −37% / 0.76 | 24.9% (17–36) / −29% | 22.3% (9–40) / −26% |
| Run 10 exits, all 96 | 20.8% (16–24) / −37% / 0.93 | 37.6% (29–48) / −29% | 31.2% (16–50) / −29% |
| Run 8 exits, original 34 | 9.9% (7–13) / −30% / 0.67 | 13.6% / −20% | 26.4% / −17% |
| Run 10 exits, original 34 | 13.6% (11–15) / −40% / 0.77 | 19.2% / −22% | 18.4% / −17% |
| Run 10, random 75% of symbols | 18.6% (14–21) / −37% / 0.87 | 37.4% / −31% | 21.1% / −30% |
| Run 10 + trend screen (above rising 200d EMA) | 13.2% (11–16) / −38% / 0.68 | 26.2% / −35% | 25.6% / −34% |
| Run 10 + trend screen (above 200d EMA) | 14.9% / −39% / 0.73 | 31.0% / −34% | 30.6% / −35% |
| Run 10, take dropped 10 EMA entries | 20.4% / −39% / 0.92 | 32.1% / −29% | 31.3% / −27% |
| Run 10, drop 10 and 20 EMA entries | 16.1% / −35% / 0.82 | 27.3% / −31% | 16.7% / −29% |
| **Run 10, strongest signals first** | **21.8% (20–24)** / −38% / **0.98** | **40.3% (33–45)** / −33% / 1.29 | **37.9% (35–40)** / −25% / 1.25 |
| ↳ same, original 34 | 15.4% (15–17) / −39% / 0.84 | 24.2% / −24% | 30.4% / −14% |
| ↳ same, random 75% of symbols | 19.0% (17–23) / −39% / 0.89 | 38.6% / −32% | 29.0% / −26% |
| ↳ same, **no leveraged ETFs** (plain margin) | 19.5% (18–21) / **−33%** / 0.98 | 36.2% / −31% / 1.29 | 32.4% / −23% |
| ↳ same, no margin (max 100% invested) | 12.7% (12–14) / **−20%** / **1.01** | 16.0% / −19% | 14.8% / −15% |
| Strict adding rule | 3.2% / −13% / 0.62 | 3.5% | 4.3% |
| SPY buy & hold | 8.9% / −57% / 0.54 | 10.4% / −25% / 0.66 | 16.2% / −19% / 1.00 |

"Strongest signals first" (`Params.signal_priority = "quality"`, now the default) takes same-time signals in order of timeframe (1w first), then entry EMA (200 first). Per trade, the edge rises with both: 1w averages 0.28R, and the 200 EMA is the best entry on 4 of 5 timeframes.

**Findings**
- **Run 10 exits beat run 8** in 5 of 6 universe/window medians (2007–: 20.8% vs 14.6%). The exception is original 34 over the last 2 years, where the range is very wide. Kept.
- **Strongest signals first** raises every median and narrows the range a lot (last 2 years: 10th percentile 16% → 35%). Adopted.
- **All 96 symbols beat the original 34** in every window, and random 75% subsets keep most of it (19.0% vs 21.8%). The result does not hang on a few names. The hindsight caveat stays: every symbol was picked knowing it trended.
- **The trend screen hurts** in every window, and per trade too. On every timeframe, signals taken while the stock was below its 200-day EMA did better (1w 0.47R vs 0.22R). In a list of stocks picked as long-term winners, buying their dips worked by construction. So this test cannot judge the screen fairly: its job is to drop stocks that stop trending, and this list has none.
- **Dropping the 10/20 EMA entries hurts:** fewer trades for the buffer rule to work with. All five EMAs stay.
- **Leverage is a risk dial, not an edge.** Sharpe is about the same with leveraged ETFs (0.98), plain margin (0.98) and no margin (1.01). More leverage gives proportionally more return and drawdown. Leveraged ETFs add about 2 points of CAGR for about 5 points of extra drawdown, and that 2 points is the least trustworthy part of the simulation: synthetic 2× returns, no decay, and assumed availability before most of these funds existed. Neither variant charges margin interest, which flatters plain margin. **Kept** (user decision 2026-10-29): over the last 2 years they also narrowed the range (10th percentile 35% vs 15% without them).
- **The edge holds across eras** for 1d and 1w (1d 0.02–0.12R, 1w 0.12–0.34R per trade in each 5-year period since 2007). 30m/1h/4h only have 2–5 years of history.

## Run 10: best tested exit per timeframe (now the default)

Exits per timeframe (`Params.tf_overrides`, `ladder_min_period`):
- **30m:** sell the whole position at 4R (from run 9).
- **1h:** half at 3R + trail (unchanged).
- **4h / 1d / 1w:** EMA ladder down to the **20 EMA** (was 10), wiggle 1 ATR.

The ladder settings were compared again on the 96-symbol setup (`python -m ema_touch.backtest.exits`, round 6), avg R cap 10:

| Ladder | 4h | 1d | 1w | Total R 4h–1w |
|---|---|---|---|---|
| Lowest rung 10 EMA, wiggle 1 ATR (previous) | 0.084 | 0.072 | 0.251 | 5,723 |
| Lowest rung 10 EMA, wiggle 0.5 ATR | 0.067 | 0.059 | 0.205 | 4,484 |
| **Lowest rung 20 EMA, wiggle 1 ATR** | **0.088** | **0.072** | **0.281** | **6,558** |
| Lowest rung 20 EMA, wiggle 0.5 ATR | 0.086 | 0.068 | 0.230 | 5,684 |

**Per trade, all timeframes (entry rules on):** avg R cap 10 0.109 → **0.114**, total R 9,751 → **10,380**, profit factor 1.35 → 1.36. By timeframe: 30m 0.097, 1h 0.195, 4h 0.088, 1d 0.072, 1w 0.281.

**Portfolio, CAGR / max DD (run 8 exits → run 10 exits)**

| Window | Universe | Default rules | Strict adding rule |
|---|---|---|---|
| 2007– | All 96 | 19.8% / −38% → **20.6% / −37%** | 3.6% → **4.4%** |
| | Original 34 | 15.2% / −28% → 15.6% / −41% | 2.5% → **4.9%** |
| 2022– | All 96 | 22.7% / −32% → **42.3% / −32%** | 3.5% → **5.8%** |
| | Original 34 | 26.0% / −18% → 23.3% / −26% | 3.3% → **7.7%** |
| Last 2 years | All 96 | 36.5% / −28% → 35.7% / −30% | 5.3% → **9.1%** |
| | Original 34 | 38.4% / −18% → 26.2% / −20% | 4.1% → **8.6%** |

- Per trade, the new exits are better on every timeframe they change and the same on 1h.
- With the strict adding rule, which holds few positions and so depends little on trade order, the new exits improve CAGR in all six cases.
- With the default rules the result is mixed (+20 points in one case, −12 in another). That is the path dependence seen in run 9: different exit times change which later trades get the capital.

## Run 9: 30m/1h sell the whole position at the target vs half at 3R + trail

96 symbols, run 8 rules. Only the 30m/1h exit changes; 4h/1d/1w keep the EMA ladder. Run with `python -m ema_touch.backtest.exits` (round 5).

**What the trailed half earns now.** 22% of 30m/1h trades reach 3R and sell half. In 60% of those the second half then exits below 3R. Its median contribution is +1.0R, against +1.5R if it had been sold at the target. Its mean is **+2.15R**, because a few trades run to 20–45R.

**Per trade (avg R cap 10, after costs)**

| 30m/1h exit | 30m | 1h | Total R (cap 10), all TFs |
|---|---|---|---|
| **Half at 3R + trail (current)** | 0.081 | **0.195** | 7,394 |
| Whole at 2R | 0.032 | 0.114 | 6,499 |
| Whole at 3R | 0.067 | 0.159 | 7,362 |
| Whole at 4R | **0.097** | 0.171 | 7,720 |

**Portfolio: P&L of the 30m/1h positions themselves ($M)**

| Universe, window | Half 3R + trail | Whole 2R | Whole 3R | Whole 4R |
|---|---|---|---|---|
| All 96, 2007– | **9.49** | 4.53 | 1.23 | 3.34 |
| All 96, 2022– | **0.71** | 0.55 | 0.37 | 0.48 |
| Original 34, 2007– | **5.30** | 1.43 | 2.09 | 3.88 |
| Original 34, 2022– | **0.98** | 0.29 | 0.53 | 0.64 |

- **Decision: keep half at 3R + trail.** It earns the most from 30m/1h positions in every universe and window. The runners pay for the many times the second half gives back.
- Whole at 4R is the closest alternative: better on 30m alone, worse on 1h.
- **The portfolio totals are path-dependent and not a fair comparison here.** Whole-portfolio CAGR swung by ±20 points between variants:
  - All 96, 2022–: 22.7% → 43.8% (whole at 3R).
  - Original 34, last 2 years: 38.4% → 9.0% (whole at 3R).
  - 30m/1h positions are only about 4–8% of positions. Changing when they free capital changes which later 4h/1d/1w trades get taken first-come-first-served, and that compounds over years. Treat any single portfolio CAGR as one path, not a precise figure.

## Run 8: bigger universe (96 symbols)

Same rules as run 7. Added 49 stocks that have trended since 2022 (MU, APP, RKLB, MNST, HOOD, CTAS, …) and 13 sector/commodity ETFs (SMH, GLD, SLV, MAGS, DRAM, IBIT, …); see `common/universe.py`. 18 more 2× leveraged ETFs, all verified in IBKR.

Data fixes in this run (`common/data.py`, `common.universe.HISTORY_START`):
- Zero-volume bars with no price range are dropped. IBKR fills trading halts with them, e.g. NBIS 2022–2024 at a frozen 18.94. A stop placed on those bars is a fraction of a cent wide, which turned one loss into −397R.
- Pre-merger SPAC history (ASTS, VRT, RKLB, SOFI: flat near $10) and NBIS's history as Yandex are ignored.
- The original 34 symbols are almost unaffected (portfolio CAGR 15.4% → 15.2%).

**Per trade (entry rules on, avg R cap 10)**

| Group | Trades | Win rate | Avg R | Total R |
|---|---|---|---|---|
| Indexes | 2,399 | 30% | 0.07 | 223 |
| Original 31 stocks | 23,694 | 22% | 0.10 | 3,112 |
| Trend stocks | 33,689 | 20% | 0.11 | 4,976 |
| ETFs | 8,006 | 26% | **0.14** | 1,441 |
| **All 96** | 67,788 | 22% | **0.109** | 9,751 |

By timeframe: 30m 0.08, 1h 0.20, 4h 0.08, 1d 0.07, 1w 0.25. The new symbols are as good per trade as the original ones, and the ETFs are better. Best new symbols by total R: SLV, CTAS, MU, APP, GLD, SHOP, CAT. Worst: UBER, MSTR, CRWV, IBIT, and DRAM (launched April 2026, only 74 trades).

**Portfolio (buffer 2× + adding to winners)**

| Window | Universe | CAGR | Max DD | Sharpe | Avg invested |
|---|---|---|---|---|---|
| 2007–2026 | All 96 | **19.8%** | −38% | **0.96** | 93% |
| | Original 34 | 15.2% | −28% | 0.90 | 80% |
| 2022–2026 | All 96 | 22.7% | −32% | 0.87 | 105% |
| | Original 34 | **26.0%** | **−18%** | **1.10** | 115% |
| Last 2 years | All 96 | 36.5% | −28% | 1.28 | 94% |
| | Original 34 | **38.4%** | **−18%** | **1.46** | 114% |
| | SPY buy & hold, 2007 / 2022 / 2y | 8.9% / 10.4% / 16.2% | −57% / −25% / −19% | 0.54 / 0.66 / 1.00 | |

Without leveraged ETFs (all 96): 15.3% (2007), 23.0% (2022, Sharpe 1.02, −25%), 20.7% (2 years). Without margin: 10.4%, 12.2%, 17.5%.

- **More symbols raised the 20-year return but not the recent one.** The margin cap binds constantly: 34,000 entries were skipped for margin. Positions are taken first-come-first-served, so more symbols means capital is spread over more names and fewer adds go to the winners (1,703 adds vs 2,779 with the original list).
- **The drawdowns come from the high-momentum names moving together.**
  - 2021-11 → 2023-01 (−38%): MSTR, CAT, APP, KLAC, PANW, MELI and GDX losses.
  - June → October 2026 (−32%, still open on the last day of data): APP −57%, CRWV −52%, VRT −42% and NBIS −41% from their June peaks, while SPY is −1%. Over the same months the original list is −12%.
- The trend stocks earned the most overall ($14.6M over 20 years) but also lost the most in 2022 (−$1.2M).
- **Hindsight bias is bigger here than in run 7.** The new stocks were picked because they trended well up to 2026, and the 2022+ window is the period they were picked for.

## Run 7: breaks no longer reset the touch count

Same setup as run 6, but a close below the break level doesn't erase past touches; they only age out of the lookback window. Run with `python -m ema_touch.backtest.run --no-reset --lookback 500`.

**Per trade (entry rules on, avg R cap 10)**

| Signal rule | Trades | 30m | 1h | 4h | 1d | 1w | Overall | Total R |
|---|---|---|---|---|---|---|---|---|
| Reset on break, last 100 bars (run 6) | 7,417 | 0.22 | 0.09 | −0.04 | 0.07 | 0.15 | 0.072 | 722 |
| No reset, last 100 bars | 18,006 | 0.07 | 0.14 | 0.04 | 0.06 | 0.19 | 0.076 | 1,880 |
| No reset, last 250 bars | 24,740 | 0.07 | 0.18 | 0.05 | 0.07 | 0.20 | 0.089 | 2,971 |
| **No reset, last 500 bars** | 26,094 | 0.08 | 0.20 | 0.06 | 0.07 | 0.20 | **0.095** | **3,334** |
| No reset, 250 bars, EMA held ≥ 60% | 23,108 | 0.06 | 0.16 | 0.05 | 0.06 | 0.20 | 0.083 | 2,677 |

**Portfolio, 2007–2026 (no reset, 500 bars)**

| Adding rule | CAGR | Max DD | Sharpe | Avg invested | On margin | Leveraged |
|---|---|---|---|---|---|---|
| Strict | 2.1% | −9% | 0.54 | 13% | 0% | 0% |
| Buffer 1× + adding to winners | 11.2% | −22% | 0.79 | 62% | 70% | 27% |
| **Buffer 2× + adding to winners** | **15.4%** | −26% | **0.93** | 79% | 76% | 28% |
| ↳ same, but no leveraged ETFs (plain margin) | 11.8% | −20% | 0.88 | 68% | | 0% |
| ↳ same, but no margin (max 100% invested) | 8.2% | −15% | 0.88 | 44% | | 0% |
| SPY buy & hold | 8.9% | −57% | 0.54 | 100% | | |

Last 2 years, buffer 2× + adding: 27.6% CAGR, −18% max DD, Sharpe 1.22 (SPY 16.2%, −19%, 1.00).

- Not resetting gives 3.5× more trades at equal or better quality per trade, enough to keep the buffer rule supplied, so the account is much more invested.
- **Concentration:** the 10 best trades produce 34% of all profit, almost all TSLA, NVDA, AVGO and AMD. 2013 (+90% without leverage) is mostly TSLA's 2013 run. This is where survivorship bias in the stock list matters most.
- About a quarter of the return comes from leveraged ETFs (15.4% vs 11.8%). This is the least reliable part of the simulation: synthetic 2× returns, no decay, and assumed availability before most of these ETFs existed.

## Run 6: EMA 10–200 entries, ladder from 10 EMA, winners as buffer, adding to winners

Setup: entries on EMA 10/20/50/100/200 only. 4h/1d/1w exit with the EMA ladder (rungs down to the 10 EMA, stop 1 ATR below the EMA). 30m/1h keep 50% at 3R + trail. Run with `python -m ema_touch.backtest.run` then `python -m ema_touch.backtest.portfolio`.

**Per trade (entry rules on, avg R cap 10):** 30m 0.22, 1h 0.09, **4h −0.04**, 1d 0.07, 1w 0.15. 4h loses with this ladder.

**Portfolio, 2007–2026**

| Adding rule | CAGR | Max DD | Sharpe | Avg invested | Entries | Adds | On margin |
|---|---|---|---|---|---|---|---|
| Strict (every position at breakeven) | 1.0% | −11% | 0.30 | 12% | 993 | — | 0% |
| Strict + adding to winners | 1.2% | −9% | 0.35 | 12% | 906 | 76 | 0% |
| Buffer: open risk ≤ 1× locked profit | 1.3% | −19% | 0.26 | 22% | 2,110 | — | 5% |
| Buffer 1× + adding to winners | 2.7% | −17% | 0.40 | 26% | 2,028 | 471 | 18% |
| **Buffer: open risk ≤ 2× locked profit, + adding** | **4.3%** | −21% | **0.51** | 32% | 2,411 | 662 | 28% |
| SPY buy & hold | 8.9% | −57% | 0.54 | 100% | | | |

**Last 2 years (2024-11 → 2026-10)**

| Adding rule | CAGR | Max DD | Sharpe |
|---|---|---|---|
| Strict | 0.4% | −4% | 0.15 |
| Buffer 1× + adding | 6.3% | −5% | 0.96 |
| Buffer 2× + adding | 11.7% | −9% | **1.20** |
| SPY | 16.2% | −19% | 1.00 |

- Using winners as a buffer roughly triples the number of trades taken and lifts returns. The account is still only about a third invested on average.
- Add-on lots are only slightly profitable on their own (≈0.03R per lot vs ≈0.14R for first entries). The bigger effect is that they change which later entries the buffer allows.
- Compared with run 5 (SMA+EMA, ladder to the 20 EMA), the strict rule got worse (3.6% → 1.0%). Likely causes: dropping SMA halves the signals, and the 10 EMA rung makes 4h exits too tight.

## Run 5: EMA only, and the EMA ladder exit on 4h/1d/1w

From this run on, signals and index checks use EMA only. 30m/1h always use 50% at 3R + trail at MA − 1.5 ATR. On 4h/1d/1w the R-target exit (same as 30m/1h) is compared with the EMA ladder: the stop climbs to each shorter EMA price closes above, at EMA − wiggle × ATR, full exit, no partial. "Lowest rung" = the shortest EMA the stop may climb to.

**Per trade (avg R cap 10, after costs)**

| 4h/1d/1w exit | 4h | 1d | 1w | All TFs total R |
|---|---|---|---|---|
| R targets (current) | 0.049 | **0.131** | **0.254** | **1,292** |
| Ladder to 5 EMA, wiggle 0 | −0.022 | 0.023 | 0.060 | 533 |
| Ladder to 5 EMA, wiggle 0.25 ATR | 0.003 | 0.034 | 0.070 | 686 |
| Ladder to 5 EMA, wiggle 1 ATR | 0.002 | 0.038 | 0.144 | 778 |
| Ladder to 10 EMA, wiggle 1 ATR | −0.003 | 0.057 | 0.138 | 839 |
| Ladder to 20 EMA, wiggle 1 ATR | −0.003 | 0.059 | 0.144 | 846 |

The ladder wins more often (22–41% of trades vs 17%) and keeps more of each peak (42–54% vs 37%), but it exits the long trends early, and those earn most of the profit.

**Portfolio (strict adding rule, 2007–2026)**

| 4h/1d/1w exit | CAGR | Max drawdown | Sharpe | Positions | 2022 |
|---|---|---|---|---|---|
| R targets | 2.6% | −32% | 0.32 | 1,023 | −26% |
| Ladder to 20 EMA, wiggle 1 ATR | **3.6%** | **−12%** | **0.64** | 982 | −6% |
| SPY buy & hold | 8.9% | −57% | 0.54 | | −19% |

In the portfolio the ladder wins: it closes positions before a trend's gains are given back, so equity is much steadier (positive in 15 of 20 years). The R-target portfolio depends on a few positions held for years, which swing the equity (−26% in 2022). Both stay far below SPY because the strict adding rule keeps the account about 20% invested.

## Run 4: take-profit variants

Same signals and entry rules, different exits; after costs. Run with `python -m ema_touch.backtest.exits`. "Kept of peak" = median share of the best open profit that was actually realized, for trades that reached +2R.

| Exit rule | Avg R (cap 10) | Total R (cap 10) | Profit factor | Kept of peak |
|---|---|---|---|---|
| 50% at 2R, rest on close below MA − 1.5 ATR (old) | 0.135 | 2,278 | 1.50 | 39% |
| **50% at 3R, rest on close below MA − 1.5 ATR (new)** | **0.141** | **2,382** | **1.52** | 39% |
| 50% at 1R, same trail | 0.109 | — | 1.46 | 24% |
| 50% at 2R, rest on close below the touch band | 0.036 | — | 1.12 | 51% |
| 50% at 2R, 2 ATR chandelier trail | 0.059 | — | 1.16 | 57% |
| 50% at 2R, 3 ATR chandelier trail | 0.093 | 1,834 | 1.24 | 48% |
| 3 ATR chandelier only, no partial | 0.100 | — | 1.30 | 44% |
| Everything at 2R | 0.062 | — | 1.15 | 89% |
| Everything at 3R | 0.088 | 1,907 | 1.22 | 86% |
| Profit lock: after +1R stop to +0.25R | 0.104 | 1,879 | 1.43 | 41% |
| Profit lock: after +1.5R stop to +0.5R | 0.107 | 1,929 | 1.41 | 43% |

Where the money is (old rule):

| Peak open profit | Trades | Avg final R |
|---|---|---|
| below +0.5R | 6,745 | −0.77 |
| +0.5R to +2R | 6,240 | −0.15 to −0.34 |
| +2R to +5R | 2,206 | +0.94 to +1.26 |
| above +5R | 1,742 | **+4.63** |

The wide trail does give back about 60% of the peak on winners, but the 10% of trades that run past +5R earn most of the profit. Every tighter exit or lock tested cuts them short and loses more than it saves.

Portfolio (strict adding rule, 2007–2026): 2.3% CAGR with 2R, 2.4% with 3R. With the strict rule, exits barely matter; the adding rule limits how much the account is invested.

## Run 3: portfolio simulation (phase 2)

Changes: 30m/1h require SPY confluence; size 10% with confluence (5% if a QQQ/DIA counter-signal), else 5%. Trades are replayed through the portfolio rules: one position per symbol, the adding rule, margin up to 2× equity, and 2× leveraged ETFs above 100% invested (14 verified in IBKR). Start equity $1M. Run with `python -m ema_touch.backtest.portfolio --max-at-risk N`.

**Per trade after costs, with the new entry rules:** all timeframes profitable (avg R cap 10: 30m 0.24, 1h 0.14, 4h 0.07, 1d 0.12, 1w 0.22).

**Portfolio vs SPY buy-and-hold, 2007–2026**

| Adding rule | CAGR | Max drawdown | Sharpe | Positions | On margin | Leveraged |
|---|---|---|---|---|---|---|
| Strict: every open position at breakeven | 2.3% | −30% | 0.28 | 974 | 0% | 0% |
| Up to 3 positions below breakeven | 6.6% | −38% | 0.50 | 3,178 | 34% | 11% |
| Up to 10 positions below breakeven | 11.5% | −37% | 0.67 | 4,076 | 63% | 21% |
| SPY buy & hold | 8.9% | −57% | 0.54 | | | |

Last 2 years (all timeframes have data): strict 2.1%, up to 3 9.8%, up to 10 19.0%, SPY 16.2% per year.

- With the strict rule the account is only 22% invested on average (about 4 positions). It skipped 12,524 entries because some open position wasn't at breakeven yet; 22% of positions never reach breakeven and block everything until stopped out.
- The 2022 loss (−25% with the strict rule) came mostly from long-held weekly winners (MSFT, TSLA held for years) giving back unrealized gains.

**Extra caveats for the portfolio run:** leveraged ETFs are simulated as 2× the underlying's return and assumed to exist over the whole history (most single-stock ones launched 2022–2024); daily-reset decay and the 15-day maximum hold are not simulated.

**Exits (per trade, entry rules on)**

| Exit | Share | Avg R | Took 50% at 2R first |
|---|---|---|---|
| Stop (incl. gaps) | 31% | −1.1 | 1% |
| Breakeven (incl. gaps) | 55% | +0.06 | 18% |
| Close below break level (trailing) | 13% | +3.7 | 97% |

Most trades reach +1% and then come back to entry. The profit comes from the 13% that run to 2R and then trail the MA. The +1% breakeven trigger is a different distance in R per timeframe: about 0.4R on daily (stop ~2.5% away) but about 1.4R on 30m (stop ~0.7% away).

---

# Phase 1 (per trade)

## Run 2: with trading costs and the reduced SPY filter

Changes from run 1: SPY counter-signals reduced to overbought, squeeze and breakdown. Costs of 0.04% per side (0.01% commission + 0.03% slippage), i.e. 0.08% per round trip, deducted from every trade. Break level 1.5 × ATR. All figures are net avg R (cap 10).

**By timeframe**

| TF | Trades | Before costs | After costs | Cost per trade |
|---|---|---|---|---|
| 30m | 5,727 | 0.037 | **−0.088** | 0.126R |
| 1h | 7,635 | 0.070 | **−0.022** | 0.092R |
| 4h | 3,701 | 0.120 | 0.072 | 0.048R |
| 1d | 7,160 | 0.153 | 0.117 | 0.036R |
| 1w | 1,826 | 0.230 | 0.216 | 0.014R |

Intraday trades have tight stops, so the same percentage cost is a much larger share of R. 30m and 1h lose money after costs.

**Overall:** 26,049 trades, net 0.032R per trade, profit factor 1.16. Without SPY confluence the net result is −0.030R; with confluence it is +0.151R. Nearly all the profit comes from confluence trades.

**3+ prior touches vs 0–2, split by SPY confluence** (control run that trades every touch)

| TF | No confluence: 0–2 | No confluence: 3+ | Confluence: 0–2 | Confluence: 3+ |
|---|---|---|---|---|
| 30m | −0.141 | −0.093 | 0.063 | **0.280** (610 trades) |
| 1h | −0.011 | −0.007 | 0.155 | 0.159 |
| 4h | 0.038 | 0.044 | 0.103 | 0.141 |
| 1d | 0.108 | 0.172 | 0.122 | 0.082 |
| 1w | 0.234 | 0.163 | 0.327 | 0.198 |

- Intraday (30m/1h): only trades with SPY confluence are profitable. 30m with 3+ touches and confluence is the best cell, but intraday data covers only 2–4 years of a mostly rising market.
- 4h: 3+ touches and confluence both help.
- 1d/1w: profitable in every cell; 3+ touches and confluence don't add consistently.
- Year by year (3+ touches, 4h/1d/1w): losing years are 2008, 2015, 2022 (and 2007, 2018 slightly). These are market downturns, which the SPY filter doesn't fully avoid.

---

## Run 1: no costs, all six SPY counter-signals

Per-trade test of the touch signal and exit rules across 34 symbols × 60 MA/timeframe combinations. One trade per signal, measured in R (1R = distance from entry to initial stop). No portfolio rules (sizing, margin, leveraged ETFs, adding positions) yet.

**Data:** IBKR TRADES bars, regular hours. 30m: 2 years, 1h: 4 years, 4h: 5 years, 1d/1w: 20 years.

**Metric:** `avg R (cap 10)` is the average R with every trade capped at +10R. A few multi-year runners (e.g. TSLA weekly 2013, +423R) otherwise dominate the plain average.

Run with `python -m ema_touch.backtest.run --break-k 1.5` (add `--touches 0` for the control group). Full outputs: `logs/results_*.txt`, `results/*_by_combo.csv`, `results/*_trades.parquet`.

## 1. Break level: 1.5 × ATR vs strict (SPY filter on)

| | Strict (0.25 ATR) | Break 1.5 ATR |
|---|---|---|
| Trades | 3,503 | 21,687 |
| Avg R (cap 10) | 0.029 | 0.091 |
| Profit factor | 1.11 | 1.30 |

The 1.5 × ATR break level gives 6× more trades and a better result per trade.

## 2. By timeframe (break 1.5, SPY filter on)

| TF | Trades | Avg R (cap 10) | Profit factor |
|---|---|---|---|
| 30m | 4,609 | 0.021 | 1.08 |
| 1h | 6,490 | 0.048 | 1.10 |
| 4h | 2,932 | 0.084 | 1.26 |
| 1d | 6,132 | 0.161 | 1.61 |
| 1w | 1,524 | 0.219 | 3.73 |

Intraday results are thin: on 30m the average stop is ~0.7% of price, so commissions and slippage of a few hundredths of a percent would erase most of the edge.

## 3. Does "3 touches in a row" matter? (control group: every touch, break 1.5)

| Prior held touches | Trades | Avg R (cap 10) |
|---|---|---|
| 0 | 34,748 | 0.083 |
| 1 | 14,680 | 0.098 |
| 2 | 8,124 | 0.072 |
| 3 | 4,604 | 0.151 |
| 4+ | 5,274 | 0.138 |

Touches with 3+ prior held touches do better than ordinary touches (≈0.14 vs ≈0.08), clearest on 1d and 30m. On 1w the effect reverses. Year by year (1d/1w), 3+ beats 0–2 in about half the years, so the effect is real but modest and not consistent.

## 4. SPY counter-signals (break 1.5, all signals, avg R cap 10)

| Counter-signal | Share of trades | When active | When not | Verdict |
|---|---|---|---|---|
| Overbought (RSI > 70) | 9% | −0.022 | 0.082 | Keep |
| Squeeze | 11% | 0.005 | 0.081 | Keep |
| Breakdown (close through 50/100/200) | 17% | 0.029 | 0.081 | Keep |
| Below 200-day | 13% | 0.059 | 0.075 | Weak; drop? |
| Stretched (> 2 ATR from 5/10 MA) | 7% | 0.168 | 0.066 | Hurts as a filter; drop |
| Big drop (> 2 ATR down day) | 2% | 0.226 | 0.070 | Hurts as a filter; drop |

Stretched and big-drop days are mostly sell-offs (the stretch is measured in both directions), and buying touches after sell-offs worked well.

## 5. SPY confluence (SPY touching its 20/50/100/200 MA at the same time)

| | Trades | Avg R (cap 10) | Profit factor |
|---|---|---|---|
| No confluence | 14,614 | 0.050 | 1.21 |
| SPY touching | 7,073 | 0.175 | 1.51 |

The strongest effect in the test: signals with SPY confluence earn about 3.5× more per trade. This also held in the strict version. It supports using confluence for the 10% size.

## 6. Caveats

- **Survivorship bias:** the universe is today's large caps (NVDA, PLTR, TSLA, AVGO...). A long-only test on stocks we already know went up flatters every result, especially 1d/1w over 20 years.
- **Market drift:** even the control group (every touch) is profitable, so part of the result is just being long in a rising market.
- **No costs** in run 1 (added in run 2).
- **Small samples per combination:** most single MA/timeframe combinations have 30–200 trades, and the "best" combinations differ between the strict and 1.5 runs. Don't pick individual combinations from this table yet.
- **Bad ticks** in IBKR's older history are clipped when loading; trades whose stop ends up closer than 0.5 × ATR after a gap are skipped.
