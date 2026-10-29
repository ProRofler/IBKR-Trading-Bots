"""Shared helper for connecting to TWS with the paper-account safety guard."""
from ib_async import IB

from common import config


def connect(client_id: int | None = None) -> IB:
    ib = IB()
    ib.connect(
        config.TWS_HOST,
        config.TWS_PORT,
        clientId=client_id if client_id is not None else config.TWS_CLIENT_ID,
        timeout=10,
    )
    accounts = ib.managedAccounts()
    # IBKR paper accounts start with "DU" (individual) or "DF" (advisor)
    if config.PAPER_ONLY and not all(a.startswith(("DU", "DF")) for a in accounts):
        ib.disconnect()
        raise RuntimeError(f"Refusing to run: non-paper account(s) detected {accounts}")
    return ib
