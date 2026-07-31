"""Subscription plan catalog tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for sub in ("services/ai_server", "packages", "apps/api", "apps/worker"):
    p = str(ROOT / sub)
    if p not in sys.path:
        sys.path.insert(0, p)


def test_list_plans_returns_three():
    from ax_billing.plans import list_plans

    plans = list_plans()
    assert len(plans) == 3
    ids = {p["id"] for p in plans}
    assert ids == {"free", "standard", "pro"}


def test_get_plan_unknown_raises():
    from ax_billing.plans import get_plan

    with pytest.raises(KeyError, match="Unknown plan"):
        get_plan("enterprise")


def test_default_plan_id_env(monkeypatch):
    from ax_billing.plans import default_plan_id, get_plan

    monkeypatch.setenv("AX_DEFAULT_PLAN_ID", "pro")
    assert default_plan_id() == "pro"
    assert get_plan(default_plan_id()).points_limit == 200.0
