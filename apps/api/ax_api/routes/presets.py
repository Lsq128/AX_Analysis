"""Preset listing route."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from ax_api.deps import get_optional_user
from ax_api.schemas import PresetResponse
from ax_billing.plan_gates import locked_presets_for_plan
from ax_presets import list_presets

router = APIRouter(prefix="/presets", tags=["presets"])


@router.get("", response_model=list[PresetResponse])
def get_presets(user: Annotated[dict | None, Depends(get_optional_user)] = None) -> list[PresetResponse]:
    plan_id = user.get("plan_id", "standard") if user else "standard"
    locked = locked_presets_for_plan(plan_id)
    out: list[PresetResponse] = []
    for item in list_presets():
        data = dict(item)
        data["locked"] = item["id"] in locked
        out.append(PresetResponse(**data))
    return out
