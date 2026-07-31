"""Popular tickers for search suggestions."""

from __future__ import annotations

POPULAR_TICKERS: list[dict[str, str]] = [
    {"ticker": "600519.SS", "name": "贵州茅台", "market": "沪A"},
    {"ticker": "000001.SZ", "name": "平安银行", "market": "深A"},
    {"ticker": "300750.SZ", "name": "宁德时代", "market": "深A"},
    {"ticker": "0700.HK", "name": "腾讯控股", "market": "港股"},
    {"ticker": "9988.HK", "name": "阿里巴巴", "market": "港股"},
    {"ticker": "NVDA", "name": "英伟达", "market": "美股"},
    {"ticker": "AAPL", "name": "苹果", "market": "美股"},
    {"ticker": "TSLA", "name": "特斯拉", "market": "美股"},
    {"ticker": "MSFT", "name": "微软", "market": "美股"},
    {"ticker": "BTC-USD", "name": "比特币", "market": "Crypto"},
]
