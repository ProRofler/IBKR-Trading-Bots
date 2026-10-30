# Backtest results (2026-10-28)

## Run 17: 10% / 20% positions with a 10% SPY floor (2026-10-30)

Proposal: positions of 10% of equity (20% with SPY confluence; per-symbol cap stays 20%), and always hold at least 10% of equity in SPY before buying anything else. Modeled as a permanent SPY core (`Params.spy_core = 0.10`): 10% of realized equity in SPY from day one, rebalanced daily (rebalancing commissions ignored), counted toward the 2× margin cap. Also tested the stricter reading (`Params.spy_gate`): other symbols are entered only while the strategy itself holds a SPY trade. All at $10k with Tiered commissions, previous 96 symbols. `python -m ema_touch.backtest.robust --match "spy:"` (round 8, `results/robust_runs_round8.csv`, `logs/robust8.txt`).

**Portfolio, 20 replays each: median CAGR (10th–90th percentile) / median max DD (worst) / median Sharpe**

| Setup | 2007–2026 | 2022–2026 | Last 2 years |
|---|---|---|---|
| Current: 5% / 10%, no floor | 23.8% (23–26) / −38% (−43%) / 1.07 | **46.5%** / −29% / 1.50 | 46.6% / −23% / 1.49 |
| 10% / 20%, no floor | **25.5%** (22–28) / −32% (−40%) / 1.08 | 38.5% / −29% / 1.26 | **50.4%** / −22% / 1.59 |
| **Proposal:** 10% / 20%, 10% SPY core | 25.0% (23–28) / −32% (−41%) / 1.05 | 39.7% / −28% / 1.27 | 49.1% / −22% / 1.55 |
| 10% / 20%, 10% SPY core, no lev ETFs | 24.5% (21–27) / **−32% (−37%)** / 1.10 | 39.8% / −25% / 1.35 | 44.1% / −21% / 1.49 |
| 10% / 20%, only while a SPY trade is open | 13.5% / −35% / 0.78 | 19.0% / −33% / 0.91 | 20.5% / −34% / 0.91 |
| 5% / 10%, 10% SPY core | 23.8% / −40% / 1.06 | 44.4% / −30% / 1.46 | 48.2% / −23% / 1.54 |

**Findings**
- **The SPY core changes almost nothing** (within ±1.5 points of the same sizing without it, everywhere). A 10% SPY sleeve earns about 1% of equity a year, but it also takes 10% of the 2× margin budget, and signals are often refused because the cap is reached (skip_margin is the most common decision), so in busy periods it replaces strategy positions with SPY.
- **10% / 20% sizing:** since 2007 slightly more return (25.5% vs 23.8%) with clearly smaller drawdowns (−32% vs −38%), but since 2022 clearly worse (38–40% vs 46.5%) and a wider spread between replays. Sharpe is about the same overall. Unlike run 16's 20% / 30%, it does not make results noticeably more luck-dependent since 2007.
- **Gating entries on the strategy's own SPY trade halves the return:** SPY is in a trade only part of the time, so most signals are skipped.

## Run 16: bigger positions, sized on 2× equity (2026-10-30)

Proposal: treat the account as twice its size (`Params.sizing_base = 2`), size positions at 10% of that (15% with SPY confluence), i.e. 20% / 30% of equity; allow up to 3× equity in positions and switch to leveraged ETFs above 2×. The per-symbol cap (20%) also applies to 2× equity. All at $10k with Tiered commissions, previous 96 symbols, run 13 rules. `python -m ema_touch.backtest.robust --match "size:"` (round 7, `results/robust_runs_round7.csv`).

**Portfolio, 20 replays each: median CAGR (10th–90th percentile) / median max DD (worst) / median Sharpe**

| Setup | 2007–2026 | 2022–2026 | Last 2 years |
|---|---|---|---|
| Current: 5% / 10% of equity, 2× cap, lev ETFs above 1× | 23.8% (23–26) / −38% (−43%) / 1.07 | 46.5% / −29% / 1.50 | 46.6% / −23% / 1.49 |
| **Proposal:** 20% / 30% of equity, 3× cap, lev ETFs above 2× | **35.1%** (29–38) / −43% (−50%) / 1.09 | 55.1% / −36% (−45%) / 1.32 | 66.7% / −24% / 1.56 |
| 20% / 30%, 3× cap, no lev ETFs | 33.4% (29–38) / −43% (−49%) / 1.11 | **60.6%** / −30% / 1.47 | 63.8% / −23% / 1.56 |
| 20% / 30%, 2× cap, lev ETFs above 1× | 22.9% (20–27) / −42% (−50%) / 0.95 | 37.7% / −36% (−57%) / 1.17 | 45.8% / −20% / 1.42 |
| 20% / 30%, 2× cap, no lev ETFs | 26.1% (19–33) / −40% / 1.06 | 35.9% / −34% / 1.20 | 53.3% / −19% / 1.64 |
| 20% / 30%, no margin | 13.0% / −32% / 0.85 | 21.6% / −23% / 1.12 | 27.1% / −16% / 1.39 |

**Findings**
- **Bigger positions alone don't help.** At the same 2× cap they give about the same or less (22.9–26.1% vs 23.8% since 2007) with deeper drawdowns and a much wider range between replays: fewer, larger positions make results depend more on which signals happened to get the capital.
- **The gain comes from the 3× cap** (33–35% vs 24% since 2007). Sharpe stays the same (1.07 → 1.09–1.11): it is more leverage, not more edge, with drawdowns of −43% (worst −50%). Leveraged ETFs above 2× add little over plain 3× (35.1% vs 33.4%, and worse since 2022).
- **A $10k Reg T margin account can't hold 3× overnight:** the initial margin for stocks held overnight is 50%, i.e. 2× (4× intraday only for pattern day traders with $25k+). Higher leverage needs a portfolio margin account (minimum $110k at IBKR) or leveraged ETFs, and IBKR charges leveraged ETFs higher margin. Margin calls and forced liquidation are not modeled; at 3× a −43% drawdown would likely have triggered them.
- One real benefit of bigger positions at $10k: a 20% position is $2,000, so every one of the 96 symbols can be bought in whole shares, and the $0.35 minimum commission matters less.

## Run 15: higher win rate (later breakeven, partial profit) and small-account commissions (2026-10-30)

Run 13 rules on the previous 96 symbols. Variants (`Params.breakeven_r`, `Params.ladder_partial_r` / `ladder_partial_fraction`): stop to breakeven at +0.5R / +1R / +2R / +3R / never (instead of +1%), and selling 25% at +2R with the rest on the EMA ladder. Cost models (`Params.start_equity`, `Params.commission_min`): $1M with percentage costs as before, and $10k with a minimum commission per order of $1 (IBKR Fixed) or $0.35 (IBKR Tiered, approximate). Run with `python -m ema_touch.backtest.exits` (round 8) and `python -m ema_touch.backtest.robust --match '$'` (round 6, `results/robust_runs_round6.csv`).

**Per trade (all 152 symbols, entry rules on)**

| Variant | Win rate | Avg R (cap 10) | Return per trade | Avg R on the 56 steady stocks |
|---|---|---|---|---|
| Breakeven at +1% (current) | 19.6% | 0.115 | 0.7% | 0.079 |
| at +0.5R | 22.7% | 0.143 | 1.0% | 0.096 |
| at +1R | 29.7% | 0.194 | 1.3% | 0.140 |
| at +2R | 34.1% | 0.239 | 1.6% | 0.186 |
| at +3R | 32.2% | 0.266 | 1.8% | 0.210 |
| 25% at +2R, rest on the ladder | 21.7% | 0.112 | 0.6% | |

**Portfolio, 20 replays each: median CAGR / median max DD / median Sharpe**

| Variant | 2007–2026, $1M | 2022–2026, $1M | Last 2 years, $1M | Last 2 years, $10k Fixed |
|---|---|---|---|---|
| **Breakeven at +1% (current)** | 24.5% / −38% / 1.10 | 46.6% / −29% / 1.54 | **48.0% / −23% / 1.53** | 42.3% |
| at +0.5R | 27.3% / −35% / 1.11 | 49.6% / −31% / 1.54 | 13.0% / −21% / 0.65 | 10.3% |
| at +1R | 23.9% / −36% / 1.00 | 51.8% / −32% / 1.53 | 20.1% / −24% / 0.81 | 13.1% |
| at +2R | 25.7% / −42% / 1.03 | 52.8% / −32% / 1.57 | 11.8% / −23% / 0.60 | 10.3% |
| at +3R | 28.8% / −40% / 1.10 | 46.8% / −32% / 1.46 | 10.6% / −22% / 0.59 | 5.6% |
| never (ladder only) | 9.2% / −36% / 0.54 | 51.9% / −35% / 1.43 | 12.3% / −27% / 0.58 | 9.2% |
| 25% at +2R | 20.0% / −36% / 0.96 | 39.0% / −32% / 1.33 | 37.8% / −26% / 1.27 | 31.6% |
| +1R and 25% at +2R | 18.8% / −37% / 0.84 | 41.0% / −35% / 1.33 | 2.2% / −20% / 0.23 | −0.4% |

**Commission at $10k (current rules)**: CAGR 2007– / since 2022 / last 2 years

| Cost model | 2007– | 2022– | Last 2 years |
|---|---|---|---|
| $1M, percentage costs | 24.5% | 46.6% | 48.0% |
| $10k, $1 minimum (IBKR Fixed) | 21.8% | 40.4% | 42.3% |
| $10k, $0.35 minimum (IBKR Tiered) | 23.8% | 46.5% | 46.6% |

**Findings**
- **A later breakeven raises the win rate and the edge per trade, on the trend and the steady stocks alike, but not the portfolio.** It wins some windows and loses the last 2 years badly (48% → 11–20%). The +1% breakeven is what feeds the buffer rule: positions get out of risk within days, so new ones can open. With a later breakeven, positions stay at risk longer, the buffer rule blocks entries, and the account sits under-invested (exposure over the last 2 years: 0.81× → 0.46× at +3R). Without any breakeven, almost nothing gets out of risk after the first positions, so the account is nearly empty (exposure 0.04× since 2007). **Kept at +1%.**
- **Partial profits lower returns everywhere** (25% at +2R: 24.5% → 20.0%). Rejected again.
- **The win rate stays around 20%.** It is the price of this design: many tiny breakeven exits keep the risk budget free for new entries, and a few long trends pay for everything.
- **At $10k, IBKR Fixed's $1 minimum costs 3–6 points of CAGR a year; Tiered's ~$0.35 minimum costs about 1.** Use Tiered pricing for the small account. Positions are not rounded to whole shares here: at $10k, 21 of the 96 symbols cost more than a 5% position ($500), and rounding leaves the rest about 18% under size.

## Run 14: 56 steady large caps added (2026-10-29)

Added `common.universe.STEADY_STOCKS`: big, liquid names in steady but unspectacular uptrends (MS, AXP, SPGI, HON, UNP, LMT, MCD, LOW, ABT, TMO, AMGN, CSCO, IBM, TXN, INTU, NEE, COP, PLD, …). Daily and weekly bars only. Data fixes: IBKR's history has a year missing for CME (2007-07 to 2008-07) and 2.5 years for TMUS (2013-04 to 2015-10, MetroPCS before), cut with `HISTORY_START`. A gap scan of all 152 symbols finds no other holes. Run 13 rules (1d touch entry, 1w next-bar). `python -m ema_touch.backtest.robust`, round 5 (`results/robust_runs_round5.csv`).

**Per trade (entry rules on, after costs), avg R (cap 10) / return per trade / profit factor**

| Group | 1d | 1w | 1d / 1w since 2022 (avg R) |
|---|---|---|---|
| Steady 56 | 0.074 / 0.2% / 1.23 | 0.108 / 0.8% / 1.60 | 0.005 / 0.036 |
| Previous 96 | 0.115 / 0.5% / 1.39 | 0.281 / 3.7% / 3.05 | 0.141 / 0.274 |
| Original 34 | 0.079 / 0.3% / 1.27 | 0.226 / 3.1% / 2.53 | 0.060 / 0.138 |

On the steady 56 the edge per trade is positive in every 5-year era but small, and close to zero since 2022 (1d by era: 0.036, 0.080, 0.164, 0.005).

**Portfolio, 20 replays each: CAGR median (10th–90th percentile) / median max DD / median Sharpe**

| Universe | 2007–2026 | 2022–2026 | Last 2 years |
|---|---|---|---|
| Previous 96 | 24.5% (24–26) / −38% / 1.10 | 46.6% (41–52) / −29% / 1.54 | 48.0% (43–52) / −23% / 1.53 |
| All 152 | 20.4% (19–22) / −31% / 1.03 | 37.3% (34–43) / −27% / 1.49 | 24.0% (20–45) / −13% / 1.43 |
| ↳ random 75% of symbols | 21.0% / −31% / 1.06 | 34.0% / −28% / 1.39 | 24.5% / −15% / 1.29 |
| ↳ no margin | 13.1% / −18% / 1.08 | 23.6% / −16% / 1.49 | 19.1% / −8% / 1.54 |
| Steady 56 only | 10.6% (10–12) / −24% / 0.75 | 6.8% / −19% / 0.58 | 11.8% / −9% / 1.23 |
| Original 34 | 13.3% / −29% / 0.81 | 11.2% / −29% / 0.63 | 9.8% / −15% / 0.69 |
| SPY buy & hold | 8.9% / −57% / 0.54 | 10.4% / −25% / 0.66 | 16.2% / −19% / 1.00 |

**Findings**
- **Adding the steady names lowers returns in every window** (2007–: 24.5% → 20.4%; last 2 years: 48% → 24%) and lowers drawdowns (−38% → −31%; −23% → −13%). Sharpe is a little lower. Over the last 2 years the average exposure falls from 0.81× to 0.57×: steady positions sit at risk longer and the buffer rule then blocks new entries, so capital goes to weaker names instead of waiting for strong ones.
- **On ordinary large caps alone the strategy is modest:** 10.6% CAGR since 2007 with a −24% drawdown, vs SPY's 8.9% with −57%. Better risk-adjusted than SPY, but below SPY since 2022. Most of the headline return comes from trading strong trending stocks, which supports picking symbols by a relative-strength rule instead of by hand.
- **Replay noise:** "previous 96" here and "1d touch + 1w next-bar" in run 13 are the same trades, but adding symbols changes each signal's random order. The medians came out 24.5% vs 26.1%. Differences of 1–2 points between replay sets are noise.

## Run 13: daily and weekly only (2026-10-29, now the default)

30m, 1h and 4h are no longer traded (`Params.timeframes = ("1d", "1w")`). **Adopted: touch entry on 1d, next-bar entry on 1w** (row "1d touch + 1w next-bar" below; user decision after the weekly finding). Default trades: `results/default_trades.parquet` = `exit_touch_1d` on 1d/1w. `python -m ema_touch.backtest.robust`, round 4 (`results/robust_runs_round4*.csv`).

**Portfolio, 20 replays each: CAGR median (10th–90th percentile) / median max DD / median Sharpe**

| Setup | 2007–2026 | 2022–2026 | Last 2 years |
|---|---|---|---|
| All 5 timeframes (run 12 default) | 30.7% (29–32) / −33% / 1.28 | 45.6% (34–52) / −27% / 1.45 | 47.7% (39–60) / −21% / 1.56 |
| **1d + 1w** | **30.7% (29–32) / −32% / 1.30** | **47.0% (44–51) / −25% / 1.56** | 43.6% (34–54) / −21% / 1.46 |
| ↳ no leveraged ETFs (plain margin) | 27.2% (26–28) / −28% / 1.28 | 39.7% / −22% / 1.54 | 39.5% / −21% / 1.44 |
| ↳ no margin (max 100% invested) | 16.1% (15–17) / −14% / 1.23 | 19.6% / −13% / 1.31 | 24.5% / −10% / 1.54 |
| ↳ random 75% of symbols | 30.0% (28–33) / −32% / 1.29 | 49.3% / −25% / 1.58 | 46.5% (24–58) / −25% / 1.48 |
| ↳ original 34 | 15.1% (15–16) / −26% / 0.91 | **3.0%** (2–4) / −26% / 0.27 | 9.7% / −9% / 0.76 |
| ↳ strict adding rule | 5.3% / −8% / 0.95 | 2.9% | 1.6% |
| 1d + 1w, next-bar entry on both | 21.1% (19–22) / −36% / 0.99 | 41.2% / −27% / 1.35 | 38.5% / −27% / 1.29 |
| ↳ original 34 | 13.0% / −30% / 0.79 | 14.9% / −21% / 0.81 | 12.0% / −14% / 0.82 |
| **1d touch + 1w next-bar (adopted)** | **26.1% (24–27) / −37% / 1.14** | **46.7% (45–52) / −30% / 1.52** | **45.3% (41–50) / −23% / 1.49** |
| ↳ random 75% of symbols | 24.9% (23–28) / −33% / 1.11 | 49.5% / −28% / 1.55 | 40.3% (27–60) / −24% / 1.40 |
| ↳ original 34 | 12.6% / −29% / 0.79 | 11.0% / −29% / 0.62 | 10.0% / −15% / 0.70 |
| SPY buy & hold | 8.9% / −57% / 0.54 | 10.4% / −25% / 0.66 | 16.2% / −19% / 1.00 |

**Findings**
- **Dropping 30m/1h/4h costs nothing:** same return since 2007, slightly lower drawdown, higher Sharpe since 2022, a little lower over the last 2 years. The bot only needs daily bars. Adopted.
- **Leverage is still a risk dial:** Sharpe is 1.23–1.30 with leveraged ETFs, plain margin or no margin.
- **Warning: on the original 34 large caps the touch entry on 1w did badly since 2022** (3.0% CAGR vs 14.9% with the next-bar entry). Weekly positions earned $141k vs $699k in one replay; weekly trades on these 34 since 2022 averaged +0.56% vs +2.44%. Over the full period the touch entry is still better on the same 34 (15.1% vs 13.0%), and on all 96 it is better in every window. Weekly trades on 34 symbols over 4 years are a small sample, so this may be noise, but it is the weakest spot of the current rules. The tighter weekly stop (median 6.5% vs 8.0% of price) shakes out of more of the big weekly trends.
- On the original 34, the touch entry doesn't help on 1d either recently; its gain comes from the trend stocks added in run 8, where the next-bar entry often misses gap-ups after a touch.: buy on the touch, check the hold before the close (2026-10-29, now the default on 1d/1w)

**Rule tested** (`Params.entry_mode = "touch"`): a limit buy rests at the top of the touch band (previous bar's EMA + 0.25 ATR) and fills when price touches it during the session; the stop is the previous bar's EMA − 1 ATR. Near the close, if price is below the band (the touch didn't hold), sell. Otherwise manage the position as before. The old rule (`"next_bar"`) waited for the touch bar to close and held, then bought the next bar at close + 0.1 ATR. Run with `python -m ema_touch.backtest.exits` (round 7) and `python -m ema_touch.backtest.robust` (round 3, `results/robust_runs_round3.csv`).

**Per trade (entry rules on, after costs)**

| Timeframe | Next-bar entry: avg R (cap 10) / return per trade / trades | Touch entry |
|---|---|---|
| 30m | 0.097 / 0.14% / 11,192 | 0.052 / 0.08% / 12,253 |
| 1h | 0.195 / 0.38% / 10,569 | 0.144 / 0.30% / 11,255 |
| 4h | 0.088 / 0.36% / 17,520 | 0.089 / 0.36% / 18,456 |
| 1d | 0.072 / 0.36% / 23,784 | **0.115 / 0.54% / 26,818** |
| 1w | 0.281 / 3.73% / 4,906 | **0.304** / 3.29% / 4,828 |

On 1d the better price shows: 17.6% of trades reach the trailing exit vs 15.8%. 9% of touches don't hold and are sold at the close, at about −1.9% each. On 1w the stop is tighter (median risk 6.5% vs 8.0%), so R is higher but the average return per trade is lower.

**Portfolio, 20 replays each: CAGR median (10th–90th percentile) / median max DD / median Sharpe**

| Setup | 2007–2026 | 2022–2026 | Last 2 years |
|---|---|---|---|
| Next-bar entry (run 11 default) | 21.8% (20–24) / −38% / 0.98 | 40.3% (33–45) / −33% / 1.29 | 37.9% (35–40) / −25% / 1.25 |
| **Touch entry on 1d + 1w** | **30.7% (29–32) / −33% / 1.28** | 45.6% (34–52) / **−27%** / 1.45 | 47.7% (39–60) / **−21%** / **1.56** |
| Touch entry on 1d only | 27.6% (26–29) / −38% / 1.15 | **49.7% (47–55)** / −34% / **1.47** | **48.6%** (32–57) / −23% / 1.47 |
| Next-bar, random 75% of symbols | 19.0% (17–23) / −39% / 0.89 | 38.6% / −32% | 29.0% / −26% |
| Touch on 1d, random 75% of symbols | 25.1% (21–27) / −37% / 1.09 | 44.9% / −32% | 38.0% / −25% |

**Findings**
- The touch entry on 1d + 1w beats the next-bar entry in every window, with lower drawdowns and a higher Sharpe. Average exposure rises only from 0.98× to 1.09×, so most of the gain is not extra leverage. **Adopted for 1d and 1w** (`Params.tf_overrides`).
- 30m and 1h are worse with the touch entry, and 4h is unchanged; they keep the next-bar entry. A check 15 minutes before a 30m bar closes is also impractical with delayed data.
- **The close as a stand-in for "15 minutes before the close":** on daily touches since 2024-11 (4,153 with 30m data), deciding at 15:30 matches the decision at the close 95% of the time. 3% looked held at 15:30 but failed by the close (we'd keep them), 2% the reverse (we'd sell them). With 15-minute delayed data, a check at 15:45 sees about the 15:30 price, so this is what live trading on delayed data would get.
- Robustness experiments from run 11 (`robust.py` rounds 1–2) still use the next-bar trades (`results/exit_next_bar_trades.parquet`).

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
