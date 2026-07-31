"""Current user profile and quota."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from ax_api.deps import get_current_user
from ax_api.schemas import UserMeResponse

router = APIRouter(prefix="/me", tags=["me"])


@router.get("", response_model=UserMeResponse)
def get_me(user: Annotated[dict, Depends(get_current_user)]) -> UserMeResponse:
    points_limit = float(user.get("points_limit", 50.0))
    points_used = float(user.get("points_used", 0.0))
    return UserMeResponse(
        user_id=user["external_id"],
        display_name=user.get("display_name") or user["external_id"],
        plan_id=user.get("plan_id", "standard"),
        plan_label=user.get("plan_label", "标准版"),
        points_limit=points_limit,
        points_used=points_used,
        points_remaining=max(0.0, points_limit - points_used),
        is_admin=bool(user.get("is_admin")),
    )
