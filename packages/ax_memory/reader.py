"""Read per-user trading memory entries for the review UI."""

from __future__ import annotations

from ax_engine.paths import user_data_paths
from tradingagents.agents.utils.memory import TradingMemoryLog

RATING_LABELS_ZH: dict[str, str] = {
    "Buy": "买入",
    "Overweight": "增持",
    "Hold": "持有",
    "Underweight": "减持",
    "Sell": "卖出",
}


def memory_log_path(user_id: str) -> str:
    return user_data_paths(user_id)["memory_log_path"]


def _memory_log(user_id: str) -> TradingMemoryLog:
    return TradingMemoryLog({"memory_log_path": memory_log_path(user_id)})


def load_user_entries(user_id: str) -> list[dict]:
    """Return memory entries newest-first, shaped for API responses."""
    entries = _memory_log(user_id).load_entries()
    shaped: list[dict] = []
    for entry in entries:
        rating = entry.get("rating") or "Hold"
        shaped.append(
            {
                "id": f"{entry['date']}|{entry['ticker']}",
                "date": entry["date"],
                "ticker": entry["ticker"],
                "rating": rating,
                "rating_label": RATING_LABELS_ZH.get(rating, rating),
                "pending": bool(entry.get("pending")),
                "raw_return": entry.get("raw"),
                "alpha_return": entry.get("alpha"),
                "holding_days": _parse_holding(entry.get("holding")),
                "decision": entry.get("decision") or "",
                "reflection": entry.get("reflection") or "",
            }
        )
    shaped.sort(key=lambda e: e["date"], reverse=True)
    return shaped


def memory_stats(entries: list[dict]) -> dict:
    pending = sum(1 for e in entries if e.get("pending"))
    resolved = len(entries) - pending
    tickers_pending = sorted({e["ticker"] for e in entries if e.get("pending")})
    return {
        "total_entries": len(entries),
        "pending_count": pending,
        "resolved_count": resolved,
        "tickers_pending": tickers_pending,
    }


def _parse_holding(value: str | None) -> int | None:
    if not value:
        return None
    cleaned = value.strip().lower().rstrip("d")
    try:
        return int(cleaned)
    except ValueError:
        return None
