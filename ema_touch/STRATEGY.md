# Strategy: MA touch (draft)

Status: draft. Everything marked **[proposed]** was filled in by Claude and is waiting for review. Unmarked items were decided by the user.

## 1. Core idea
If price has touched a moving average 3 times in a row and held it each time, we expect it to hold on the 4th touch. We enter on that 4th touch.

## 2. Indicators and timeframes
- Moving averages: **EMA only**, periods 5, 10, 20, 50, 100, 200 (6 lines). SMA was dropped on 2026-10-28; this applies to signals and the index checks.
- Timeframes: 30m, 1h, 4h, 1d, 1w
- Entry points: the 10, 20, 50, 100 and 200 EMA (the 5 EMA is not an entry), so 25 EMA/timeframe combinations per symbol
- ATR (average true range) is calculated on the same timeframe as the MA, period 14 **[proposed]**

## 3. Signal

### 3.1 Touch (ATR-based tolerance)
- Band = MA ± k × ATR, with k = 0.25 **[proposed]**
- **Touch:** the bar's low enters the band
- **Held:** the bar closes above MA − k × ATR, so a small pierce is allowed
- **Not held:** the bar closes below the band. It doesn't count as a touch.
- **Break:** a close below the **break level = MA − 1.5 × ATR**. Breaks do **not** reset the count (changed 2026-10-28): if the instrument has reacted to this EMA in the past, we assume it will again, even if it broke through in between.
- After any touch (held or not), price must trade fully above the band again before the next touch counts
- Touches must be at least 5 bars apart **[proposed]**
- **Signal:** at least 3 held touches within the last **500 bars** **[proposed]**, so old reactions eventually age out. 500 bars is about 38 trading days on 30m, about 2 years on 1d and about 10 years on 1w.
- Tested and not needed: also requiring the EMA to have held at least 60% of the time (held touches vs breaks).

### 3.2 Trend filter [proposed]
- Price approaches the MA from above (the bars before the touch closed above the band).
- The MA slopes up: MA now > MA 5 bars ago.

### 3.3 Direction [proposed]
- Long only in version 1. Shorts and inverse ETFs (SH, PSQ, SQQQ) can be added later as a mirror of the same rules.

## 4. Market filter (indexes)

### 4.1 Benchmarks
- SPY is the main benchmark for every stock.
- QQQ and DIA are additional checks. Tech stocks (IBKR sector field) get QQQ checked as well. DIA is checked for all stocks as general market breadth **[proposed]**.

### 4.2 Strong counter-signals
Index counter-signals are checked on the **daily** timeframe **[proposed]**:

- **Overbought:** RSI(14) > 70 **[threshold proposed]**
- **Squeeze:** a volatility squeeze, meaning Bollinger Bands (20, 2) are inside Keltner Channels (20, 1.5 × ATR). The index is coiled and the direction of the next move is unknown **[interpretation proposed]**
- **Breakdown:** the index closed through the band of its 50, 100 or 200 MA within the last 3 bars

Dropped after the backtest of 2026-10-28 (see BACKTEST_RESULTS.md), because they made results worse when used as blocks:
- Stretched: more than 2 × ATR from the 5/10 MA
- SPY below its 200-day MA
- Big down day: SPY fell more than 2 × ATR in one day

### 4.3 How the filter is applied
- A counter-signal on **SPY** is a hard block: no new entries.
- A counter-signal on **QQQ or DIA** (where checked) caps the position at 5%.
- **Confluence:** SPY's daily bar is touching its 20, 50, 100 or 200 MA (SMA or EMA, as in section 3.1).
  - **30m and 1h:** confluence is **required**. Without it these timeframes lost money after costs in the backtest.
  - **4h, 1d, 1w:** confluence is optional and raises the size to 10% (section 6).

## 5. Instruments
- Individual stocks
- Index ETFs SPY, QQQ, DIA, traded on their own touch signals, with SPY counter-signals still applying
- Leveraged ETFs on indexes and on single stocks, e.g.:
  - SPY → SSO (2×) / UPRO (3×)
  - QQQ → QLD (2×) / TQQQ (3×)
  - DIA → DDM (2×) / UDOW (3×)
  - MSFT → MSFU, PLTR → PLTU, and similar single-stock leveraged ETFs
- The underlying → leveraged ETF mapping lives in a config file. Each ticker is verified against IBKR contract details before use.
- Signals for leveraged ETFs are calculated on the underlying (index or stock); orders are executed in the leveraged ETF.
- Leveraged ETFs are sized like any other position: 5–10% of the portfolio in dollars, with no adjustment for leverage.

### 5.2 When to use leveraged ETFs
- Up to 100% of net liquidation invested: trade the plain instrument.
- Above 100% (on margin): **prefer** the leveraged ETF of the signal's underlying when one exists. If none exists, trade the plain instrument on margin.
- Cap: the full margin IBKR allows. Before each order the bot runs an IBKR what-if check and skips the order if it would exceed available funds.
- Kept after the robustness test (user decision 2026-10-29): versus plain margin they add about 2–5 points of CAGR and 2–5 points of drawdown at the same Sharpe (BACKTEST_RESULTS.md, run 11).
- Note: IBKR usually charges higher margin requirements on leveraged ETFs, so they use up buying power faster than their dollar size suggests.
- Use 2× where both 2× and 3× exist **[proposed]**: the daily-reset decay is much smaller.
- Leveraged ETFs are not used for 1w signals, and the maximum hold is 15 trading days **[proposed]**: daily-reset products lose value over long holds in choppy markets.

## 6. Position sizing
- Base size: **5%** of net liquidation.
- **10%** with SPY confluence (section 4.3), unless a QQQ (tech stocks) or DIA counter-signal caps it at 5%.
- Size is in dollars, rounded down to whole shares.

## 7. Entry [proposed]
- Wait for the touch bar to **close** and hold (section 3.1).
- Then send a **limit buy at that bar's close + 0.1 × ATR**, valid for one bar. If it doesn't fill, the signal expires.
- One position per symbol. If several MA/timeframe combinations trigger at once, the **highest timeframe** (and within it, the longest MA) defines the stop and exit.
- **Strongest signals first** (adopted 2026-10-28): when signals on different symbols arrive at the same time and buying power or the adding rule can't take them all, take them in order of timeframe (1w first), then entry EMA (200 first). In the robustness test this raised the median return and made results much less dependent on luck (BACKTEST_RESULTS.md, run 11).

## 8. Exits [proposed]
All exit orders are sent to TWS as a **bracket** together with the entry, so IBKR holds them even if the bot is offline.

- **Initial stop:** the lower of (MA − 1 × ATR) and (touch-bar low − 0.25 × ATR)
- **Breakeven:** at +1% profit, move the stop to the entry price
- R = entry − initial stop. Each timeframe uses the best exit tested for it (BACKTEST_RESULTS.md, runs 9–10).

| Timeframe | Take profit |
|---|---|
| 30m | Sell the **whole position at 4R** |
| 1h | Sell **50% at 3R**; the rest exits on a close below the break level |
| 4h, 1d, 1w | **EMA ladder** down to the 20 EMA, stop 1 × ATR below the support EMA |

**30m: whole position at 4R**
- One limit order at entry + 4R. Before that, the position exits at the stop or on a close below the break level (MA − 1.5 × ATR).
- Selling everything beat selling half on 30m: 0.097R per trade vs 0.081R for half at 3R (2R: 0.032, 3R: 0.067).

**1h: half at 3R + trail**
- **Part 1:** sell 50% at **3R**.
- **Part 2:** the remaining 50% exits when a bar closes below the break level of the signal MA (MA − 1.5 × ATR, the touch streak broke), or at the stop.
- Until the stop moves to breakeven, the initial stop (MA − 1 × ATR) is above the break level, so it triggers first. After breakeven, the break level acts as a trailing exit as the MA rises.
- On 1h this beat selling everything (0.195R vs 0.114–0.171R). The trailed half often gives back to below 3R (median +1.0R), but its runners average +2.15R.

**4h, 1d and 1w: EMA ladder**
- After entry on an EMA, when a bar closes above a shorter EMA, that EMA becomes the new support. The stop moves to EMA − 1 × ATR, is updated every bar and is never lowered.
- Rungs: 20, 50, 100, 200 EMA. Example: entry on the 200 EMA climbs 100 → 50 → 20. An entry on the 10 EMA trails the 10 EMA once its stop is at breakeven.
- The whole position exits at the stop. There is no partial target.
- The 20 EMA as the lowest rung beat the 10 EMA on all three timeframes, and a 1 ATR wiggle beat 0.5 ATR (run 10).

Tested and rejected (BACKTEST_RESULTS.md, runs 4–5, 9–10):
- Tighter trailing exits (touch band, 2–3 ATR chandelier) and profit locks (stop to +0.25R after +1R, or +0.5R after +1.5R).
- Wiggle 0–0.5 ATR, and the 5 or 10 EMA as the lowest ladder rung.
- They keep more of each winner's peak but cut the big runners short, which earn most of the profit.

## 9. Rule for adding positions
- Each position's stop moves to entry once that position is +1% (section 8). The +1% is measured on the position, not the portfolio.
- No limit on the number of open positions; buying power is the only limit (section 5.2).

### 9.1 Winners as a buffer (adopted 2026-10-28)
- **Locked profit:** for each position whose stop is above entry, the dollars it keeps if that stop is hit.
- **Open risk:** for each position whose stop is below entry, the dollars it loses if that stop is hit.
- **Rule:** a new position is allowed if the open risk of the existing positions is at most **2 × the locked profit**.
- With no locked profit this is the original rule: every open position must be out of risk (stop at entry or better) before a new one opens.

### 9.2 Adding to winning positions (adopted 2026-10-28)
- A new signal on a symbol already held opens another lot (5–10%, sized as usual) if every existing lot of that symbol has its stop at entry or better.
- At most 3 lots per symbol, and at most 20% of equity in one symbol **[proposed]**.
- Each lot keeps its own stop and exit.

## 10. Universe
- Only successful instruments in a positive trend that already show EMA patterns. Poor performers are not traded.
- Index ETFs: SPY, QQQ, DIA (plus SSO, QLD, DDM for execution).
- Stocks: the original 31 large caps plus 49 stocks that have trended since 2022, any size (e.g. RKLB, MNST, APP, CTAS).
- Sector / thematic / commodity ETFs: SMH, SOXX, XLK, XLI, XLF, ITA, URA, GLD, SLV, GDX, MAGS, DRAM, IBIT.
- 2× leveraged ETFs where one exists (32 verified in IBKR), used per section 5.2.
- The watchlist is `common/universe.py` and can be changed at any time.
- The list is picked by hand, knowing what trended, so backtests overstate what to expect live.
- A trend screen (only trade a symbol above its rising 200-day EMA) was tested and is **off** (`Params.trend_filter`). It lowered returns in every window (run 11), but that test is biased against it: in a list of known winners, buying their dips worked by construction. Review the list periodically by hand instead and remove names that stop trending.
- With 96 symbols the margin cap is almost always full, and many of the new names fall together (June–October 2026: APP, CRWV, VRT, NBIS −40–57%). See BACKTEST_RESULTS run 8.

## 11. Risk limits
- No daily or weekly loss limits: losses don't stop new entries. Risk is controlled per position by stops and by the rule for adding positions (section 9).
- Overnight and weekend holds are allowed. Stops stay live in TWS.
- No new entries in the first 15 minutes after the open **[proposed]**.

## 12. Data
- Backtesting: IBKR historical bars.
- Paper trading: 15-minute delayed data is treated as real-time for now, on all timeframes. Intraday signals will fire about 15 minutes late, which is acceptable for testing.
- Before trading live: subscribe to real-time US stock data in IBKR.

## 13. Validation plan
1. Backtest the touch signal (sections 3–4) across all 60 MA/timeframe combinations on the universe, with and without the index filter.
2. Measure: how often the 4th touch held, average R per trade, win rate, maximum drawdown.
3. Keep only combinations with a positive edge, then run the full rules (sections 6–11) in the backtest.
4. Paper-trade the surviving combinations live.
