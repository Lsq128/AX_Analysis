"""Object key helpers for report trees."""

from __future__ import annotations

from ax_engine.paths import safe_path_component


def report_key_prefix(*, user_id: str, job_id: str) -> str:
    user = safe_path_component(user_id)
    job = safe_path_component(job_id, max_len=36)
    return f"reports/{user}/{job}"


def object_key(prefix: str, relative: str) -> str:
    rel = relative.strip().lstrip("/")
    if not rel:
        return prefix.rstrip("/")
    return f"{prefix.rstrip('/')}/{rel}"
