"""AX_BILLING_ENABLED flag: personal default off, SaaS on when enabled."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for sub in ("services/ai_server", "packages", "apps/api", "apps/worker"):
    p = str(ROOT / sub)
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ["AX_JOB_STORE"] = "memory"
os.environ["AX_AUTH_ALLOW_HEADER"] = "true"

from ax_api.main import create_app
from ax_auth.jwt_utils import create_access_token
from ax_billing import is_billing_enabled
from ax_jobs.store import reset_job_store
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def memory_store(monkeypatch):
    monkeypatch.setenv("AX_JOB_STORE", "memory")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("AX_BILLING_ENABLED", raising=False)
    reset_job_store()
    yield
    reset_job_store()


@pytest.fixture
def client():
    return TestClient(create_app())


def test_billing_disabled_by_default(monkeypatch):
    monkeypatch.delenv("AX_BILLING_ENABLED", raising=False)
    assert is_billing_enabled() is False


def test_billing_enabled_truthy(monkeypatch):
    monkeypatch.setenv("AX_BILLING_ENABLED", "true")
    assert is_billing_enabled() is True
    monkeypatch.setenv("AX_BILLING_ENABLED", "1")
    assert is_billing_enabled() is True


def test_auth_config_exposes_billing_enabled(client, monkeypatch):
    monkeypatch.delenv("AX_BILLING_ENABLED", raising=False)
    data = client.get("/api/v1/auth/config").json()
    assert data["billing_enabled"] is False

    monkeypatch.setenv("AX_BILLING_ENABLED", "true")
    data = client.get("/api/v1/auth/config").json()
    assert data["billing_enabled"] is True


def test_presets_unlocked_when_billing_off(client, monkeypatch):
    monkeypatch.setenv("AX_DEFAULT_PLAN_ID", "free")
    monkeypatch.delenv("AX_BILLING_ENABLED", raising=False)
    token = create_access_token(subject="free-user")
    resp = client.get("/api/v1/presets", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    presets = {p["id"]: p for p in resp.json()}
    assert presets["deep"]["locked"] is False


def test_create_deep_ok_when_billing_off(client, monkeypatch):
    monkeypatch.setenv("AX_DEFAULT_PLAN_ID", "free")
    monkeypatch.delenv("AX_BILLING_ENABLED", raising=False)
    token = create_access_token(subject="free-user")
    resp = client.post(
        "/api/v1/analyses",
        headers={"Authorization": f"Bearer {token}"},
        json={"ticker": "AAPL", "analysis_date": "2026-07-29", "preset": "deep"},
    )
    assert resp.status_code == 202
    body = resp.json()
    assert body.get("points_charged") in (None, 0, 0.0)


def test_billing_plans_404_when_off(client, monkeypatch):
    monkeypatch.delenv("AX_BILLING_ENABLED", raising=False)
    assert client.get("/api/v1/billing/plans").status_code == 404


def test_quota_estimate_404_when_off(client, monkeypatch):
    monkeypatch.delenv("AX_BILLING_ENABLED", raising=False)
    resp = client.get("/api/v1/llm/quota-estimate?preset=quick&provider=deepseek")
    assert resp.status_code == 404
