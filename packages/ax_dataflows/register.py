"""Register AX data vendors with tradingagents routing."""

from __future__ import annotations

from typing import Any

from ax_dataflows.vendors.fundamentals import (
    get_akshare_balance_sheet,
    get_akshare_cashflow,
    get_akshare_fundamentals,
    get_akshare_income_statement,
)
from ax_dataflows.vendors.indicators import get_akshare_indicators
from ax_dataflows.vendors.news import get_akshare_global_news, get_akshare_news
from ax_dataflows.vendors.stock import get_akshare_stock_data


def register_vendors(vendor_methods: dict[str, dict[str, Any]], vendor_list: list[str]) -> None:
    if "akshare" not in vendor_list:
        vendor_list.append("akshare")

    vendor_methods.setdefault("get_stock_data", {})["akshare"] = get_akshare_stock_data
    vendor_methods.setdefault("get_indicators", {})["akshare"] = get_akshare_indicators
    vendor_methods.setdefault("get_fundamentals", {})["akshare"] = get_akshare_fundamentals
    vendor_methods.setdefault("get_balance_sheet", {})["akshare"] = get_akshare_balance_sheet
    vendor_methods.setdefault("get_cashflow", {})["akshare"] = get_akshare_cashflow
    vendor_methods.setdefault("get_income_statement", {})["akshare"] = get_akshare_income_statement
    vendor_methods.setdefault("get_news", {})["akshare"] = get_akshare_news
    vendor_methods.setdefault("get_global_news", {})["akshare"] = get_akshare_global_news
