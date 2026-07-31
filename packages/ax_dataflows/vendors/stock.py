"""AKShare OHLCV fetch for A-shares (Tencent-first, East Money fallback)."""

from __future__ import annotations

import logging
from datetime import datetime

import pandas as pd

from ax_dataflows.symbols import to_akshare_code, to_tx_symbol
from ax_dataflows.vendors._akshare import require_akshare

logger = logging.getLogger(__name__)

_AK_COL_MAP = {
    "日期": "Date",
    "开盘": "Open",
    "最高": "High",
    "最低": "Low",
    "收盘": "Close",
    "成交量": "Volume",
    "date": "Date",
    "open": "Open",
    "high": "High",
    "low": "Low",
    "close": "Close",
    "volume": "Volume",
}

_EM_TIMEOUT_SEC = 8.0


def _normalize_ohlcv(raw: pd.DataFrame) -> pd.DataFrame:
    frame = raw.rename(columns=_AK_COL_MAP)
    if "Date" not in frame.columns:
        if isinstance(frame.index, pd.DatetimeIndex):
            frame = frame.reset_index()
            if "Date" not in frame.columns and "date" in frame.columns:
                frame = frame.rename(columns={"date": "Date"})
            elif "index" in frame.columns:
                frame = frame.rename(columns={"index": "Date"})
        if "Date" not in frame.columns:
            raise ValueError("OHLCV response missing date column")

    frame["Date"] = pd.to_datetime(frame["Date"], errors="coerce")
    frame = frame.dropna(subset=["Date"])
    for col in ("Open", "High", "Low", "Close", "Volume"):
        if col in frame.columns:
            frame[col] = pd.to_numeric(frame[col], errors="coerce")

    frame = frame.dropna(subset=["Close"])
    frame = frame.sort_values("Date")
    return frame.reset_index(drop=True)


def _fetch_tencent(ak, symbol: str, start: str, end: str) -> pd.DataFrame:
    tx_symbol = to_tx_symbol(symbol)
    raw = ak.stock_zh_a_hist_tx(
        symbol=tx_symbol,
        start_date=start,
        end_date=end,
        adjust="qfq",
    )
    if raw is None or raw.empty:
        raise ValueError(f"tencent returned no rows for {tx_symbol}")
    return _normalize_ohlcv(raw)


def _fetch_eastmoney(ak, symbol: str, start: str, end: str) -> pd.DataFrame:
    code = to_akshare_code(symbol)
    raw = ak.stock_zh_a_hist(
        symbol=code,
        period="daily",
        start_date=start,
        end_date=end,
        adjust="qfq",
        timeout=_EM_TIMEOUT_SEC,
    )
    if raw is None or raw.empty:
        raise ValueError(f"eastmoney returned no rows for {code}")
    return _normalize_ohlcv(raw)


def fetch_a_share_ohlcv(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Fetch daily OHLCV: Tencent first, then East Money."""
    from tradingagents.dataflows.symbol_utils import NoMarketDataError

    ak = require_akshare()
    code = to_akshare_code(symbol)
    start = start_date.replace("-", "")
    end = end_date.replace("-", "")
    errors: list[str] = []

    for name, fetch in (
        ("tencent", _fetch_tencent),
        ("eastmoney", _fetch_eastmoney),
    ):
        try:
            frame = fetch(ak, symbol, start, end)
            if not frame.empty:
                if name != "tencent":
                    logger.info("A-share OHLCV for %s via %s (%s rows)", code, name, len(frame))
                return frame
            errors.append(f"{name}: empty")
        except Exception as exc:  # noqa: BLE001 — try next free source
            logger.warning("A-share OHLCV %s failed for %s: %s", name, code, exc)
            errors.append(f"{name}: {exc}")

    raise NoMarketDataError(
        symbol,
        code,
        f"no OHLCV from tencent/eastmoney {start_date}..{end_date}; {'; '.join(errors)}",
    )


def get_akshare_stock_data(
    symbol: str,
    start_date: str,
    end_date: str,
) -> str:
    """Vendor-compatible OHLCV CSV string for ``get_stock_data``."""
    datetime.strptime(start_date, "%Y-%m-%d")
    datetime.strptime(end_date, "%Y-%m-%d")

    from tradingagents.dataflows.stockstats_utils import _assert_ohlcv_not_stale

    code = to_akshare_code(symbol)
    data = fetch_a_share_ohlcv(symbol, start_date, end_date)
    _assert_ohlcv_not_stale(data, end_date, symbol, code)

    numeric = ["Open", "High", "Low", "Close"]
    for col in numeric:
        if col in data.columns:
            data[col] = data[col].round(2)

    csv_string = data.to_csv(index=False)
    header = (
        f"# A-share data for {code} (AKShare qfq, tencent-first) from {start_date} to {end_date}\n"
        f"# Total records: {len(data)}\n"
        f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    )
    return header + csv_string
