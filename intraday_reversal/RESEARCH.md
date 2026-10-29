# Day-trading research (2026-10-29)

Goal from the user: a day-trading strategy that is consistent rather than aggressive. All positions close by the end of the day; shorting and intraday margin are allowed.

## Summary

| # | Idea | Data | Result | Verdict |
|---|---|---|---|---|
| 1 | Noise-area intraday momentum (Zarattini, Aziz, Barbon 2024) on index/sector ETFs | 30m 2y, 1h 4y | Negative on SPY, DIA, XLF, XLI; positive only on QQQ/XLK (Sharpe ~1.0 on 1h) | Rejected: depends on which ETF |
| 2 | Early-day signals (gap, first 30 min, relative volume) → rest of day, cross-sectional | 30m, 1h | 1–10 bp/day spreads, t < 2 | Rejected: below costs |
| 3 | Time-series momentum/reversal by time of day (incl. "last half hour", Gao et al. 2018) | 30m, 1h | ≤ 3 bp, no slot significant | Rejected |
| 4 | Opening range breakout (9 variants: breakout/candle, OR/mid/ATR stops, targets) | 30m, 1h | Best: wide-stop breakout on high-volume days, ~15 bp net/trade; tight stops can't be judged on 30m bars | Inconclusive: needs 5-min data |
| 5 | Gap fade on stocks | 30m, 1h | Raw t-stats look strong, but the effect is concentrated on days when the whole market gapped >1%, and it fails in 2024 and 2026 | Rejected |
| 6 | Intraday pairs mean reversion (correlated stocks/ETFs) | 30m | ~2.6 bp gross per trade, negative after costs | Rejected |
| 7 | Gap momentum ("stocks in play": big gap, high volume) | 30m, 1h | Stocks ~0; ETFs only on market-wide gap days, mostly 2025 | Rejected |
| 8 | Open-to-close cross-sectional sorts (gap, prior day, momentum, IBS, RSI2…) | 1d, 20y | Only gap reversal, and it decayed from 36 bp/day (2007–11) to ~4 bp (2017–26) | Rejected: decayed |
| 9–12 | **Open-to-close reversal after a big intraday move, ETFs** | 1d, 20y | Sharpe 0.59 with costs, positive in all four 5-year eras | **Adopted** → STRATEGY.md |

Bottom line: on the 96 liquid large caps and ETFs in the cache, the published intraday edges are thin or gone after costs. The one that survives 20 years is next-day intraday reversal on ETFs. It is real but modest: about 4–5% a year at 8% volatility, max drawdown −12%, and returns concentrated in turbulent years.

## Data and method
- Intraday: cached 30m bars (Oct 2024 → Oct 2026) and 1h bars (Oct 2022 → Oct 2026) for all 96 symbols. Daily: up to 20 years.
- Fills at the next bar's open after a signal; exits at the day's last close. Costs 1–2 bp slippage per side plus $0.005/share, unless stated.
- Bar-resolution caveat: with 30m bars, when a stop and the entry both fall inside one bar the order is unknown. The tests assume the stop was hit (conservative). That makes tight-stop strategies (e.g. 5-minute ORB with a 10%-of-ATR stop) look much worse than they may be. They need 1–5 minute bars.
- TWS was not running during this research, so no new data was downloaded.

## 1. Noise-area intraday momentum (`research/noise_momentum.py`, logs `01_*`)
Rules: bands at open × (1 ± average absolute move from the open at that time of day over 14 days), widened by the overnight gap. Long above the upper band, short below the lower one, checked every 30 min; trailing stop at the band or VWAP; flat at the close; sized to 2% daily volatility, max 4×.

| 1h bars, 2022–2026, 1 bp/side | Sharpe | CAGR | Max DD |
|---|---|---|---|
| SPY | −0.05 | −1.6% | −29% |
| QQQ | 1.04 | 14.3% | −15% |
| DIA | −1.40 | −17.8% | −59% |
| XLK | 1.15 | 15.0% | −13% |
| XLF / XLI | −0.57 / −1.14 | | |

On 30m bars (2024–2026) SPY was −0.91. The published SPY result (Sharpe 1.33, 2007–2024) did not show up in our window. It works only on tech, which trended strongly in this period.

## 2–3. Early-day signals and time-of-day scans (`early_signals.py`, `time_of_day.py`)
- Quintile sorts of market-relative gap, first-30-min move and prior-close → 10:00 move against the rest-of-day return: high-minus-low spreads of 2–10 bp/day, t-stats 0.3–2.1.
- Trading the sign of the move so far (from the open or the prior close) at every half-hour until the close: ETFs and stocks both ≤ 5 bp, none significant. The last half hour after the first move (Gao et al.) was slightly negative.

## 4. Opening range breakout (`orb.py`, logs `04_*`)
Opening range = first 30 minutes. Average R per trade with costs (2 bp/side + $0.005/share), stocks:

| Variant | All stocks | Relative volume > 2.5 |
|---|---|---|
| Breakout, stop at the other side of the range (30m) | −0.01R (0.2 bp) | +0.05R (15.7 bp) |
| Breakout, stop at the range midpoint | −0.25R | −0.13R |
| Breakout, stop 0.1 / 0.25 ATR | −0.79R / −0.22R (bar-resolution artefact) | |
| Direction of the first candle, stop at the range | −0.05R | −0.01R |
| Breakout with a 60-min range | −0.02R | −0.01R |

The published ORB edge (Zarattini, Barbon, Aziz 2024) comes from 5-minute ranges, tight stops and a screen of the most "in play" stocks across the whole US market. None of that can be reproduced on 30-minute bars of 96 large caps.

## 5. Gap fade (`gap_fade.py`, logs `05_*`)
Stocks with 0.5–1.0 ATR gaps reversed after 10:00 by 11–27 bp (t 4–5). Split by the market's own gap, almost all of it comes from days when SPY gapped more than 1% (+38 bp vs 1–5 bp otherwise). Those are a few dozen market-wide days, not thousands of independent trades. By year (1h): 2023 +7 bp, 2024 −2 bp, 2025 +26 bp, 2026 +2 bp. Per-day portfolio Sharpe 0.22 (1h).

## 6. Intraday pairs (`pairs.py`, log `06_*`)
Pairs with a 60-day daily return correlation ≥ 0.8. Trade the spread back towards zero when it moves more than 2 standard deviations during the day; exit at zero or the close. About 8,600 trades; +2.6 bp gross, −1.4 bp after costs. Every variant (z 1.5/2.5, correlation 0.7/0.85, spread from the open) had a negative Sharpe.

## 7. Gap momentum (`gap_momentum.py`, logs `07_*`)
Trade in the gap's direction at 10:00 when the gap is > 1 ATR, stop at the opening range. Stocks: Sharpe −1.3 to +0.3 depending on the variant, with the sign changing year to year. ETFs: positive (Sharpe ~0.6–1.0) but driven by market-wide gap days, mostly in 2025.

## 8. Open-to-close cross-section, 20 years (`oc_cross_section.py`, log `08_*`)
Signals known at the open, return from the open to the close, the 80 stocks in the universe. High-minus-low quintile spread (bp/day) by era:

| Signal | 2007–11 | 2012–16 | 2017–21 | 2022–26 |
|---|---|---|---|---|
| Today's gap | −36.4 | −10.2 | −4.0 | −4.5 |
| Yesterday's open→close | +7.3 | +0.1 | −9.2 | −2.1 |
| 5-day / 20-day / 12-month return, IBS, RSI(2), distance from 200-day MA | | | | all within ±8, t < 2 |

The gap reversal was a strong anomaly before 2012 and has mostly been traded away.

## 9–12. Open-to-close reversal on ETFs (`oc_index.py`, `oc_groups.py`, `reversal_*.py` → `backtest.py`)
Next-day open→close return after yesterday's open→close move, index ETFs (SPY/QQQ/DIA), bp:

| Yesterday's move | 2007–11 | 2012–16 | 2017–21 | 2022–26 |
|---|---|---|---|---|
| < −2% | +29.5 | +66.2 | +47.9 | +45.6 |
| −2% to −1% | +18.9 | 0.0 | +20.0 | +8.0 |
| +1% to +2% | −13.3 | −11.7 | −21.3 | +10.7 |
| > +2% | −4.2 | +18.7 | −34.6 | −31.1 |

Measured in ATRs, after a move above +0.5 ATR, other ETFs fell the next day in every era (−4 to −18 bp). After down days the long side of those ETFs did not work in 2007–2016. Stocks show the same pattern trade by trade, but a stock portfolio lost money: a stock that drops alone usually has news and keeps going, and stock-wide drops are the market signal again.

On the 30m/1h bars the reversal builds through the whole day (about +10 bp by 10:00, +27 bp by the close), so holding until the close is right. The daily open matched the first intraday bar's open on every day checked.

### Final rules (`python -m intraday_reversal.backtest`, log `backtest.txt`)
Index ETFs long and short, other ETFs short only, threshold 0.75 ATR, 0.4% equity risk per ATR, max 200% gross, MOO entry, MOC exit, no stop. 2006-11 → 2026-10, $0.005/share + 1 bp slippage per side:

| | CAGR | Vol | Sharpe | Max DD | Win months | 07–11 | 12–16 | 17–21 | 22–26 |
|---|---|---|---|---|---|---|---|---|---|
| **Default** | **4.5%** | 8.0% | **0.59** | **−11.7%** | 54% | 0.57 | 0.51 | 0.71 | 0.54 |
| Threshold 0.5 / 1.0 / 1.25 | 2.9 / 2.6 / 1.6% | | 0.31 / 0.49 / 0.46 | | | | | | |
| Index only, long + short | 2.3% | 4.6% | 0.53 | −8.8% | 54% | 0.71 | 0.40 | 0.57 | 0.42 |
| Other ETFs long too | 4.3% | 11.2% | 0.43 | −32.0% | 54% | 0.30 | −0.23 | 0.79 | 0.74 |
| Stop 1.0 / 1.5 ATR | 3.3 / 4.0% | | 0.46 / 0.53 | | | | | | |
| Slippage 2 / 3 bp per side | 2.7 / 1.0% | | 0.38 / 0.17 | | | | | | |
| No costs | 8.0% | 8.1% | 0.99 | −8.9% | 59% | | | | |
| No leverage (max gross 1.0) | 3.5% | 6.6% | 0.55 | −10.3% | 54% | | | | |
| SPY buy & hold | 9.1% | 19.5% | 0.54 | −56.5% | 64% | | | | |

- Leaving out any one symbol: Sharpe 0.52–0.64. No single ETF carries it.
- Daily correlation with SPY: −0.11. It tends to make money when the market is falling hard (2008 +11.6%, 2020 +16.9%, 2025 +26.3%).
- A volatility filter (trade only when ATR is high for that ETF) was tested and not adopted. Trades in the calmest quarter averaged −1.4 bp, but the other quarters were not in order (+11.6, +4.8, +21.2 bp) and the split by era was unstable.

## Next steps
1. **5-minute data** (needs TWS running): IBKR serves 5-min bars several years back. It would allow a fair test of the strongest published day-trading results: 5-min ORB on stocks in play, and noise-area momentum at 1–5 minute resolution.
2. **More ETFs** (daily bars are enough): IWM, XLE, XLV, XLY, XLP, XLU, XLB, XBI, KRE, TLT, EEM, EFA… More instruments mean more trades for the reversal strategy, which should smooth its returns.
3. **Paper-trade the reversal** with MOO/MOC orders to measure real fills against the bar open/close. The edge is ~10 bp per trade, so a 2 bp error matters.
