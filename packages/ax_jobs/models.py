"""Shared job models for API and Worker."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AnalysisJobRecord:
    job_id: str
    user_id: str
    ticker: str
    analysis_date: str
    preset_id: str | None
    analysts: list[str]
    research_depth: int
    status: JobStatus = JobStatus.QUEUED
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)
    report_path: str | None = None
    error: str | None = None
    stats: dict[str, Any] | None = None
    decision_preview: str | None = None
    run_config: dict[str, Any] | None = None

    @classmethod
    def new(
        cls,
        *,
        user_id: str,
        ticker: str,
        analysis_date: str,
        analysts: list[str],
        research_depth: int,
        preset_id: str | None = None,
        run_config: dict[str, Any] | None = None,
    ) -> AnalysisJobRecord:
        return cls(
            job_id=str(uuid4()),
            user_id=user_id,
            ticker=ticker,
            analysis_date=analysis_date,
            preset_id=preset_id,
            analysts=analysts,
            research_depth=research_depth,
            run_config=run_config,
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AnalysisJobRecord:
        status = data.get("status", JobStatus.QUEUED.value)
        if isinstance(status, JobStatus):
            status_value = status
        else:
            status_value = JobStatus(status)
        return cls(
            job_id=data["job_id"],
            user_id=data["user_id"],
            ticker=data["ticker"],
            analysis_date=data["analysis_date"],
            preset_id=data.get("preset_id"),
            analysts=list(data.get("analysts") or []),
            research_depth=int(data.get("research_depth", 1)),
            status=status_value,
            created_at=data.get("created_at", utc_now_iso()),
            updated_at=data.get("updated_at", utc_now_iso()),
            report_path=data.get("report_path"),
            error=data.get("error"),
            stats=data.get("stats"),
            decision_preview=data.get("decision_preview"),
            run_config=data.get("run_config"),
        )
