"""Strategy parameters. Values mirror STRATEGY.md."""
from dataclasses import dataclass

# Index ETFs: traded both ways. Other ETFs: short only (their long side lost money in 2007-2016).
INDEX = ("SPY", "QQQ", "DIA")
SHORT_ONLY = ("SMH", "SOXX", "XLK", "XLI", "XLF", "ITA", "URA", "GLD", "SLV", "GDX", "MAGS", "DRAM", "IBIT")


@dataclass(frozen=True)
class Params:
    atr_period: int = 14
    threshold_atr: float = 0.75     # yesterday's open->close move, in daily ATRs, that triggers a trade
    long_symbols: tuple = INDEX
    short_symbols: tuple = INDEX + SHORT_ONLY

    # Sizing: a 1-ATR move against a position costs risk_per_trade of equity
    risk_per_trade: float = 0.004
    max_position: float = 0.5       # of equity, per symbol
    max_gross: float = 2.0          # of equity, all positions together (IBKR intraday buying power is 4x)

    stop_atr: float = 0.0           # 0 = no stop; stops cut the edge in every test (RESEARCH.md)

    # Costs per side (backtest only). Market-on-open/close orders fill in the auction, so there is
    # no spread to cross; slippage covers the gap between our fill and the bar's open/close.
    # Commission is per share on split-adjusted prices, which overstates it before a split (conservative).
    commission_per_share: float = 0.005  # IBKR fixed rate, exchange fees included
    slippage_pct: float = 0.0001


DEFAULT = Params()
