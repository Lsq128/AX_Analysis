"""Trading memory / review routes."""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query

from ax_api.deps import get_current_user_id
from ax_api.schemas import MemoryEntryResponse, MemoryStatsResponse
from ax_memory import load_user_entries, memory_stats

router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("/entries", response_model=list[MemoryEntryResponse])
def list_memory_entries(
    user_id: Annotated[str, Depends(get_current_user_id)],
    status: Annotated[Literal["all", "pending", "resolved"], Query()] = "all",
) -> list[MemoryEntryResponse]:
    entries = load_user_entries(user_id)
    if status == "pending":
        entries = [e for e in entries if e["pending"]]
    elif status == "resolved":
        entries = [e for e in entries if not e["pending"]]
    return [MemoryEntryResponse(**e) for e in entries]


@router.get("/stats", response_model=MemoryStatsResponse)
def get_memory_stats(
    user_id: Annotated[str, Depends(get_current_user_id)],
) -> MemoryStatsResponse:
    entries = load_user_entries(user_id)
    return MemoryStatsResponse(**memory_stats(entries))
