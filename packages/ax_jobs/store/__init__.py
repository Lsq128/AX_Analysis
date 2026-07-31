"""Job store factory."""

from __future__ import annotations

from typing import Protocol

from ax_jobs.models import AnalysisJobRecord
from ax_jobs.settings import resolve_store_backend
from ax_jobs.store.memory import MemoryJobStore
from ax_jobs.store.redis_store import RedisJobStore

_STORE = None


class JobStore(Protocol):
    def create_job(self, job: AnalysisJobRecord) -> AnalysisJobRecord: ...
    def get_job(self, job_id: str) -> AnalysisJobRecord | None: ...
    def update_job(self, job_id: str, **fields) -> AnalysisJobRecord | None: ...
    def dequeue(self, timeout: float = 5.0) -> str | None: ...
    def publish_event(self, job_id: str, event: dict) -> None: ...
    def iter_events(self, job_id: str, *, from_index: int = 0): ...


def get_job_store(*, reset: bool = False):
    global _STORE
    if reset or _STORE is None:
        from ax_db.session import db_enabled

        if db_enabled():
            from ax_jobs.store.postgres_store import PostgresJobStore

            _STORE = PostgresJobStore()
        else:
            backend = resolve_store_backend()
            _STORE = RedisJobStore() if backend == "redis" else MemoryJobStore()
    return _STORE


def reset_job_store() -> None:
    global _STORE
    _STORE = None
