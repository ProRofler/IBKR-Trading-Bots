"""Entry filter and position sizing rules (STRATEGY.md sections 4.3 and 6), shared by backtest and live bot."""
import pandas as pd

from ema_touch.bot.params import DEFAULT, Params


def entry_allowed(signals: pd.DataFrame, p: Params = DEFAULT) -> pd.Series:
    """SPY counter-signals block everything; short timeframes also need SPY confluence; the optional
    trend screen needs the symbol itself in a daily uptrend."""
    needs_confluence = signals["tf"].isin(p.confluence_required_tfs)
    allowed = ~signals["spy_counter"] & (~needs_confluence | signals["spy_touch"])
    if p.trend_filter != "off":
        allowed &= signals[f"trend_{p.trend_filter}"].fillna(False).astype(bool)
    return allowed


def position_size(signals: pd.DataFrame, p: Params = DEFAULT) -> pd.Series:
    """Fraction of equity: size_confluence with SPY confluence, else (or with a QQQ (tech only) or DIA
    counter-signal) size_base."""
    capped = signals["dia_counter"] | (signals["is_tech"] & signals["qqq_counter"])
    big = signals["spy_touch"] & ~capped
    return big.map({True: p.size_confluence, False: p.size_base})
