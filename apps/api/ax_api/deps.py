"""FastAPI dependencies."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ax_auth.jwt_utils import allow_header_fallback, subject_from_token
from ax_billing.admin import is_admin_user, verify_admin_api_key
from ax_billing.plans import default_plan_id, get_plan
from ax_db.repository import UserRepository
from ax_db.session import db_enabled, session_scope
from ax_jobs.store import get_job_store

_bearer = HTTPBearer(auto_error=False)


def get_store():
    return get_job_store()


def _resolve_external_id(
    credentials: HTTPAuthorizationCredentials | None,
    x_user_id: str | None,
) -> str:
    if credentials and credentials.credentials:
        return subject_from_token(credentials.credentials)
    if allow_header_fallback() and x_user_id and x_user_id.strip():
        return x_user_id.strip()
    raise HTTPException(status_code=401, detail="Authentication required")


def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    x_user_id: Annotated[str | None, Header(alias="X-User-Id")] = None,
) -> str:
    return _resolve_external_id(credentials, x_user_id)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    x_user_id: Annotated[str | None, Header(alias="X-User-Id")] = None,
):
    external_id = _resolve_external_id(credentials, x_user_id)
    if not db_enabled():
        plan = get_plan(default_plan_id())
        return {
            "external_id": external_id,
            "id": external_id,
            "display_name": external_id,
            "points_limit": plan.points_limit,
            "points_used": 0.0,
            "plan_id": plan.id,
            "plan_label": plan.label,
            "is_admin": is_admin_user(external_id),
        }

    with session_scope() as session:
        user = UserRepository(session).get_or_create(external_id)
        quota = UserRepository(session).get_quota(user.id)
        plan_id = quota.plan_id if quota else "standard"
        plan_label = get_plan(plan_id).label if quota else "标准版"
        return {
            "id": user.id,
            "external_id": user.external_id,
            "display_name": user.display_name,
            "points_limit": quota.points_limit if quota else 50.0,
            "points_used": quota.points_used if quota else 0.0,
            "plan_id": plan_id,
            "plan_label": plan_label,
            "is_admin": is_admin_user(external_id),
        }


def get_optional_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    x_user_id: Annotated[str | None, Header(alias="X-User-Id")] = None,
):
    try:
        return get_current_user(credentials, x_user_id)
    except HTTPException:
        return None


def require_admin(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    x_user_id: Annotated[str | None, Header(alias="X-User-Id")] = None,
    x_admin_key: Annotated[str | None, Header(alias="X-Admin-Key")] = None,
) -> str:
    if verify_admin_api_key(x_admin_key):
        return "admin-api-key"
    external_id = _resolve_external_id(credentials, x_user_id)
    if not is_admin_user(external_id):
        raise HTTPException(status_code=403, detail="Admin access required")
    return external_id


def assert_job_owner(job_user_id: str, current_user_id: str) -> None:
    if job_user_id != current_user_id:
        raise HTTPException(status_code=404, detail="Analysis job not found")
