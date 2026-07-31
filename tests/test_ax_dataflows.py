"""Tests for ax_dataflows A-share adapters."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
for sub in ("services/ai_server", "packages"):
    p = str(ROOT / sub)
    if p not in sys.path:
        sys.path.insert(0, p)

from ax_dataflows.inject import apply_a_share_vendors
from ax_dataflows.symbols import is_a_share, to_akshare_code
from ax_engine.build_config import build_config
from ax_engine.models import AnalysisRequest


def test_is_a_share():
    assert is_a_share("600519.SS")
    assert is_a_share("000001.SZ")
    assert is_a_share("600519")
    assert not is_a_share("AAPL")
    assert not is_a_share("0700.HK")


def test_to_akshare_code():
    assert to_akshare_code("600519.SS") == "600519"
    assert to_akshare_code("000001.sz") == "000001"


def test_apply_a_share_vendors():
    cfg = {"data_vendors": {"core_stock_apis": "yfinance"}, "global_news_queries": ["US only"]}
    out = apply_a_share_vendors(cfg, "600519.SS")
    assert out["data_vendors"]["core_stock_apis"] == "akshare,yfinance"
    assert out["data_vendors"]["fundamental_data"] == "akshare,yfinance"
    assert out["data_vendors"]["news_data"] == "akshare,yfinance"
    assert any("A股" in q for q in out["global_news_queries"])


def test_build_config_injects_for_maotai(monkeypatch):
    monkeypatch.delenv("TRADINGAGENTS_MAX_DEBATE_ROUNDS", raising=False)
    monkeypatch.delenv("TRADINGAGENTS_MAX_RISK_ROUNDS", raising=False)
    req = AnalysisRequest(ticker="600519.SS", analysis_date="2026-07-29", analysts=["market"], research_depth=1)
    config, _ = build_config(req)
    assert config["data_vendors"]["core_stock_apis"] == "akshare,yfinance"
    assert config["data_vendors"]["fundamental_data"] == "akshare,yfinance"
    assert config["data_vendors"]["news_data"] == "akshare,yfinance"


def test_em_symbol_helpers():
    assert to_akshare_code("600519.SS") == "600519"
    from ax_dataflows.symbols import to_em_exchange_prefix, to_em_market_symbol, to_tx_symbol

    assert to_em_market_symbol("600519.SS") == "600519.SH"
    assert to_em_market_symbol("000001.SZ") == "000001.SZ"
    assert to_em_exchange_prefix("600519.SS") == "SH600519"
    assert to_em_exchange_prefix("000001.SZ") == "SZ000001"
    assert to_tx_symbol("600519.SS") == "sh600519"
    assert to_tx_symbol("000001.SZ") == "sz000001"


@patch("ax_dataflows.vendors.stock.require_akshare")
def test_get_akshare_stock_data_tencent_first(mock_ak):
    dates = pd.date_range("2026-07-21", periods=5, freq="B")
    sample = pd.DataFrame(
        {
            "date": dates,
            "open": [100, 101, 102, 103, 104],
            "high": [101, 102, 103, 104, 105],
            "low": [99, 100, 101, 102, 103],
            "close": [100.5, 101.5, 102.5, 103.5, 104.5],
            "volume": [1000, 1100, 1200, 1300, 1400],
        }
    )
    ak = MagicMock()
    ak.stock_zh_a_hist_tx.return_value = sample
    ak.stock_zh_a_hist.side_effect = AssertionError("eastmoney should not be called")
    mock_ak.return_value = ak

    from ax_dataflows.vendors.stock import get_akshare_stock_data

    end = dates[-1].strftime("%Y-%m-%d")
    out = get_akshare_stock_data("600519.SS", "2026-07-21", end)
    assert "AKShare" in out
    assert "tencent-first" in out
    assert "600519" in out
    assert "Open" in out
    ak.stock_zh_a_hist_tx.assert_called_once()


@patch("ax_dataflows.vendors.stock.require_akshare")
def test_get_akshare_stock_data_falls_back_to_eastmoney(mock_ak):
    dates = pd.date_range("2026-07-21", periods=3, freq="B")
    em_sample = pd.DataFrame(
        {
            "日期": dates,
            "开盘": [100, 101, 102],
            "最高": [101, 102, 103],
            "最低": [99, 100, 101],
            "收盘": [100.5, 101.5, 102.5],
            "成交量": [1000, 1100, 1200],
        }
    )
    ak = MagicMock()
    ak.stock_zh_a_hist_tx.side_effect = ConnectionError("tencent blocked")
    ak.stock_zh_a_hist.return_value = em_sample
    mock_ak.return_value = ak

    from ax_dataflows.vendors.stock import get_akshare_stock_data

    end = dates[-1].strftime("%Y-%m-%d")
    out = get_akshare_stock_data("600519.SS", "2026-07-21", end)
    assert "Open" in out
    ak.stock_zh_a_hist.assert_called_once()


def test_akshare_registered_in_interface():
    from tradingagents.dataflows import interface as iface

    assert "akshare" in iface.VENDOR_LIST
    for method in (
        "get_stock_data",
        "get_indicators",
        "get_fundamentals",
        "get_balance_sheet",
        "get_income_statement",
        "get_cashflow",
        "get_news",
        "get_global_news",
    ):
        assert "akshare" in iface.VENDOR_METHODS[method]


@patch("ax_dataflows.vendors.fundamentals.require_akshare")
def test_get_akshare_fundamentals(mock_ak):
    ak = MagicMock()
    ak.stock_individual_info_em.return_value = pd.DataFrame(
        {"item": ["股票简称", "总市值"], "value": ["贵州茅台", "2.1万亿"]}
    )
    ak.stock_financial_abstract.return_value = pd.DataFrame(
        {
            "选项": ["常用指标", "常用指标"],
            "指标": ["归母净利润", "营业总收入"],
            "20251231": [8.2e10, 1.72e11],
            "20250930": [6.4e10, 1.31e11],
        }
    )
    mock_ak.return_value = ak

    from ax_dataflows.vendors.fundamentals import get_akshare_fundamentals

    out = get_akshare_fundamentals("600519.SS")
    assert "贵州茅台" in out
    assert "归母净利润" in out


@patch("ax_dataflows.vendors.news.require_akshare")
def test_get_akshare_news_filters_dates(mock_ak):
    ak = MagicMock()
    ak.stock_news_em.return_value = pd.DataFrame(
        {
            "新闻标题": ["旧闻", "新讯"],
            "新闻内容": ["old", "new"],
            "发布时间": ["2026-07-20 10:00:00", "2026-07-28 12:00:00"],
            "文章来源": ["测试", "测试"],
            "新闻链接": ["http://a", "http://b"],
        }
    )
    mock_ak.return_value = ak

    from ax_dataflows.vendors.news import get_akshare_news

    out = get_akshare_news("600519.SS", "2026-07-25", "2026-07-29")
    assert "新讯" in out
    assert "旧闻" not in out


@patch("ax_dataflows.vendors.news.require_akshare")
def test_get_akshare_global_news(mock_ak):
    ak = MagicMock()
    ak.news_cctv.return_value = pd.DataFrame(
        {"date": ["20260728"], "title": ["宏观政策发布"], "content": ["政策细节" * 20]}
    )
    mock_ak.return_value = ak

    from ax_dataflows.vendors.news import get_akshare_global_news

    out = get_akshare_global_news("2026-07-29", look_back_days=3, limit=5)
    assert "宏观政策发布" in out
    assert "China Macro News" in out
