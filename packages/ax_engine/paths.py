"""Per-user filesystem paths for multi-tenant SaaS isolation."""

from __future__ import annotations

import os
import re
from pathlib import Path


def safe_path_component(value: str, *, max_len: int = 64) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]", "_", value.strip())
    if not cleaned:
        raise ValueError("path component is empty after sanitization")
    return cleaned[:max_len]


def user_data_paths(user_id: str, base_dir: Path | None = None) -> dict[str, str]:
    """Return engine path overrides for a single tenant."""
    base = base_dir or Path(os.environ.get("AX_DATA_ROOT", ax_data_default_root()))
    root = base / "users" / safe_path_component(user_id)
    return {
        "results_dir": str(root / "logs"),
        "data_cache_dir": str(root / "cache"),
        "memory_log_path": str(root / "memory" / "trading_memory.md"),
    }


def ax_data_default_root() -> Path:
    from ax_engine.env import ax_project_root

    return ax_project_root() / "data"


def apply_user_paths(config: dict, user_id: str | None) -> dict:
    if not user_id:
        return config
    paths = user_data_paths(user_id)
    updated = config.copy()
    updated["results_dir"] = paths["results_dir"]
    updated["data_cache_dir"] = paths["data_cache_dir"]
    updated["memory_log_path"] = paths["memory_log_path"]
    return updated


def ensure_directories(config: dict) -> None:
    for key in ("results_dir", "data_cache_dir", "memory_log_path"):
        path = config.get(key)
        if not path:
            continue
        p = Path(path)
        if key == "memory_log_path":
            p.parent.mkdir(parents=True, exist_ok=True)
        else:
            p.mkdir(parents=True, exist_ok=True)
