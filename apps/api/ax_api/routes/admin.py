"""Admin routes for user quota and billing management."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from ax_api.deps import require_admin
from ax_api.schemas import (
    AdminQuotaUpdateRequest,
    AdminStatsResponse,
    AdminUserResponse,
    BillingPlanResponse,
)
from ax_billing import get_plan, list_plans
from ax_db.repository import UserRepository
from ax_db.session import db_enabled, session_scope

router = APIRouter(prefix="/admin", tags=["admin"])


def _require_db() -> None:
    if not db_enabled():
        raise HTTPException(status_code=503, detail="Admin requires DATABASE_URL")


def _user_to_admin_response(user, quota) -> AdminUserResponse:
    plan_id = quota.plan_id if quota else "standard"
    plan_label = get_plan(plan_id).label
    points_limit = float(quota.points_limit if quota else 0.0)
    points_used = float(quota.points_used if quota else 0.0)
    return AdminUserResponse(
        user_id=user.external_id,
        display_name=user.display_name,
        plan_id=plan_id,
        plan_label=plan_label,
        points_limit=points_limit,
        points_used=points_used,
        points_remaining=max(0.0, points_limit - points_used),
        created_at=user.created_at.isoformat() if user.created_at else None,
    )


@router.get("/plans", response_model=list[BillingPlanResponse])
def admin_list_plans(_admin: Annotated[str, Depends(require_admin)]) -> list[BillingPlanResponse]:
    return [BillingPlanResponse(**item) for item in list_plans()]


@router.get("/stats", response_model=AdminStatsResponse)
def admin_stats(_admin: Annotated[str, Depends(require_admin)]) -> AdminStatsResponse:
    _require_db()
    with session_scope() as session:
        repo = UserRepository(session)
        return AdminStatsResponse(
            user_count=repo.count_users(),
            job_count=repo.count_jobs(),
            total_points_used=repo.sum_points_used(),
        )


@router.get("/users", response_model=list[AdminUserResponse])
def admin_list_users(
    _admin: Annotated[str, Depends(require_admin)],
    limit: int = 50,
    offset: int = 0,
) -> list[AdminUserResponse]:
    _require_db()
    with session_scope() as session:
        repo = UserRepository(session)
        users = repo.list_users(limit=min(limit, 100), offset=max(offset, 0))
        out: list[AdminUserResponse] = []
        for user in users:
            quota = repo.get_quota(user.id)
            out.append(_user_to_admin_response(user, quota))
        return out


@router.patch("/users/{external_id}/quota", response_model=AdminUserResponse)
def admin_update_user_quota(
    external_id: str,
    body: AdminQuotaUpdateRequest,
    _admin: Annotated[str, Depends(require_admin)],
) -> AdminUserResponse:
    _require_db()
    with session_scope() as session:
        repo = UserRepository(session)
        user = repo.get_by_external_id(external_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if body.reset_usage:
            repo.reset_usage(user.id)
        elif body.plan_id:
            try:
                repo.apply_plan(user.id, body.plan_id)
            except KeyError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
        elif body.points_limit is not None or body.points_used is not None:
            repo.set_quota(
                user.id,
                points_limit=body.points_limit,
                points_used=body.points_used,
            )

        quota = repo.get_quota(user.id)
        return _user_to_admin_response(user, quota)
