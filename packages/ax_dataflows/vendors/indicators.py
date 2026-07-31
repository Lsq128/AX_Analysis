"""AKShare-backed technical indicators via stockstats."""

from __future__ import annotations

from datetime import datetime

from dateutil.relativedelta import relativedelta
from stockstats import wrap

from ax_dataflows.symbols import to_akshare_code
from ax_dataflows.vendors.stock import fetch_a_share_ohlcv

_SUPPORTED = {
    "close_50_sma",
    "close_200_sma",
    "close_10_ema",
    "macd",
    "macds",
    "macdh",
    "rsi",
    "boll",
    "boll_ub",
    "boll_lb",
    "atr",
    "vwma",
    "mfi",
}


def get_akshare_indicators(
    symbol: str,
    indicator: str,
    curr_date: str,
    look_back_days: int,
) -> str:
    """Vendor-compatible indicator series for ``get_indicators``."""
    if indicator not in _SUPPORTED:
        raise ValueError(
            f"Indicator {indicator} is not supported. Choose from: {sorted(_SUPPORTED)}"
        )

    curr_dt = datetime.strptime(curr_date, "%Y-%m-%d")
    before = curr_dt - relativedelta(days=look_back_days)
    start = before.strftime("%Y-%m-%d")

    code = to_akshare_code(symbol)
    data = fetch_a_share_ohlcv(symbol, start, curr_date)
    data = data[data["Date"] <= curr_dt]

    from tradingagents.dataflows.stockstats_utils import _assert_ohlcv_not_stale

    _assert_ohlcv_not_stale(data, curr_date, symbol, code)

    df = wrap(data.copy())
    df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")
    df[indicator]

    lines: list[str] = []
    walk = curr_dt
    while walk >= before:
        ds = walk.strftime("%Y-%m-%d")
        row = df[df["Date"] == ds]
        if row.empty:
            val = "N/A: Not a trading day (weekend or holiday)"
        else:
            val = row[indicator].values[0]
        lines.append(f"{ds}: {val}")
        walk -= relativedelta(days=1)

    header = f"## {indicator} values from {start} to {curr_date} (AKShare qfq, tencent-first)\n\n"
    return header + "\n".join(lines) + "\n"
