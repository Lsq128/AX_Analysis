"""Worker job consumer — runs ax_engine for queued jobs."""

from __future__ import annotations

import logging
import traceback
from pathlib import Path
from typing import Any

from ax_engine import AnalysisRequest, load_ax_env, run_analysis_job
from ax_jobs.models import JobStatus
from ax_jobs.store import get_job_store
from ax_storage import should_upload_to_storage, upload_report_tree

logger = logging.getLogger(__name__)


def _preview_decision(text: str, limit: int = 500) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def process_job(job_id: str) -> None:
    store = get_job_store()
    job = store.get_job(job_id)
    if not job:
        logger.warning("Job %s not found, skipping", job_id)
        return

    store.update_job(job_id, status=JobStatus.RUNNING.value)
    store.publish_event(job_id, {"type": "started", "status": JobStatus.RUNNING.value})

    run_config = job.run_config or {}
    request = AnalysisRequest(
        job_id=job_id,
        user_id=job.user_id,
        ticker=job.ticker,
        analysis_date=job.analysis_date,
        analysts=job.analysts,
        research_depth=job.research_depth,
        llm_provider=run_config.get("llm_provider"),
        shallow_thinker=run_config.get("shallow_thinker"),
        deep_thinker=run_config.get("deep_thinker"),
        save_reports=True,
    )

    def on_event(event: dict[str, Any]) -> None:
        store.publish_event(job_id, event)

    try:
        result = run_analysis_job(request, on_event=on_event)
        decision = result.final_state.get("final_trade_decision", "") or ""
        report_path = result.report_path
        if report_path and should_upload_to_storage():
            local_dir = Path(report_path).parent if not Path(report_path).is_dir() else Path(report_path)
            report_path = upload_report_tree(
                local_dir,
                user_id=job.user_id,
                job_id=job_id,
            )
        store.update_job(
            job_id,
            status=JobStatus.COMPLETED.value,
            report_path=report_path,
            stats=result.stats.__dict__,
            decision_preview=_preview_decision(decision) if decision else None,
        )
        store.publish_event(
            job_id,
            {
                "type": "completed",
                "status": JobStatus.COMPLETED.value,
                "report_path": report_path,
                "stats": result.stats.__dict__,
            },
        )
        logger.info("Job %s completed report=%s", job_id, report_path)
    except Exception as exc:
        logger.exception("Job %s failed", job_id)
        store.update_job(job_id, status=JobStatus.FAILED.value, error=str(exc))
        store.publish_event(
            job_id,
            {
                "type": "failed",
                "status": JobStatus.FAILED.value,
                "error": str(exc),
                "traceback": traceback.format_exc(),
            },
        )


def run_consumer(*, poll_timeout: float = 5.0) -> None:
    load_ax_env()
    store = get_job_store()
    logger.info("Worker started (store=%s)", type(store).__name__)

    while True:
        job_id = store.dequeue(timeout=poll_timeout)
        if not job_id:
            continue
        logger.info("Processing job %s", job_id)
        process_job(job_id)
