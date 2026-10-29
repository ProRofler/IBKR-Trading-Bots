# Strategy: intraday reversal (day trading)

Status: research candidate, not yet traded. Every rule here was chosen by Claude from the backtests in RESEARCH.md and is waiting for review.

## 1. Core idea
A big move during yesterday's session (open to close) tends to partly reverse during today's session. After a strong down day, buy at today's open; after a strong up day, short at today's open. Close everything at today's close. No position is held overnight.

Why it might exist: a large intraday move is often forced or crowded flow (stop-outs, de-risking, chasing). Whoever absorbs that flow gets paid when it reverses. The reward is largest in stressed markets (2008, 2020, 2025).

## 2. Instruments
- **Index ETFs, long and short:** SPY, QQQ, DIA.
- **Other ETFs, short only:** SMH, SOXX, XLK, XLI, XLF, ITA, URA, GLD, SLV, GDX, MAGS, DRAM, IBIT (the ETFs in `common/universe.py`). Buying them after down days lost money in 2007–2016, so that side is off.
- **No single stocks.** A stock that falls on its own usually has news and keeps falling. Across 96 stocks the portfolio lost money in every variant tested (RESEARCH.md, test 11).

## 3. Signal (computed after yesterday's close)
- ATR = Wilder's ATR(14) on daily bars, as of yesterday's close.
- move = (yesterday's close − yesterday's open) / ATR
- **move < −0.75:** buy today's open (index ETFs only).
- **move > +0.75:** short today's open (all instruments above).
- Otherwise no trade.

The threshold sits in a plateau: 0.5, 1.0 and 1.25 also work in every 5-year era, with fewer trades and lower total return at higher thresholds.

## 4. Orders
- Entry: **market-on-open (MOO)** order sent before 9:28 ET. It fills in the opening auction at the official open, with no bid-ask spread.
- Exit: **market-on-close (MOC)** order sent before the 15:50 ET cutoff. It fills in the closing auction.
- No stop. Stops at 1.0 and 1.5 ATR lowered returns in every test, which is typical for mean reversion. The protection is the size limit and the forced exit at the close.
- Shorts: ETFs here are easy to borrow. Intraday shorts pay no borrow fee because nothing is held at settlement. A short MOO can be refused while the short-sale price test (SEC Rule 201) is active after a 10% drop; skip that trade.

## 5. Sizing
- Each position: a 1-ATR move against it costs **0.4% of equity**. So notional = 0.4% × equity / (ATR / price), about 25–40% of equity for an index ETF in normal markets.
- Caps: 50% of equity per position, 200% of equity for all positions together (IBKR intraday buying power is 4× for accounts over $25k). When signals exceed the cap, every position is scaled down equally.
- On average the strategy trades on 49% of days, with 0.69× equity gross exposure on those days.
- US pattern day trader rule: a margin account needs at least $25,000 equity to day trade.

## 6. Expected results (backtest 2006-11 → 2026-10, costs included)
| | Strategy | SPY buy & hold |
|---|---|---|
| CAGR | 4.5% | 9.1% |
| Volatility | 8.0% | 19.5% |
| Sharpe | 0.59 | 0.54 |
| Max drawdown | −11.7% | −56.5% |
| Winning months / years | 54% / 71% | 64% / 76% |
| Correlation with SPY (daily) | −0.11 | |

Sharpe by era: 2007–11 0.57, 2012–16 0.51, 2017–21 0.71, 2022–26 0.54. The best years were turbulent ones (2008 +11.6%, 2020 +16.9%, 2025 +26.3%); calm years are flat to slightly negative (2013 −6.1%, 2023 −5.2%).

**Costs decide it.** Modelled: $0.005/share commission plus 1 bp slippage per side, about 10 bp of net edge per trade. At 2 bp slippage Sharpe falls to 0.38, and at 3 bp to 0.17. Auction orders are what make it viable; entering with market orders a few minutes after the open would likely cost more than the edge.

## 7. Known weaknesses
- Modest edge, thin after costs (section 6).
- Returns are lumpy: they come mostly in high-volatility years.
- The 0.75 threshold and the "short only" rule for non-index ETFs were picked after looking at the full 2007–2026 data. Both sit on stable plateaus, but this is not an out-of-sample result.
- The daily bars' open and close are IBKR's first and last trade prices, not necessarily the auction prints. For these ETFs the difference is normally a cent or two, but that is exactly the size of the edge. Check it with paper fills before trading real money.
