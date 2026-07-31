"""Public billing plan routes."""

from __future__ import annotations

from fastapi import APIRouter

from ax_api.schemas import BillingPlanResponse
from ax_billing import list_plans

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/plans", response_model=list[BillingPlanResponse])
def get_billing_plans() -> list[BillingPlanResponse]:
    return [BillingPlanResponse(**item) for item in list_plans()]
