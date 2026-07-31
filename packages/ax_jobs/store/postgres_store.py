"""Postgres persistence + Redis queue/events."""

from __future__ import annotations

from typing import Any

from ax_db.repository import JobRepository, job_row_to_record
from ax_db.session import session_scope
from ax_jobs.models import AnalysisJobRecord
from ax_jobs.settings import get_settings
from ax_jobs.store.redis_store import RedisJobStore


class PostgresJobStore:
    """Job metadata in PostgreSQL; queue and SSE events in Redis."""

    def __init__(self, redis_url: str | None = None) -> None:
        settings = get_settings()
        url = redis_url or settings["redis_url"]
        if not url:
            raise ValueError("REDIS_URL is required for PostgresJobStore")
        self._redis = RedisJobStore(url)
        self._queue_key = str(settings["queue_key"])

    def create_job(
        self,
        job: AnalysisJobRecord,
        *,
        user_uuid: str,
        points_charged: float = 0.0,
    ) -> AnalysisJobRecord:
        with session_scope() as session:
            JobRepository(session).save(job, user_uuid=user_uuid, points_charged=points_charged)
        self._redis._client.rpush(self._queue_key, job.job_id)
        return job

    def create_job_simple(self, job: AnalysisJobRecord) -> AnalysisJobRecord:
        """Protocol-compatible create without user_uuid (uses external user id lookup)."""
        from ax_db.repository import UserRepository

        with session_scope() as session:
            user = UserRepository(session).get_by_external_id(job.user_id)
            if not user:
                user = UserRepository(session).get_or_create(job.user_id)
            JobRepository(session).save(job, user_uuid=user.id)
        self._redis._client.rpush(self._queue_key, job.job_id)
        return job

    def get_job(self, job_id: str) -> AnalysisJobRecord | None:
        with session_scope() as session:
            row = JobRepository(session).get(job_id)
            if not row:
                return None
            session.refresh(row, attribute_names=["user"])
            ext_id = row.user.external_id if row.user else row.user_id
            return job_row_to_record(row, external_user_id=ext_id)

    def update_job(self, job_id: str, **fields: Any) -> AnalysisJobRecord | None:
        with session_scope() as session:
            row = JobRepository(session).update(job_id, **fields)
            if not row:
                return None
            session.refresh(row, attribute_names=["user"])
            ext_id = row.user.external_id if row.user else row.user_id
            return job_row_to_record(row, external_user_id=ext_id)

    def dequeue(self, timeout: float = 5.0) -> str | None:
        return self._redis.dequeue(timeout=timeout)

    def publish_event(self, job_id: str, event: dict[str, Any]) -> None:
        self._redis.publish_event(job_id, event)

    def iter_events(self, job_id: str, *, from_index: int = 0):
        return self._redis.iter_events(
            job_id, from_index=from_index, get_job=self.get_job
        )

    def list_jobs(
        self,
        external_user_id: str,
        *,
        limit: int = 20,
        status: str | None = None,
    ) -> list[AnalysisJobRecord]:
        from ax_db.repository import UserRepository

        with session_scope() as session:
            user = UserRepository(session).get_by_external_id(external_user_id)
            if not user:
                return []
            rows = JobRepository(session).list_for_user(user.id, limit=limit, status=status)
            return [job_row_to_record(r, external_user_id=external_user_id) for r in rows]

    def requeue_job(self, job_id: str) -> AnalysisJobRecord | None:
        updated = self.update_job(job_id, status="queued", error=None)
        if updated:
            self._redis._client.rpush(self._queue_key, job_id)
        return updated
