"""LLM provider catalog and quota billing tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for sub in ("services/ai_server", "packages", "apps/api", "apps/worker"):
    p = str(ROOT / sub)
    if p not in sys.path:
        sys.path.insert(0, p)

from ax_billing import compute_consumption_points
from ax_llm import list_v1_providers, resolve_llm_selection


def test_list_v1_providers_has_three():
    providers = list_v1_providers()
    ids = {p["id"] for p in providers}
    assert ids == {"deepseek", "qwen-cn", "kimi"}
    for p in providers:
        assert "models" in p and "quick" in p["models"] and "deep" in p["models"]
        assert p["quota_factor"] >= 1.0


def test_compute_consumption_points_preset_factor():
    assert compute_consumption_points(preset_id="quick", llm_provider="deepseek") == 1.0
    assert compute_consumption_points(preset_id="full", llm_provider="qwen-cn") == 3.0
    assert compute_consumption_points(preset_id="deep", llm_provider="kimi") == 4.8


def test_resolve_llm_selection_defaults():
    sel = resolve_llm_selection("deepseek")
    assert sel["llm_provider"] == "deepseek"
    assert sel["shallow_thinker"]
    assert sel["deep_thinker"]


def test_resolve_llm_selection_custom_models():
    sel = resolve_llm_selection(
        "kimi",
        shallow_thinker="kimi-k2-turbo-preview",
        deep_thinker="kimi-k2-0711-preview",
    )
    assert sel["llm_provider"] == "kimi"
    assert sel["shallow_thinker"] == "kimi-k2-turbo-preview"
    assert sel["deep_thinker"] == "kimi-k2-0711-preview"


def test_resolve_llm_selection_rejects_unknown():
    with pytest.raises(ValueError, match="llm_provider must be one of"):
        resolve_llm_selection("openai")
