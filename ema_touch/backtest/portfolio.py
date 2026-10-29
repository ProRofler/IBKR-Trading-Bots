"""Phase-2 backtest: replay phase-1 trades through the portfolio rules.

Rules applied (STRATEGY.md): entry filter (4.3), sizing 5%/10% (6), one position per symbol with the
highest timeframe winning ties (7), the adding rule: every open position must already be at breakeven (9),
margin up to max_gross x equity with 2x leveraged ETFs preferred above 100% (5.2).

Simplifications:
- Trade outcomes come from the per-trade simulation; a leveraged position earns factor x the
  underlying's return over the same holding period (daily-reset decay and the 15-day cap are ignored).
- Leveraged ETFs are assumed available over the whole history, though most single-stock ones launched in 2022-2024.
- Position size uses realized equity; the daily equity curve marks open positions to market on daily closes.

Usage:
    python -m ema_touch.backtest.portfolio            # uses results/break1.5_trades.parquet
"""
import argparse
from dataclasses import replace

import numpy as np
import pandas as pd

from common.data import load
from common.reference import load_reference
from common.universe import ALL_SYMBOLS, INDEXES, STOCKS
from ema_touch.backtest.run import RESULTS_DIR
from ema_touch.bot.params import DEFAULT, TIMEFRAMES, Params
from ema_touch.bot.rules import entry_allowed, position_size

START_EQUITY = 1_000_000.0


def stop_level(pos: dict, t) -> float:
    """The position's stop at time t, as a ratio to its entry price."""
    i = np.searchsorted(pos["stop_times"], t.value, side="right") - 1
    return pos["stop_levels"][max(i, 0)]


def risk_and_locked(pos: dict, t) -> tuple[float, float]:
    """Dollars lost if the stop is hit (open risk), and dollars kept if it is (locked profit)."""
    level = stop_level(pos, t)
    remaining = 0.5 if pd.notna(pos["partial_time"]) and pos["partial_time"] <= t else 1.0
    exposure = pos["dollars"] * pos["factor"] * remaining
    return exposure * max(0.0, 1 - level), exposure * max(0.0, level - 1)


def adding_allowed(open_pos: list[dict], t, p: Params) -> bool:
    if p.adding_rule == "strict":
        return all(stop_level(pos, t) >= 1 for pos in open_pos)
    if p.adding_rule == "count":
        return sum(stop_level(pos, t) < 1 for pos in open_pos) <= p.max_at_risk
    risk, locked = (sum(x) for x in zip(*(risk_and_locked(pos, t) for pos in open_pos))) if open_pos else (0, 0)
    return risk <= p.buffer_ratio * locked


def simulate_portfolio(trades: pd.DataFrame, start, p: Params = DEFAULT,
                       seed: int | None = None) -> tuple[pd.DataFrame, pd.Series]:
    """With seed, signals arriving at the same time are taken in a random symbol order instead of
    the data's order (a robustness check: which symbol gets the capital first is arbitrary)."""
    leveraged = {u: v["factor"] for u, v in load_reference()["leveraged"].items()}
    c = trades[entry_allowed(trades, p) & (trades.time >= start) & trades.period.isin(p.entry_periods)].copy()
    c["size"] = position_size(c, p)
    c["ret"] = c.r * c.risk_pct  # net return on the underlying
    c["tf_rank"] = c.tf.map({tf: i for i, tf in enumerate(TIMEFRAMES)})
    c["order"] = 0.0
    if seed is not None:
        rng = np.random.default_rng(seed)
        keys = pd.DataFrame({"time": c.time, "symbol": c.symbol}).drop_duplicates()
        keys["order"] = rng.random(len(keys))
        c = c.drop(columns="order").merge(keys, on=["time", "symbol"], how="left")
    keys = ["time", "tf_rank", "period", "order"] if p.signal_priority == "quality" else ["time", "order", "tf_rank", "period"]
    ascending = [k in ("time", "order") for k in keys]
    c = c.sort_values(keys, ascending=ascending, kind="stable")

    realized = START_EQUITY
    open_pos: list[dict] = []
    log = []
    for row in c.itertuples():
        t = row.time
        for pos in [pos for pos in open_pos if pos["exit_time"] <= t]:
            realized += pos["pnl"]
            open_pos.remove(pos)

        decision = {"time": t, "symbol": row.symbol, "tf": row.tf, "ma": f"{row.ma_type}{row.period}"}
        dollars = row.size * realized
        lots = [pos for pos in open_pos if pos["symbol"] == row.symbol]
        if lots:
            can_add = (
                len(lots) < p.max_lots
                and all(stop_level(pos, t) >= 1 for pos in lots)
                and sum(pos["dollars"] for pos in lots) + dollars <= p.max_symbol_exposure * realized
            )
            if not can_add:
                log.append({**decision, "action": "skip_symbol_held"})
                continue
        if not adding_allowed(open_pos, t, p):
            log.append({**decision, "action": "skip_adding_rule"})
            continue
        gross = sum(pos["dollars"] for pos in open_pos)
        if gross + dollars > p.max_gross * realized:
            log.append({**decision, "action": "skip_margin"})
            continue
        factor = 1.0
        if gross + dollars > p.leverage_above * realized and row.symbol in leveraged and row.tf not in p.no_leverage_tfs:
            factor = leveraged[row.symbol]
        pos = {
            **decision, "action": "add" if lots else "enter", "size": row.size, "dollars": dollars,
            "factor": factor, "entry": row.entry, "entry_time": row.entry_time, "exit_time": row.exit_time,
            "be_time": row.be_time, "partial_time": row.partial_time,
            "stop_times": np.asarray(row.stop_times), "stop_levels": np.asarray(row.stop_levels),
            "r": row.r, "pnl": dollars * factor * row.ret,
            "margin": gross + dollars > p.leverage_above * realized,
        }
        open_pos.append(pos)
        log.append(pos)
    log = pd.DataFrame(log).drop(columns=["stop_times", "stop_levels"], errors="ignore")
    return log, equity_curve(log[log.action.isin(["enter", "add"])], start)


def equity_curve(positions: pd.DataFrame, start) -> pd.Series:
    """Daily equity: realized P&L plus open positions marked to market on daily closes."""
    days = load("SPY", "1d").index
    days = days[days >= start]
    equity = pd.Series(START_EQUITY, index=days)
    closes = {s: load(s, "1d")["close"].reindex(days).ffill() for s in positions.symbol.unique()}
    for pos in positions.itertuples():
        exit_day = days.searchsorted(pos.exit_time)  # first day at/after exit
        held = days >= pos.entry_time
        if exit_day < len(days):
            equity.iloc[exit_day:] += pos.pnl
            held &= days < days[exit_day]
        if held.any():
            mtm = pos.dollars * pos.factor * (closes[pos.symbol][held] / pos.entry - 1)
            equity[held] += mtm.fillna(0).to_numpy()
    return equity


def stats(equity: pd.Series) -> dict:
    years = (equity.index[-1] - equity.index[0]).days / 365.25
    daily = equity.pct_change().dropna()
    return {
        "CAGR": (equity.iloc[-1] / equity.iloc[0]) ** (1 / years) - 1,
        "max_drawdown": (equity / equity.cummax() - 1).min(),
        "sharpe": daily.mean() / daily.std() * np.sqrt(252) if daily.std() else float("nan"),
        "final_x": equity.iloc[-1] / equity.iloc[0],
    }


def avg_exposure(log: pd.DataFrame, equity: pd.Series) -> float:
    """Average of (sum of open positions' entry dollars x leverage) / equity over all days."""
    pos = log[log.action.isin(["enter", "add"])]
    gross = pd.Series(0.0, index=equity.index)
    for x in pos.itertuples():
        gross[(equity.index >= x.entry_time) & (equity.index < x.exit_time)] += x.dollars * x.factor
    return (gross / equity).mean()


def report(log: pd.DataFrame, equity: pd.Series, label: str) -> None:
    pos = log[log.action.isin(["enter", "add"])]
    spy = load("SPY", "1d")["close"].reindex(equity.index).ffill()
    print(f"\n##### Portfolio: {label} ({equity.index[0]:%Y-%m-%d} -> {equity.index[-1]:%Y-%m-%d}) #####")
    print(pd.DataFrame({"strategy": stats(equity), "SPY buy & hold": stats(spy)}).T.to_string(float_format=lambda x: f"{x:.3f}"))
    print("\nDecisions:", log.action.value_counts().to_dict())
    print(f"Positions: {len(pos)}, at 10% size: {(pos['size'] > 0.05).mean():.0%}, "
          f"on margin: {pos['margin'].mean():.0%}, leveraged ETF: {(pos.factor > 1).mean():.0%}")
    print("By timeframe:", pos.groupby("tf").size().reindex(TIMEFRAMES).fillna(0).astype(int).to_dict())
    yearly = pd.DataFrame({
        "strategy": equity.resample("YE").last().pct_change().fillna(equity.resample("YE").last().iloc[0] / START_EQUITY - 1),
        "SPY": spy.resample("YE").last().pct_change().fillna(spy.resample("YE").last().iloc[0] / spy.iloc[0] - 1),
    })
    yearly.index = yearly.index.year
    print("\nYearly returns:")
    print(yearly.T.to_string(float_format=lambda x: f"{x:+.0%}"))


VARIANTS = {
    "default": DEFAULT,  # buffer 2x + adding to winners
    "strict": replace(DEFAULT, adding_rule="strict", max_lots=1),
    "no_leveraged_etfs": replace(DEFAULT, leverage_above=99.0),
    "no_margin": replace(DEFAULT, max_gross=1.0),
}
WINDOWS = {"full": "2007-01-01", "since2022": "2022-01-01", "last2y": "2024-11-01"}
UNIVERSES = {"all": ALL_SYMBOLS, "original": INDEXES + STOCKS}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trades", default="default", help="results/<name>_trades.parquet from backtest.run")
    parser.add_argument("--detail", nargs="*", default=[], help="variants to print a full report for")
    parser.add_argument("--universe", choices=list(UNIVERSES), default="all")
    args = parser.parse_args()
    trades = pd.read_parquet(RESULTS_DIR / f"{args.trades}_trades.parquet")
    trades = trades[trades.symbol.isin(UNIVERSES[args.universe])]

    for window, start in WINDOWS.items():
        start = pd.Timestamp(start, tz="UTC")
        rows = {}
        for name, p in VARIANTS.items():
            log, equity = simulate_portfolio(trades, start, p)
            prefix = f"portfolio_{args.trades}_{args.universe}_{name}_{window}"
            log.to_csv(RESULTS_DIR / f"{prefix}_log.csv", index=False)
            equity.to_csv(RESULTS_DIR / f"{prefix}_equity.csv")
            taken = log[log.action.isin(["enter", "add"])]
            rows[name] = {
                **stats(equity), "avg_exposure": avg_exposure(log, equity),
                "positions": (log.action == "enter").sum(), "adds": (log.action == "add").sum(),
                "on_margin": taken.margin.mean(), "leveraged": (taken.factor > 1).mean(),
            }
            if name in args.detail:
                report(log, equity, f"{name}, {window}")
        spy = load("SPY", "1d")["close"]
        rows["SPY buy & hold"] = stats(spy[spy.index >= start])
        print(f"\n===== {window} ({start:%Y-%m-%d} ->) =====")
        print(pd.DataFrame(rows).T.to_string(float_format=lambda x: f"{x:.3f}"))


if __name__ == "__main__":
    main()
