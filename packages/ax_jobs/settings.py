"""Job store and queue settings."""

from __future__ import annotations

import os
from functools import lru_cache


@lru_cache
def get_settings() -> dict[str, str | None]:
    return {
        "redis_url": os.getenv("REDIS_URL"),
        "job_store": os.getenv("AX_JOB_STORE"),  # redis | memory
        "queue_key": os.getenv("AX_QUEUE_KEY", "ax:queue:analysis"),
        "job_key_prefix": os.getenv("AX_JOB_KEY_PREFIX", "ax:job:"),
        "event_channel_prefix": os.getenv("AX_EVENT_CHANNEL_PREFIX", "ax:events:"),
    }


def resolve_store_backend() -> str:
    settings = get_settings()
    explicit = settings["job_store"]
    if explicit in ("redis", "memory"):
        return explicit
    if settings["redis_url"]:
        return "redis"
    return "memory"
