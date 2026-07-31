"""Admin access helpers."""

from __future__ import annotations

import os


def admin_user_ids() -> set[str]:
    raw = os.getenv("AX_ADMIN_USER_IDS", "")
    return {item.strip() for item in raw.split(",") if item.strip()}


def admin_api_key() -> str | None:
    key = os.getenv("AX_ADMIN_API_KEY", "").strip()
    return key or None


def is_admin_user(external_id: str) -> bool:
    return external_id in admin_user_ids()


def verify_admin_api_key(provided: str | None) -> bool:
    expected = admin_api_key()
    return bool(expected and provided and provided == expected)
