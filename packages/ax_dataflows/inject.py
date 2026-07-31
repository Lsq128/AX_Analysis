"""Inject A-share vendor configuration into engine config."""

from __future__ import annotations

from typing import Any

from ax_dataflows.symbols import is_a_share


def apply_a_share_vendors(config: dict[str, Any], ticker: str) -> dict[str, Any]:
    """Prefer AKShare for Shanghai/Shenzhen listings; yfinance as fallback."""
    if not is_a_share(ticker):
        return config

    updated = config.copy()
    vendors = dict(updated.get("data_vendors") or {})
    chain = "akshare,yfinance"
    vendors["core_stock_apis"] = chain
    vendors["technical_indicators"] = chain
    vendors["fundamental_data"] = chain
    vendors["news_data"] = chain
    updated["data_vendors"] = vendors

    queries = list(updated.get("global_news_queries") or [])
    cn_queries = [
        "中国人民银行 利率 货币政策",
        "A股 宏观经济 PMI CPI",
        "证监会 监管 政策",
        "沪深 流动性 北向资金",
    ]
    if not any("A股" in q or "央行" in q for q in queries):
        updated["global_news_queries"] = cn_queries + queries[:3]

    return updated
