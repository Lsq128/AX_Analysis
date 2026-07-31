"""Report storage configuration from environment."""

from __future__ import annotations

import os
from functools import lru_cache


def _bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@lru_cache
def get_storage_settings() -> dict:
    backend = (os.environ.get("AX_REPORT_STORAGE") or "local").strip().lower()
    return {
        "backend": backend,
        "local_root": os.environ.get("AX_REPORT_LOCAL_ROOT", "").strip(),
        "bucket": os.environ.get("AX_S3_BUCKET", "").strip(),
        "region": os.environ.get("AX_S3_REGION", "us-east-1").strip(),
        "endpoint_url": os.environ.get("AX_S3_ENDPOINT", "").strip() or None,
        "access_key": os.environ.get("AX_S3_ACCESS_KEY", os.environ.get("AWS_ACCESS_KEY_ID", "")).strip(),
        "secret_key": os.environ.get("AX_S3_SECRET_KEY", os.environ.get("AWS_SECRET_ACCESS_KEY", "")).strip(),
        "signed_url_ttl": int(os.environ.get("AX_REPORT_SIGNED_URL_TTL", "3600")),
        "delete_local_after_upload": _bool("AX_REPORT_DELETE_LOCAL_AFTER_UPLOAD"),
    }


def is_storage_key(report_path: str) -> bool:
    """True when ``report_path`` is an object-store prefix, not a local filesystem path."""
    return report_path.startswith("reports/")
