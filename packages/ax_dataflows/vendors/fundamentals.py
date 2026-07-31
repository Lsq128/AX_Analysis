"""AKShare fundamentals for A-shares."""

from __future__ import annotations

from datetime import datetime

import pandas as pd

from ax_dataflows.symbols import to_akshare_code, to_em_exchange_prefix
from ax_dataflows.vendors._akshare import require_akshare


def _header(title: str, symbol: str) -> str:
    code = to_akshare_code(symbol)
    return (
        f"# {title} for {code} (AKShare)\n"
        f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    )


def _info_lines(frame: pd.DataFrame) -> list[str]:
    if frame is None or frame.empty:
        return []
    cols = {c.lower(): c for c in frame.columns}
    item_col = cols.get("item") or cols.get("项目")
    value_col = cols.get("value") or cols.get("值") or cols.get("内容")
    if not item_col or not value_col:
        return [str(frame.to_string(index=False))]
    lines: list[str] = []
    for _, row in frame.iterrows():
        item = row.get(item_col)
        value = row.get(value_col)
        if pd.notna(item) and pd.notna(value):
            lines.append(f"{item}: {value}")
    return lines


def _latest_period_columns(frame: pd.DataFrame, *, max_periods: int = 4) -> list[str]:
    periods = [c for c in frame.columns if str(c).isdigit() and len(str(c)) == 8]
    periods.sort(reverse=True)
    return periods[:max_periods]


def _abstract_lines(frame: pd.DataFrame) -> list[str]:
    if frame is None or frame.empty:
        return []
    option_col = "选项" if "选项" in frame.columns else None
    metric_col = "指标" if "指标" in frame.columns else None
    if not metric_col:
        return [str(frame.head(20).to_string(index=False))]

    periods = _latest_period_columns(frame)
    if not periods:
        return [str(frame.head(20).to_string(index=False))]

    lines: list[str] = []
    subset = frame
    if option_col:
        subset = frame[frame[option_col].astype(str).str.contains("常用|每股|盈利能力|成长", na=False)]
        if subset.empty:
            subset = frame.head(25)

    for _, row in subset.iterrows():
        metric = row.get(metric_col)
        if pd.isna(metric):
            continue
        parts = [f"{metric}:"]
        for period in periods:
            val = row.get(period)
            if pd.notna(val):
                parts.append(f"  {period}: {val}")
        if len(parts) > 1:
            lines.append("\n".join(parts))
    return lines


def _filter_reports(frame: pd.DataFrame, curr_date: str | None) -> pd.DataFrame:
    if frame is None or frame.empty:
        return frame
    if not curr_date or "REPORT_DATE" not in frame.columns:
        return frame
    cutoff = pd.to_datetime(curr_date)
    dates = pd.to_datetime(frame["REPORT_DATE"], errors="coerce")
    filtered = frame.loc[dates <= cutoff].copy()
    if filtered.empty:
        return frame.head(1)
    return filtered.sort_values("REPORT_DATE", ascending=False)


def get_akshare_fundamentals(
    ticker: str,
    curr_date: str | None = None,
) -> str:
    """Company fundamentals overview for A-shares."""
    from tradingagents.dataflows.symbol_utils import NoMarketDataError

    ak = require_akshare()
    code = to_akshare_code(ticker)
    lines: list[str] = []

    try:
        info = ak.stock_individual_info_em(symbol=code)
        lines.extend(_info_lines(info))
    except Exception:
        info = None

    try:
        abstract = ak.stock_financial_abstract(symbol=code)
        lines.extend(_abstract_lines(abstract))
    except Exception:
        abstract = None

    if not lines:
        raise NoMarketDataError(ticker, code, "akshare returned no fundamentals")

    return _header("Company Fundamentals", ticker) + "\n".join(lines)


def get_akshare_balance_sheet(
    ticker: str,
    freq: str = "quarterly",
    curr_date: str | None = None,
) -> str:
    return _financial_statement(
        ticker,
        curr_date=curr_date,
        title=f"Balance Sheet ({freq})",
        fetch=lambda ak, sym: ak.stock_balance_sheet_by_report_em(symbol=sym),
    )


def get_akshare_income_statement(
    ticker: str,
    freq: str = "quarterly",
    curr_date: str | None = None,
) -> str:
    return _financial_statement(
        ticker,
        curr_date=curr_date,
        title=f"Income Statement ({freq})",
        fetch=lambda ak, sym: ak.stock_profit_sheet_by_report_em(symbol=sym),
    )


def get_akshare_cashflow(
    ticker: str,
    freq: str = "quarterly",
    curr_date: str | None = None,
) -> str:
    return _financial_statement(
        ticker,
        curr_date=curr_date,
        title=f"Cash Flow ({freq})",
        fetch=lambda ak, sym: ak.stock_cash_flow_sheet_by_report_em(symbol=sym),
    )


def _financial_statement(
    ticker: str,
    *,
    curr_date: str | None,
    title: str,
    fetch,
) -> str:
    from tradingagents.dataflows.symbol_utils import NoMarketDataError

    ak = require_akshare()
    sym = to_em_exchange_prefix(ticker)
    data = fetch(ak, sym)
    if data is None or data.empty:
        raise NoMarketDataError(ticker, to_akshare_code(ticker), f"no {title.lower()} data")

    data = _filter_reports(data, curr_date)
    trimmed = data.head(4)
    csv_string = trimmed.to_csv(index=False)
    return _header(title, ticker) + csv_string
