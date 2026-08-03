"""LLM provider API routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ax_billing import compute_consumption_points
from ax_llm import list_v1_providers
from ax_presets import get_preset

router = APIRouter(prefix="/llm", tags=["llm"])


class ModelOptionResponse(BaseModel):
    label: str
    id: str


class ProviderDefaultsResponse(BaseModel):
    quick: str
    deep: str


class ProviderResponse(BaseModel):
    id: str
    label: str
    quota_factor: float
    description: str
    models: dict[str, list[ModelOptionResponse]]
    defaults: ProviderDefaultsResponse


class QuotaEstimateResponse(BaseModel):
    preset_id: str
    preset_label: str
    base_points: float
    provider_id: str
    provider_factor: float
    total_points: float


@router.get("/providers", response_model=list[ProviderResponse])
def get_llm_providers() -> list[ProviderResponse]:
    return [ProviderResponse(**item) for item in list_v1_providers()]


@router.get("/quota-estimate", response_model=QuotaEstimateResponse)
def estimate_quota(
    preset: Annotated[str, Query()],
    provider: Annotated[str, Query()] = "deepseek",
) -> QuotaEstimateResponse:
    from ax_billing import is_billing_enabled

    if not is_billing_enabled():
        raise HTTPException(status_code=404, detail="Billing is disabled")

    try:
        p = get_preset(preset)
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    base = float(p.quota_points)
    total = compute_consumption_points(preset_id=preset, llm_provider=provider)
    from ax_llm.v1_providers import PROVIDER_SPECS

    spec = PROVIDER_SPECS.get(provider.lower())
    if not spec:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")

    return QuotaEstimateResponse(
        preset_id=p.id,
        preset_label=p.label,
        base_points=base,
        provider_id=spec.id,
        provider_factor=spec.quota_factor,
        total_points=total,
    )
