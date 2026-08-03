"""Public billing plan routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ax_api.schemas import BillingPlanResponse
from ax_billing import is_billing_enabled, list_plans

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/plans", response_model=list[BillingPlanResponse])
def get_billing_plans() -> list[BillingPlanResponse]:
    if not is_billing_enabled():
        raise HTTPException(status_code=404, detail="Billing is disabled")
    return [BillingPlanResponse(**item) for item in list_plans()]
