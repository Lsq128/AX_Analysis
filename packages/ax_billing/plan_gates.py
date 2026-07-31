"""Plan-based feature gates."""

from __future__ import annotations

# Presets blocked per subscription plan (wireframe: free cannot run deep).
LOCKED_PRESETS_BY_PLAN: dict[str, frozenset[str]] = {
    "free": frozenset({"deep"}),
}


def locked_presets_for_plan(plan_id: str) -> frozenset[str]:
    return LOCKED_PRESETS_BY_PLAN.get(plan_id, frozenset())


def is_preset_allowed(plan_id: str, preset_id: str) -> bool:
    return preset_id not in locked_presets_for_plan(plan_id)
