"""Fetch reference data from IBKR: each symbol's sector, and which leveraged ETF candidates exist.

Usage:
    python -m common.reference
Writes data/reference.json and prints the leveraged ETF names for review.
"""
import json
import re

from ib_async import Stock

from common.data import DATA_DIR
from common.connection import connect
from common.universe import ALL_SYMBOLS, LEVERAGED_CANDIDATES

REFERENCE_PATH = DATA_DIR / "reference.json"


def load_reference() -> dict:
    return json.loads(REFERENCE_PATH.read_text())


def main():
    ib = connect(client_id=91)
    ref = {"sectors": {}, "leveraged": {}}
    try:
        for symbol in ALL_SYMBOLS:
            details = ib.reqContractDetails(Stock(symbol, "SMART", "USD"))
            ref["sectors"][symbol] = details[0].industry if details else None
            if not details:
                print(f"NOT FOUND in IBKR: {symbol}")
            elif len(details) > 1:
                print(f"ambiguous ({len(details)} contracts): {symbol}")

        for underlying, etf in LEVERAGED_CANDIDATES.items():
            details = ib.reqContractDetails(Stock(etf, "SMART", "USD"))
            name = details[0].longName if details else ""
            match = re.search(r"(\d(?:\.\d+)?)X", name.upper())
            # ProShares names 2x funds "ULTRA" and 3x funds "ULTRAPRO"
            factor = float(match.group(1)) if match else 3.0 if "ULTRAPRO" in name.upper() else 2.0 if "ULTRA" in name.upper() else None
            ok = bool(details) and factor is not None
            print(f"{underlying:6} -> {etf:6} {f'{factor:g}x' if ok else '???'} {name}")
            if ok:
                ref["leveraged"][underlying] = {"etf": etf, "factor": factor, "name": name}
    finally:
        ib.disconnect()

    REFERENCE_PATH.write_text(json.dumps(ref, indent=2))
    print("\nSectors:", ref["sectors"])


if __name__ == "__main__":
    main()
