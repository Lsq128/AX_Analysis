"""In-process job store for tests and local dev without Redis."""

from __future__ import annotations

import threading
from collections import deque
from collections.abc import Iterator
from typing import Any

from ax_jobs.models import AnalysisJobRecord, JobStatus, utc_now_iso


class MemoryJobStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._jobs: dict[str, AnalysisJobRecord] = {}
        self._queue: deque[str] = deque()
        self._events: dict[str, list[dict[str, Any]]] = {}
        self._event_cond = threading.Condition(self._lock)

    def create_job(self, job: AnalysisJobRecord) -> AnalysisJobRecord:
        with self._event_cond:
            self._jobs[job.job_id] = job
            self._events.setdefault(job.job_id, [])
            self._queue.append(job.job_id)
            self._event_cond.notify_all()
        return job

    def get_job(self, job_id: str) -> AnalysisJobRecord | None:
        with self._event_cond:
            job = self._jobs.get(job_id)
            return AnalysisJobRecord.from_dict(job.to_dict()) if job else None

    def update_job(self, job_id: str, **fields: Any) -> AnalysisJobRecord | None:
        with self._event_cond:
            job = self._jobs.get(job_id)
            if not job:
                return None
            data = job.to_dict()
            data.update(fields)
            data["updated_at"] = utc_now_iso()
            if "status" in data and not isinstance(data["status"], JobStatus):
                data["status"] = JobStatus(data["status"])
            updated = AnalysisJobRecord.from_dict(data)
            self._jobs[job_id] = updated
            self._event_cond.notify_all()
            return AnalysisJobRecord.from_dict(updated.to_dict())

    def dequeue(self, timeout: float = 5.0) -> str | None:
        with self._event_cond:
            if not self._queue:
                self._event_cond.wait(timeout=timeout)
            if not self._queue:
                return None
            return self._queue.popleft()

    def publish_event(self, job_id: str, event: dict[str, Any]) -> None:
        payload = dict(event)
        payload.setdefault("job_id", job_id)
        with self._event_cond:
            self._events.setdefault(job_id, []).append(payload)
            self._event_cond.notify_all()

    def iter_events(self, job_id: str, *, from_index: int = 0) -> Iterator[dict[str, Any]]:
        index = from_index
        with self._event_cond:
            while True:
                events = self._events.get(job_id, [])
                while index < len(events):
                    yield events[index]
                    index += 1
                job = self._jobs.get(job_id)
                if job and job.status in (JobStatus.COMPLETED, JobStatus.FAILED):
                    return
                self._event_cond.wait(timeout=1.0)

    def notify_status(self, job_id: str) -> None:
        with self._event_cond:
            self._event_cond.notify_all()

    def list_jobs(
        self,
        external_user_id: str,
        *,
        limit: int = 20,
        status: str | None = None,
    ) -> list[AnalysisJobRecord]:
        with self._event_cond:
            jobs = [j for j in self._jobs.values() if j.user_id == external_user_id]
        if status:
            jobs = [j for j in jobs if j.status.value == status]
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return [AnalysisJobRecord.from_dict(j.to_dict()) for j in jobs[:limit]]

    def requeue_job(self, job_id: str) -> AnalysisJobRecord | None:
        with self._event_cond:
            job = self._jobs.get(job_id)
            if not job:
                return None
            data = job.to_dict()
            data["status"] = JobStatus.QUEUED.value
            data["error"] = None
            data["updated_at"] = utc_now_iso()
            updated = AnalysisJobRecord.from_dict(data)
            self._jobs[job_id] = updated
            self._queue.append(job_id)
            self._event_cond.notify_all()
            return AnalysisJobRecord.from_dict(updated.to_dict())
