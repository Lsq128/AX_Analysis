"""Ticker normalization and asset classification (ported from cli/utils.py)."""

from __future__ import annotations

from ax_engine.models import AnalystType, AssetType

CRYPTO_SUFFIXES = ("-USD", "-USDT", "-USDC", "-BTC", "-ETH")


def is_valid_ticker_input(value: str) -> bool:
    v = value.strip()
    return not v or (all(ch.isalnum() or ch in "._-^=" for ch in v) and len(v) <= 32)


def normalize_ticker_symbol(ticker: str) -> str:
    try:
        from tradingagents.dataflows.symbol_utils import normalize_symbol

        return normalize_symbol(ticker)
    except Exception:
        return ticker.strip().upper()


def detect_asset_type(ticker: str) -> AssetType:
    canonical = normalize_ticker_symbol(ticker)
    if canonical.endswith(CRYPTO_SUFFIXES):
        return AssetType.CRYPTO
    return AssetType.STOCK


def filter_analysts_for_asset_type(
    analysts: list[str | AnalystType], asset_type: AssetType | str
) -> list[str]:
    if isinstance(asset_type, AssetType):
        asset_type = asset_type.value
    keys = [
        a.value if isinstance(a, AnalystType) else a
        for a in analysts
    ]
    if asset_type != AssetType.CRYPTO.value:
        return keys
    return [k for k in keys if k != AnalystType.FUNDAMENTALS.value]


def order_analyst_keys(analysts: list[str]) -> list[str]:
    from ax_engine.models import ANALYST_ORDER

    selected = set(analysts)
    return [k for k in ANALYST_ORDER if k in selected]
