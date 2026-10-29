"""Backtest of the intraday reversal strategy on daily bars (enter at the open, exit at the close).

Usage (from the project root):
    python -m intraday_reversal.backtest            # default rules + variants and robustness tables
    python -m intraday_reversal.backtest --quick    # default rules only
Writes results/trades.parquet and results/daily.csv for the default rules.
"""
import argparse
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

from intraday_reversal.params import DEFAULT, INDEX, SHORT_ONLY, Params
from intraday_reversal.signals import add_signal, daily_bars

RESULTS_DIR = Path(__file__).resolve().parent / "results"
ERAS = [("2007", "2011"), ("2012", "2016"), ("2017", "2021"), ("2022", "2026")]
_bars = {}


def bars(symbol: str) -> pd.DataFrame:
    if symbol not in _bars:
        _bars[symbol] = daily_bars(symbol)
    return _bars[symbol]


def trades(p: Params = DEFAULT) -> pd.DataFrame:
    rows = []
    for s in sorted(set(p.long_symbols) | set(p.short_symbols)):
        d = add_signal(bars(s), p)
        d = d[((d.direction == 1) & (s in p.long_symbols)) | ((d.direction == -1) & (s in p.short_symbols))]
        t = pd.DataFrame({"symbol": s, "direction": d.direction, "move": d.move, "atr_pct": d.atr / d.open,
                          "open": d.open, "close": d.close, "high": d.high, "low": d.low})
        rows.append(t)
    t = pd.concat(rows).reset_index()
    t["ret"] = t.direction * (t.close / t.open - 1)
    if p.stop_atr:
        stop = p.stop_atr * t.atr_pct
        hit = np.where(t.direction == 1, t.low / t.open - 1 <= -stop, t.high / t.open - 1 >= stop)
        t["ret"] = np.where(hit, -stop - p.slippage_pct, t.ret)
    t["net"] = t.ret - 2 * (p.commission_per_share / t.open + p.slippage_pct)
    # sizing: a 1-ATR move costs risk_per_trade of equity, capped per position and in total
    t["weight"] = np.minimum(p.max_position, p.risk_per_trade / t.atr_pct)
    gross = t.groupby("day").weight.transform("sum")
    t["weight"] *= np.minimum(1, p.max_gross / gross)
    t["pnl"] = t.weight * t.net
    return t


def daily_returns(t: pd.DataFrame) -> pd.Series:
    """Portfolio return per trading day (0 on days without trades)."""
    return t.groupby("day").pnl.sum().reindex(bars("SPY").index).fillna(0)


def stats(r: pd.Series) -> dict:
    eq = (1 + r).cumprod()
    years = len(r) / 252
    dd = (eq / eq.cummax() - 1).min()
    monthly = (1 + r).groupby(r.index.to_period("M")).prod() - 1
    yearly = (1 + r).groupby(r.index.year).prod() - 1
    active = r[r != 0]
    return dict(cagr=round((eq.iloc[-1] ** (1 / years) - 1) * 100, 1), vol=round(r.std() * np.sqrt(252) * 100, 1),
                sharpe=round(r.mean() / r.std() * np.sqrt(252), 2), max_dd=round(dd * 100, 1),
                win_days=round((active > 0).mean() * 100), win_months=round((monthly > 0).mean() * 100),
                win_years=round((yearly > 0).mean() * 100), worst_month=round(monthly.min() * 100, 1))


def era_sharpes(r: pd.Series) -> dict:
    out = {}
    for a, b in ERAS:
        x = r[(r.index >= pd.Timestamp(a)) & (r.index < pd.Timestamp(str(int(b) + 1)))]
        out[f"{a[2:]}-{b[2:]}"] = round(x.mean() / x.std() * np.sqrt(252), 2)
    return out


def row(name: str, p: Params) -> dict:
    t = trades(p)
    r = daily_returns(t)
    days_in = (t.groupby("day").weight.sum() > 0).sum() / len(r)
    return dict(name=name) | stats(r) | dict(trades=len(t), net_bp=round(t.net.mean() * 1e4, 1),
                                             days_in=round(days_in * 100), avg_gross=round(t.groupby("day").weight.sum().mean(), 2)) \
        | era_sharpes(r)


def spy_buy_hold() -> dict:
    c = bars("SPY").close
    r = c.pct_change().fillna(0)
    return dict(name="SPY buy & hold (close to close)") | stats(r) | era_sharpes(r)


VARIANTS = {
    "default": DEFAULT,
    "threshold 0.5": replace(DEFAULT, threshold_atr=0.5),
    "threshold 1.0": replace(DEFAULT, threshold_atr=1.0),
    "threshold 1.25": replace(DEFAULT, threshold_atr=1.25),
    "index only, long+short": replace(DEFAULT, short_symbols=INDEX),
    "index only, long": replace(DEFAULT, short_symbols=()),
    "shorts only": replace(DEFAULT, long_symbols=()),
    "other ETFs long too": replace(DEFAULT, long_symbols=INDEX + SHORT_ONLY),
    "stop 1.0 ATR": replace(DEFAULT, stop_atr=1.0),
    "stop 1.5 ATR": replace(DEFAULT, stop_atr=1.5),
    "slippage 2 bp/side": replace(DEFAULT, slippage_pct=0.0002),
    "slippage 3 bp/side": replace(DEFAULT, slippage_pct=0.0003),
    "no costs": replace(DEFAULT, slippage_pct=0, commission_per_share=0),
    "half size (risk 0.2%)": replace(DEFAULT, risk_per_trade=0.002),
    "no leverage (max gross 1.0)": replace(DEFAULT, max_gross=1.0),
}


def leave_one_out() -> pd.DataFrame:
    rows = []
    for s in INDEX + SHORT_ONLY:
        p = replace(DEFAULT, long_symbols=tuple(x for x in DEFAULT.long_symbols if x != s),
                    short_symbols=tuple(x for x in DEFAULT.short_symbols if x != s))
        rows.append(row(f"without {s}", p))
    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 30)
    RESULTS_DIR.mkdir(exist_ok=True)

    t = trades(DEFAULT)
    r = daily_returns(t)
    t.to_parquet(RESULTS_DIR / "trades.parquet")
    r.to_csv(RESULTS_DIR / "daily.csv")
    print(f"Default rules, {r.index[0]:%Y-%m-%d} -> {r.index[-1]:%Y-%m-%d}")
    print(pd.DataFrame([row("default", DEFAULT), spy_buy_hold()]).to_string(index=False))
    yearly = ((1 + r).groupby(r.index.year).prod() - 1) * 100
    spy = bars("SPY").close.pct_change().fillna(0)
    spy_y = ((1 + spy).groupby(spy.index.year).prod() - 1) * 100
    print("\nBy year, % return (strategy | SPY):")
    print(pd.DataFrame({"strategy": yearly.round(1), "SPY": spy_y.round(1)}).T.to_string())
    print(f"\nCorrelation of daily returns with SPY open->close: "
          f"{r.corr((bars('SPY').close / bars('SPY').open - 1).reindex(r.index)):.2f}, close->close: {r.corr(spy.reindex(r.index)):.2f}")
    print("\nBy symbol and side:")
    g = t.groupby(["symbol", "direction"]).agg(trades=("net", "size"), net_bp=("net", lambda x: x.mean() * 1e4),
                                               win=("net", lambda x: (x > 0).mean() * 100), pnl=("pnl", "sum"))
    print(g.round(1).unstack("direction").to_string())
    if args.quick:
        return

    print("\nVariants (one change from default each):")
    v = pd.DataFrame([row(name, p) for name, p in VARIANTS.items()])
    print(v.to_string(index=False))
    v.to_csv(RESULTS_DIR / "variants.csv", index=False)

    print("\nLeave one symbol out:")
    loo = leave_one_out()
    print(loo.to_string(index=False))
    loo.to_csv(RESULTS_DIR / "leave_one_out.csv", index=False)


if __name__ == "__main__":
    main()
