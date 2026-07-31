"""Redis-backed job store and queue."""

from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from typing import Any

import redis

from ax_jobs.models import AnalysisJobRecord, JobStatus, utc_now_iso
from ax_jobs.settings import get_settings


class RedisJobStore:
    def __init__(self, redis_url: str | None = None) -> None:
        settings = get_settings()
        url = redis_url or settings["redis_url"]
        if not url:
            raise ValueError("REDIS_URL is required for RedisJobStore")
        # redis-py 8 defaults socket_timeout=5, which races BLPOP(timeout=5)
        # on empty queues (TimeoutError instead of None). Disable socket timeout;
        # blocking commands use their own timeout.
        client_kwargs = {
            "decode_responses": True,
            "socket_timeout": None,
            "socket_connect_timeout": 5,
        }
        self._client = redis.Redis.from_url(url, **client_kwargs)
        self._pubsub_client = redis.Redis.from_url(url, **client_kwargs)
        self._queue_key = str(settings["queue_key"])
        self._job_prefix = str(settings["job_key_prefix"])
        self._event_prefix = str(settings["event_channel_prefix"])
        self._lock = threading.Lock()

    def _job_key(self, job_id: str) -> str:
        return f"{self._job_prefix}{job_id}"

    def _event_channel(self, job_id: str) -> str:
        return f"{self._event_prefix}{job_id}"

    def _progress_key(self, job_id: str) -> str:
        return f"{self._event_prefix}progress:{job_id}"

    def create_job(self, job: AnalysisJobRecord) -> AnalysisJobRecord:
        key = self._job_key(job.job_id)
        self._client.set(key, json.dumps(job.to_dict(), ensure_ascii=False))
        self._client.rpush(self._queue_key, job.job_id)
        return job

    def get_job(self, job_id: str) -> AnalysisJobRecord | None:
        raw = self._client.get(self._job_key(job_id))
        if not raw:
            return None
        return AnalysisJobRecord.from_dict(json.loads(raw))

    def update_job(self, job_id: str, **fields: Any) -> AnalysisJobRecord | None:
        job = self.get_job(job_id)
        if not job:
            return None
        data = job.to_dict()
        data.update(fields)
        data["updated_at"] = utc_now_iso()
        if "status" in data and not isinstance(data["status"], JobStatus):
            data["status"] = JobStatus(data["status"]).value
        elif "status" in data and isinstance(data["status"], JobStatus):
            data["status"] = data["status"].value
        updated = AnalysisJobRecord.from_dict(data)
        self._client.set(
            self._job_key(job_id),
            json.dumps(updated.to_dict(), ensure_ascii=False),
        )
        return updated

    def dequeue(self, timeout: float = 5.0) -> str | None:
        try:
            item = self._client.blpop(self._queue_key, timeout=max(1, int(timeout)))
        except redis.exceptions.TimeoutError:
            return None
        if not item:
            return None
        _, job_id = item
        return job_id

    def publish_event(self, job_id: str, event: dict[str, Any]) -> None:
        payload = dict(event)
        payload.setdefault("job_id", job_id)
        message = json.dumps(payload, ensure_ascii=False, default=str)
        self._client.publish(self._event_channel(job_id), message)
        # Late SSE subscribers miss pubsub history; keep latest progress for replay.
        if payload.get("type") == "progress":
            self._client.set(self._progress_key(job_id), message, ex=86400)

    def iter_events(
        self,
        job_id: str,
        *,
        from_index: int = 0,
        get_job: Any | None = None,
    ) -> Iterator[dict[str, Any]]:
        del from_index  # reserved for future offset replay
        resolve_job = get_job or self.get_job
        pubsub = self._pubsub_client.pubsub(ignore_subscribe_messages=True)
        pubsub.subscribe(self._event_channel(job_id))
        try:
            cached = self._client.get(self._progress_key(job_id))
            if cached:
                try:
                    yield json.loads(cached)
                except json.JSONDecodeError:
                    pass
            while True:
                message = pubsub.get_message(timeout=1.0)
                if message and message.get("type") == "message":
                    data = message.get("data")
                    event: dict[str, Any] | None = None
                    if isinstance(data, str):
                        event = json.loads(data)
                        yield event
                    job = resolve_job(job_id)
                    if job and job.status in (JobStatus.COMPLETED, JobStatus.FAILED):
                        if event and event.get("type") in ("completed", "failed"):
                            return
                else:
                    job = resolve_job(job_id)
                    if job and job.status in (JobStatus.COMPLETED, JobStatus.FAILED):
                        return
        finally:
            pubsub.close()

    def list_jobs(
        self,
        external_user_id: str,
        *,
        limit: int = 20,
        status: str | None = None,
    ) -> list[AnalysisJobRecord]:
        jobs: list[AnalysisJobRecord] = []
        cursor = 0
        pattern = f"{self._job_prefix}*"
        while True:
            cursor, keys = self._client.scan(cursor=cursor, match=pattern, count=100)
            for key in keys:
                raw = self._client.get(key)
                if not raw:
                    continue
                job = AnalysisJobRecord.from_dict(json.loads(raw))
                if job.user_id != external_user_id:
                    continue
                if status and job.status.value != status:
                    continue
                jobs.append(job)
            if cursor == 0:
                break
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return jobs[:limit]

    def requeue_job(self, job_id: str) -> AnalysisJobRecord | None:
        job = self.get_job(job_id)
        if not job:
            return None
        updated = self.update_job(job_id, status=JobStatus.QUEUED.value, error=None)
        if updated:
            self._client.rpush(self._queue_key, job_id)
        return updated
