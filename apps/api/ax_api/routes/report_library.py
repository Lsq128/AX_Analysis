"""Report library — list completed analyses with saved reports."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from ax_api.deps import get_current_user_id, get_store
from ax_api.routes.analyses import _job_response
from ax_api.schemas import AnalysisJobResponse

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("", response_model=list[AnalysisJobResponse])
def list_reports(
    user_id: Annotated[str, Depends(get_current_user_id)],
    store=Depends(get_store),
    limit: int = 50,
) -> list[AnalysisJobResponse]:
    if not hasattr(store, "list_jobs"):
        return []
    jobs = store.list_jobs(user_id, limit=min(limit, 100), status="completed")
    return [_job_response(j) for j in jobs if j.report_path]
