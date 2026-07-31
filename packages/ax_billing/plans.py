"""Subscription plan catalog for AX SaaS billing."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class SubscriptionPlan:
    id: str
    label: str
    points_limit: float
    price_cny: float
    description: str


PLANS: dict[str, SubscriptionPlan] = {
    "free": SubscriptionPlan(
        "free",
        "体验版",
        10.0,
        0.0,
        "新用户试用，适合单次快速诊股",
    ),
    "standard": SubscriptionPlan(
        "standard",
        "标准版",
        50.0,
        49.0,
        "个人投资者主力套餐，覆盖日常研判",
    ),
    "pro": SubscriptionPlan(
        "pro",
        "专业版",
        200.0,
        199.0,
        "高频深度分析，适合活跃交易者",
    ),
}


def default_plan_id() -> str:
    return os.getenv("AX_DEFAULT_PLAN_ID", "standard").strip() or "standard"


def get_plan(plan_id: str) -> SubscriptionPlan:
    try:
        return PLANS[plan_id]
    except KeyError as exc:
        valid = ", ".join(sorted(PLANS))
        raise KeyError(f"Unknown plan {plan_id!r}. Valid: {valid}") from exc


def list_plans() -> list[dict]:
    return [
        {
            "id": p.id,
            "label": p.label,
            "points_limit": p.points_limit,
            "price_cny": p.price_cny,
            "description": p.description,
        }
        for p in PLANS.values()
    ]
