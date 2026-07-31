"""Analysis job routes."""

from __future__ import annotations

import asyncio
import json
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from ax_api.deps import assert_job_owner, get_current_user, get_current_user_id, get_store
from ax_api.schemas import AnalysisJobResponse, CreateAnalysisRequest
from ax_billing import compute_consumption_points, is_preset_allowed
from ax_db.repository import InsufficientQuotaError, UserRepository
from ax_db.session import db_enabled, session_scope
from ax_engine.ticker import is_valid_ticker_input, normalize_ticker_symbol
from ax_jobs.models import AnalysisJobRecord, JobStatus
from ax_jobs.errors import classify_job_error
from ax_jobs.store.postgres_store import PostgresJobStore
from ax_llm import resolve_llm_selection
from ax_presets import expand_preset

router = APIRouter(prefix="/analyses", tags=["analyses"])


def _job_response(job: AnalysisJobRecord, *, points_charged: float | None = None) -> AnalysisJobResponse:
    data = job.to_dict()
    if points_charged is not None:
        data["points_charged"] = points_charged
    if job.status == JobStatus.FAILED and job.error:
        info = classify_job_error(job.error)
        data["error_code"] = info.code
        data["error_message"] = info.message
        data["retryable"] = info.retryable
    return AnalysisJobResponse(**data)


def _resolve_params(body: CreateAnalysisRequest) -> tuple[list[str], int, str | None, float]:
    if body.preset:
        params = expand_preset(body.preset)
        base = float(params["quota_points"])
        points = compute_consumption_points(base_points=base, llm_provider=body.llm_provider)
        return (
            list(params["analysts"]),  # type: ignore[arg-type]
            int(params["research_depth"]),
            str(params["preset_id"]),
            points,
        )
    assert body.analysts is not None and body.research_depth is not None
    depth_points = {1: 1.0, 3: 2.5, 5: 4.0}.get(body.research_depth, float(body.research_depth))
    points = compute_consumption_points(base_points=depth_points, llm_provider=body.llm_provider)
    return body.analysts, body.research_depth, None, points


@router.get("", response_model=list[AnalysisJobResponse])
def list_analyses(
    user_id: Annotated[str, Depends(get_current_user_id)],
    store=Depends(get_store),
    limit: int = 20,
    status: str | None = None,
) -> list[AnalysisJobResponse]:
    if hasattr(store, "list_jobs"):
        jobs = store.list_jobs(user_id, limit=limit, status=status)
        return [_job_response(j) for j in jobs]
    return []


@router.post("", response_model=AnalysisJobResponse, status_code=202)
def create_analysis(
    body: CreateAnalysisRequest,
    user_id: Annotated[str, Depends(get_current_user_id)],
    user: Annotated[dict, Depends(get_current_user)],
    store=Depends(get_store),
) -> AnalysisJobResponse:
    if not is_valid_ticker_input(body.ticker):
        raise HTTPException(status_code=400, detail="Invalid ticker symbol")

    if body.preset and not is_preset_allowed(user.get("plan_id", "standard"), body.preset):
        raise HTTPException(
            status_code=403,
            detail={
                "message": "当前套餐不可用此分析方案，请升级套餐。",
                "preset": body.preset,
                "plan_id": user.get("plan_id"),
            },
        )

    try:
        analysts, research_depth, preset_id, points = _resolve_params(body)
        llm = resolve_llm_selection(
            body.llm_provider,
            shallow_thinker=body.shallow_thinker,
            deep_thinker=body.deep_thinker,
        )
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    ticker = normalize_ticker_symbol(body.ticker)
    job = AnalysisJobRecord.new(
        user_id=user_id,
        ticker=ticker,
        analysis_date=body.analysis_date,
        analysts=analysts,
        research_depth=research_depth,
        preset_id=preset_id,
        run_config=llm,
    )

    if db_enabled() and isinstance(store, PostgresJobStore):
        try:
            with session_scope() as session:
                user = UserRepository(session).get_or_create(user_id)
                UserRepository(session).charge_points(user.id, points)
                store.create_job(job, user_uuid=user.id, points_charged=points)
        except InsufficientQuotaError as exc:
            raise HTTPException(
                status_code=402,
                detail={
                    "message": "配额不足",
                    "required": exc.required,
                    "remaining": exc.remaining,
                },
            ) from exc
    else:
        store.create_job(job)

    store.publish_event(job.job_id, {"type": "queued", "status": JobStatus.QUEUED.value})
    return _job_response(job, points_charged=points if db_enabled() else None)


@router.get("/{job_id}", response_model=AnalysisJobResponse)
def get_analysis(
    job_id: str,
    user_id: Annotated[str, Depends(get_current_user_id)],
    store=Depends(get_store),
) -> AnalysisJobResponse:
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Analysis job not found")
    assert_job_owner(job.user_id, user_id)
    return _job_response(job)


@router.post("/{job_id}/retry", response_model=AnalysisJobResponse)
def retry_analysis(
    job_id: str,
    user_id: Annotated[str, Depends(get_current_user_id)],
    store=Depends(get_store),
) -> AnalysisJobResponse:
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Analysis job not found")
    assert_job_owner(job.user_id, user_id)
    if job.status != JobStatus.FAILED:
        raise HTTPException(status_code=409, detail="Only failed jobs can be retried")
    info = classify_job_error(job.error)
    if not info.retryable:
        raise HTTPException(
            status_code=400,
            detail={"message": info.message, "error_code": info.code},
        )
    if not hasattr(store, "requeue_job"):
        raise HTTPException(status_code=501, detail="Retry is not supported for this job store")
    updated = store.requeue_job(job_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Analysis job not found")
    store.publish_event(job_id, {"type": "queued", "status": JobStatus.QUEUED.value})
    return _job_response(updated)


async def _sse_stream(job_id: str, store) -> Any:
    job = store.get_job(job_id)
    if not job:
        yield f"event: error\ndata: {json.dumps({'detail': 'not found'})}\n\n"
        return

    status_payload = {"type": "status", **job.to_dict()}
    yield f"event: status\ndata: {json.dumps(status_payload, ensure_ascii=False, default=str)}\n\n"

    loop = asyncio.get_event_loop()

    def _iter_events():
        return store.iter_events(job_id)

    iterator = _iter_events()

    def _next_event(it):
        try:
            return next(it)
        except StopIteration:
            return None

    while True:
        event = await loop.run_in_executor(None, _next_event, iterator)
        if event is None:
            break
        payload = json.dumps(event, ensure_ascii=False, default=str)
        yield f"event: {event.get('type', 'message')}\ndata: {payload}\n\n"
        if event.get("type") in ("completed", "failed"):
            break

    final = store.get_job(job_id)
    if final:
        final_payload = {"type": "status", **final.to_dict()}
        yield f"event: status\ndata: {json.dumps(final_payload, ensure_ascii=False, default=str)}\n\n"


@router.get("/{job_id}/events")
async def stream_analysis_events(
    job_id: str,
    user_id: Annotated[str, Depends(get_current_user_id)],
    store=Depends(get_store),
) -> StreamingResponse:
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Analysis job not found")
    assert_job_owner(job.user_id, user_id)

    return StreamingResponse(
        _sse_stream(job_id, store),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
