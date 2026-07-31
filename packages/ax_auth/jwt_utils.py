"""JWT authentication helpers for AX API."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import HTTPException

DEFAULT_EXPIRE_HOURS = 168  # 7 days


def jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET")
    if not secret:
        if os.getenv("AX_AUTH_DEV_MODE", "true").lower() in ("true", "1", "yes"):
            return "ax-dev-insecure-secret-change-in-production"
        raise RuntimeError("JWT_SECRET is required when AX_AUTH_DEV_MODE is disabled")
    return secret


def jwt_expire_hours() -> int:
    raw = os.getenv("JWT_EXPIRE_HOURS")
    return int(raw) if raw else DEFAULT_EXPIRE_HOURS


from ax_auth.settings import allow_header_fallback


def create_access_token(*, subject: str, claims: dict[str, Any] | None = None) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + timedelta(hours=jwt_expire_hours()),
    }
    if claims:
        payload.update(claims)
    return jwt.encode(payload, jwt_secret(), algorithm="HS256")


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, jwt_secret(), algorithms=["HS256"])
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=401, detail="Token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc


def subject_from_token(token: str) -> str:
    payload = decode_access_token(token)
    sub = payload.get("sub")
    if not sub or not isinstance(sub, str):
        raise HTTPException(status_code=401, detail="Invalid token subject")
    return sub
