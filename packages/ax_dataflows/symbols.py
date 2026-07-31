"""A-share symbol helpers."""

from __future__ import annotations

import re

_A_SHARE_SUFFIX = (".SS", ".SH", ".SZ")
_A_SHARE_BARE = re.compile(r"^\d{6}$")


def is_a_share(ticker: str) -> bool:
    t = ticker.strip().upper()
    if any(t.endswith(s) for s in _A_SHARE_SUFFIX):
        return True
    return bool(_A_SHARE_BARE.match(t))


def to_akshare_code(ticker: str) -> str:
    """Return 6-digit A-share code for AKShare APIs."""
    t = ticker.strip().upper()
    for suffix in _A_SHARE_SUFFIX:
        if t.endswith(suffix):
            return t[: -len(suffix)]
    if _A_SHARE_BARE.match(t):
        return t
    raise ValueError(f"Not an A-share ticker: {ticker!r}")


def to_em_market_symbol(ticker: str) -> str:
    """East Money symbol with market suffix, e.g. ``600519.SH``."""
    code = to_akshare_code(ticker)
    if code.startswith(("5", "6", "9")):
        return f"{code}.SH"
    return f"{code}.SZ"


def to_em_exchange_prefix(ticker: str) -> str:
    """East Money exchange-prefixed symbol, e.g. ``SH600519``."""
    code = to_akshare_code(ticker)
    if code.startswith(("5", "6", "9")):
        return f"SH{code}"
    return f"SZ{code}"


def to_tx_symbol(ticker: str) -> str:
    """Tencent Finance symbol, e.g. ``sh600519`` / ``sz000001``."""
    return to_em_exchange_prefix(ticker).lower()
