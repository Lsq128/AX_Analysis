"""Recent ticker suggestions and search."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from ax_api.deps import get_current_user_id, get_store
from ax_api.schemas import RecentTickerResponse, TickerSearchResult
from ax_engine.ticker_catalog import POPULAR_TICKERS

router = APIRouter(prefix="/tickers", tags=["tickers"])


@router.get("/recent", response_model=list[RecentTickerResponse])
def list_recent_tickers(
    user_id: Annotated[str, Depends(get_current_user_id)],
    store=Depends(get_store),
    limit: int = 10,
) -> list[RecentTickerResponse]:
    if not hasattr(store, "list_jobs"):
        return []
    jobs = store.list_jobs(user_id, limit=min(limit * 5, 50))
    seen: set[str] = set()
    out: list[RecentTickerResponse] = []
    for job in jobs:
        ticker = job.ticker
        if ticker in seen:
            continue
        seen.add(ticker)
        out.append(
            RecentTickerResponse(
                ticker=ticker,
                last_analysis_date=job.analysis_date,
                last_job_id=job.job_id,
                last_status=job.status.value if hasattr(job.status, "value") else str(job.status),
            )
        )
        if len(out) >= limit:
            break
    return out


@router.get("/search", response_model=list[TickerSearchResult])
def search_tickers(
    user_id: Annotated[str, Depends(get_current_user_id)],
    store=Depends(get_store),
    q: Annotated[str, Query(min_length=1, max_length=32)] = "",
    limit: int = 10,
) -> list[TickerSearchResult]:
    query = q.strip().lower()
    if not query:
        return []

    results: list[TickerSearchResult] = []
    seen: set[str] = set()

    if hasattr(store, "list_jobs"):
        for job in store.list_jobs(user_id, limit=50):
            ticker = job.ticker
            if ticker.lower().find(query) >= 0 and ticker not in seen:
                seen.add(ticker)
                results.append(
                    TickerSearchResult(ticker=ticker, source="recent"),
                )

    for item in POPULAR_TICKERS:
        ticker = item["ticker"]
        if ticker in seen:
            continue
        hay = f"{item['ticker']} {item['name']} {item['market']}".lower()
        if query in hay:
            seen.add(ticker)
            results.append(
                TickerSearchResult(
                    ticker=item["ticker"],
                    name=item["name"],
                    market=item["market"],
                    source="catalog",
                )
            )
        if len(results) >= limit:
            break

    return results[: min(limit, 20)]
