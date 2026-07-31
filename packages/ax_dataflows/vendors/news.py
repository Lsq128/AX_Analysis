"""AKShare news for A-shares."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd
from dateutil.relativedelta import relativedelta

from ax_dataflows.symbols import to_akshare_code
from ax_dataflows.vendors._akshare import require_akshare


def _parse_pub_date(value) -> datetime | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def _in_window(pub: datetime | None, start_dt: datetime, end_dt: datetime) -> bool:
    if pub is None:
        return end_dt.date() >= datetime.now(timezone.utc).date() - timedelta(days=1)
    return start_dt <= pub <= end_dt + timedelta(days=1)


def get_akshare_news(
    ticker: str,
    start_date: str,
    end_date: str,
) -> str:
    """Ticker-specific A-share news from East Money."""
    ak = require_akshare()
    code = to_akshare_code(ticker)
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")

    raw = ak.stock_news_em(symbol=code)
    if raw is None or raw.empty:
        return f"No news found for {code} between {start_date} and {end_date}"

    title_col = "新闻标题" if "新闻标题" in raw.columns else raw.columns[1]
    content_col = "新闻内容" if "新闻内容" in raw.columns else None
    time_col = "发布时间" if "发布时间" in raw.columns else None
    source_col = "文章来源" if "文章来源" in raw.columns else None
    link_col = "新闻链接" if "新闻链接" in raw.columns else None

    blocks: list[str] = []
    for _, row in raw.iterrows():
        pub = _parse_pub_date(row.get(time_col)) if time_col else None
        if not _in_window(pub, start_dt, end_dt):
            continue
        title = row.get(title_col, "No title")
        source = row.get(source_col, "Unknown") if source_col else "Unknown"
        block = f"### {title} (source: {source})\n"
        if content_col and pd.notna(row.get(content_col)):
            block += f"{row.get(content_col)}\n"
        if link_col and pd.notna(row.get(link_col)):
            block += f"Link: {row.get(link_col)}\n"
        blocks.append(block)

    if not blocks:
        return f"No news found for {code} between {start_date} and {end_date}"

    return f"## {code} News (AKShare), from {start_date} to {end_date}:\n\n" + "\n".join(blocks)


def get_akshare_global_news(
    curr_date: str,
    look_back_days: int | None = None,
    limit: int | None = None,
) -> str:
    """Domestic macro/news headlines via CCTV bulletin archive."""
    from tradingagents.dataflows.config import get_config

    ak = require_akshare()
    config = get_config()
    if look_back_days is None:
        look_back_days = config["global_news_lookback_days"]
    if limit is None:
        limit = config["global_news_article_limit"]

    curr_dt = datetime.strptime(curr_date, "%Y-%m-%d")
    start_dt = curr_dt - relativedelta(days=look_back_days)

    blocks: list[str] = []
    seen: set[str] = set()
    day = curr_dt
    while day >= start_dt and len(blocks) < limit:
        date_key = day.strftime("%Y%m%d")
        try:
            frame = ak.news_cctv(date=date_key)
        except Exception:
            frame = None
        if frame is not None and not frame.empty:
            for _, row in frame.iterrows():
                title = str(row.get("title", "")).strip()
                if not title or title in seen:
                    continue
                seen.add(title)
                content = str(row.get("content", "")).strip()
                snippet = content[:400] + ("…" if len(content) > 400 else "")
                blocks.append(f"### {title} (source: 新闻联播 {date_key})\n{snippet}\n")
                if len(blocks) >= limit:
                    break
        day -= timedelta(days=1)

    start_label = start_dt.strftime("%Y-%m-%d")
    if not blocks:
        return f"No domestic macro news found between {start_label} and {curr_date}"

    header = f"## China Macro News (AKShare CCTV), from {start_label} to {curr_date}:\n\n"
    return header + "\n".join(blocks)
