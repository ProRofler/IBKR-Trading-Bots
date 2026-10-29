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

# Big, liquid names in steady but unspectacular uptrends (added 2026-10-29), to test the strategy on
# more ordinary stocks than the trend list. Daily and weekly bars only.
STEADY_STOCKS = [
    # Financials
    "MS", "AXP", "BLK", "SPGI", "MCO", "ICE", "CME", "PGR", "CB", "TRV",
    # Industrials / defense / services
    "HON", "UNP", "LMT", "RTX", "NOC", "GD", "DE", "WM", "RSG", "ADP",
    # Consumer
    "MCD", "LOW", "CL", "MDLZ", "YUM", "PM",
    # Healthcare
    "ABT", "TMO", "DHR", "SYK", "BSX", "AMGN", "GILD", "VRTX", "REGN", "ZTS",
    # Tech
    "CSCO", "IBM", "TXN", "QCOM", "INTU", "ACN", "ADI", "MSI", "APH", "NOW",
    # Utilities / telecom / energy / real estate
    "NEE", "SO", "DUK", "TMUS", "COP", "EOG", "PLD", "AMT",
]

# The 96 symbols of runs 8-13, before STEADY_STOCKS
PREVIOUS_SYMBOLS = INDEXES + STOCKS + TREND_STOCKS + ETFS
ALL_SYMBOLS = PREVIOUS_SYMBOLS + STEADY_STOCKS

# Extra liquid names for day trading research (added 2026-10-29), deliberately including stocks that
# fell or went sideways since 2022, so a scanner is not tested only on past winners. Kept out of
# ALL_SYMBOLS so ema_touch results don't change. Daily bars: `python -m common.data --symbols ...
# --timeframes 1d`; intraday bars: `python -m common.intraday`.
DAYTRADE_EXTRA = [
    # Tech / semis
    "INTC", "QCOM", "MRVL", "SMCI", "CSCO", "IBM", "TXN",
    # Software / internet
    "SNOW", "NET", "DDOG", "ZS", "MDB", "TTD", "ABNB", "PYPL", "SNAP", "PINS", "ROKU", "ZM", "DOCU",
    "U", "AFRM", "UPST", "DKNG",
    # Autos
    "RIVN", "LCID", "F", "GM", "NIO",
    # Consumer
    "NKE", "SBUX", "TGT", "LULU", "DIS", "CMG", "MCD",
    # Healthcare
    "PFE", "MRNA", "CVS", "BMY",
    # Travel
    "AAL", "UAL", "DAL", "CCL",
    # Energy / industrials
    "OXY", "SLB", "BA", "ENPH",
    # Financials / crypto miners
    "WFC", "C", "SCHW", "MARA", "RIOT",
    # China
    "BABA", "PDD",
    # ETFs
    "IWM", "XLE", "XLV", "TLT", "XBI",
]
DAYTRADE_SYMBOLS = ALL_SYMBOLS + DAYTRADE_EXTRA

# Ignore bars before these dates: SPAC shells trading near $10 before the merger, NBIS's history as
# Yandex before its 2022-2024 halt and relisting as a different company, and holes in IBKR's history
# (CME: 2007-07 to 2008-07 missing; TMUS: 2013-04 to 2015-10 missing, MetroPCS before that).
HISTORY_START = {
    "ASTS": "2021-04-07", "VRT": "2020-02-07", "RKLB": "2021-08-25", "SOFI": "2021-06-01",
    "NBIS": "2024-10-21", "LCID": "2021-07-26", "DKNG": "2020-04-24",
    "CME": "2008-07-14", "TMUS": "2015-10-27",
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
