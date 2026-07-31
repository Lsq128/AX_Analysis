"""Load AX_Analysis environment before importing tradingagents."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

_LOADED = False


def ax_project_root() -> Path:
    """Return AX_Analysis repo root (parent of packages/)."""
    return Path(__file__).resolve().parents[2]


def load_ax_env(*, allow_parent_fallback: bool = True) -> Path:
    """Load ``AX_Analysis/.env`` once; optionally fall back to repo-root ``.env`` for dev."""
    global _LOADED
    root = ax_project_root()
    env_path = root / ".env"
    load_dotenv(env_path, override=False)
    if allow_parent_fallback and not _has_llm_key():
        parent_env = root.parent / ".env"
        if parent_env.is_file():
            load_dotenv(parent_env, override=False)
    _LOADED = True
    return env_path


def _has_llm_key() -> bool:
    keys = (
        "DEEPSEEK_API_KEY",
        "DASHSCOPE_CN_API_KEY",
        "MOONSHOT_API_KEY",
        "OPENAI_API_KEY",
    )
    return any(os.environ.get(k) for k in keys)


def ensure_ax_env_loaded() -> None:
    if not _LOADED:
        load_ax_env()
