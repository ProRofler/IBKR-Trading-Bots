"""Symbols with cached bars in data/, shared by all strategies. Edit freely, then run
`python -m common.data` to download the new ones.

These lists were built for the EMA touch strategy (ema_touch/STRATEGY.md section 10): successful,
trending instruments. Note for backtests: lists picked today (knowing what trended) overstate
results compared with choosing them at the time.
"""

# Benchmarks for the market filter (ema_touch section 4); also traded
INDEXES = ["SPY", "QQQ", "DIA"]

# Original large-cap list
STOCKS = [
    # Tech
    "AAPL", "MSFT", "NVDA", "AVGO", "AMD", "ORCL", "CRM", "ADBE", "PLTR",
    # Communication / consumer
    "GOOGL", "META", "NFLX", "AMZN", "TSLA", "HD", "COST", "WMT", "KO", "PEP", "PG",
    # Financials
    "JPM", "BAC", "V", "MA",
    # Healthcare
    "LLY", "UNH", "JNJ", "MRK", "ABBV",
    # Energy
    "XOM", "CVX",
]

# Stocks trending since 2022, any size (added 2026-10-28)
TREND_STOCKS = [
    # Semis / hardware
    "MU", "LRCX", "KLAC", "AMAT", "TSM", "ARM", "ANET", "VRT",
    # Software / internet
    "APP", "CRWD", "PANW", "FICO", "SHOP", "MELI", "SPOT", "UBER", "DASH", "RDDT", "NBIS", "CRWV",
    # Fintech / crypto / financials
    "HOOD", "COIN", "MSTR", "NU", "SOFI", "KKR", "APO", "GS",
    # Space / defense / industrials
    "RKLB", "ASTS", "AXON", "GE", "GEV", "HWM", "ETN", "PWR", "TT", "CAT", "URI", "CTAS",
    # Power / utilities
    "CEG", "VST",
    # Consumer / healthcare
    "MNST", "TJX", "RCL", "BKNG", "ORLY", "ISRG", "MCK",
]

# Sector / thematic / commodity ETFs (added 2026-10-28)
ETFS = ["SMH", "SOXX", "XLK", "XLI", "XLF", "ITA", "URA", "GLD", "SLV", "GDX", "MAGS", "DRAM", "IBIT"]

ALL_SYMBOLS = INDEXES + STOCKS + TREND_STOCKS + ETFS

# Ignore bars before these dates: SPAC shells trading near $10 before the merger, and NBIS's
# history as Yandex before its 2022-2024 halt and relisting as a different company.
HISTORY_START = {
    "ASTS": "2021-04-07", "VRT": "2020-02-07", "RKLB": "2021-08-25", "SOFI": "2021-06-01",
    "NBIS": "2024-10-21",
}

# Underlying -> leveraged ETF candidates. Run `python -m common.reference` to verify them in
# IBKR; only verified entries (written to data/reference.json) are used. Review the printed names:
# the check confirms the leverage factor, not that the fund tracks the right underlying.
LEVERAGED_CANDIDATES = {
    "SPY": "SSO", "QQQ": "QLD", "DIA": "DDM",
    "AAPL": "AAPU", "MSFT": "MSFU", "NVDA": "NVDU", "AMZN": "AMZU", "GOOGL": "GGLL",
    "META": "METU", "TSLA": "TSLL", "PLTR": "PLTU", "AVGO": "AVL", "AMD": "AMDL", "LLY": "ELIL",
    "MU": "MUU", "TSM": "TSMX", "COIN": "CONL", "MSTR": "MSTU", "CRWD": "CRWL", "PANW": "PALU",
    "ARM": "ARMG", "HOOD": "HOOX", "APP": "APPX", "RKLB": "RKLX", "SHOP": "SHPU",
    "SMH": "USD", "XLK": "ROM", "XLF": "UYG", "XLI": "UXI", "GLD": "UGL", "SLV": "AGQ", "GDX": "NUGT",
}
