"""Indicator calculations on OHLC DataFrames (columns: open, high, low, close)."""
import pandas as pd


def sma(s: pd.Series, n: int) -> pd.Series:
    return s.rolling(n, min_periods=n).mean()


def ema(s: pd.Series, n: int) -> pd.Series:
    out = s.ewm(span=n, adjust=False).mean()
    out.iloc[: n - 1] = float("nan")  # not meaningful until n bars exist
    return out


def ma(s: pd.Series, kind: str, n: int) -> pd.Series:
    return sma(s, n) if kind == "SMA" else ema(s, n)


def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    """Wilder's average true range."""
    prev_close = df["close"].shift()
    tr = pd.concat(
        [df["high"] - df["low"], (df["high"] - prev_close).abs(), (df["low"] - prev_close).abs()],
        axis=1,
    ).max(axis=1)
    out = tr.ewm(alpha=1 / n, adjust=False).mean()
    out.iloc[:n] = float("nan")
    return out


def rsi(s: pd.Series, n: int = 14) -> pd.Series:
    """Wilder's relative strength index."""
    delta = s.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    out = 100 - 100 / (1 + gain / loss)
    out.iloc[:n] = float("nan")
    return out
