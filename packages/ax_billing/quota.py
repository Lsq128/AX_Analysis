"""Quota and consumption points for AX SaaS."""

from __future__ import annotations

from ax_llm.v1_providers import provider_quota_factor
from ax_presets import preset_quota_points


def compute_consumption_points(
    *,
    preset_id: str | None = None,
    base_points: float | None = None,
    llm_provider: str | None = None,
) -> float:
    """consumption = preset_base × provider_factor (rounded to 1 decimal)."""
    if base_points is None:
        if not preset_id:
            raise ValueError("preset_id or base_points required")
        base_points = preset_quota_points(preset_id)
    factor = provider_quota_factor(llm_provider)
    return round(float(base_points) * factor, 1)
