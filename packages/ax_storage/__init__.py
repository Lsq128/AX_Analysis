"""Report object storage for AX SaaS."""

from __future__ import annotations

import shutil
from functools import lru_cache
from pathlib import Path

from ax_storage.keys import report_key_prefix
from ax_storage.local import LocalReportStorage
from ax_storage.settings import get_storage_settings, is_storage_key
from ax_storage.s3 import S3ReportStorage


@lru_cache
def get_report_storage():
    settings = get_storage_settings()
    backend = settings["backend"]
    if backend == "s3":
        return S3ReportStorage(
            bucket=settings["bucket"],
            region=settings["region"],
            endpoint_url=settings["endpoint_url"],
            access_key=settings["access_key"],
            secret_key=settings["secret_key"],
        )
    root = settings["local_root"]
    if root:
        return LocalReportStorage(Path(root))
    from ax_engine.env import ax_project_root

    return LocalReportStorage(ax_project_root() / "data" / "report_storage")


def upload_report_tree(
    local_dir: Path,
    *,
    user_id: str,
    job_id: str,
) -> str:
    """Upload a local report directory; return the storage key prefix."""
    settings = get_storage_settings()
    storage = get_report_storage()
    key = report_key_prefix(user_id=user_id, job_id=job_id)
    stored = storage.upload_tree(local_dir, key)

    if settings["backend"] == "s3" and settings["delete_local_after_upload"]:
        shutil.rmtree(local_dir, ignore_errors=True)

    return stored


def should_upload_to_storage() -> bool:
    return get_storage_settings()["backend"] == "s3"


def reset_report_storage_cache() -> None:
    get_storage_settings.cache_clear()
    if hasattr(get_report_storage, "cache_clear"):
        get_report_storage.cache_clear()


__all__ = [
    "get_report_storage",
    "upload_report_tree",
    "should_upload_to_storage",
    "is_storage_key",
    "report_key_prefix",
    "reset_report_storage_cache",
]
