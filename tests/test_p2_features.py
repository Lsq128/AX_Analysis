"""P2 feature tests: plan gates, ticker search, report export, rate limit."""

from __future__ import annotations

import io
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for sub in ("services/ai_server", "packages", "apps/api", "apps/worker"):
    p = str(ROOT / sub)
    if p not in sys.path:
        sys.path.insert(0, p)

import os

os.environ["AX_JOB_STORE"] = "memory"
os.environ["AX_AUTH_ALLOW_HEADER"] = "true"

from ax_api.main import create_app
from ax_auth.jwt_utils import create_access_token
from ax_billing.plan_gates import is_preset_allowed, locked_presets_for_plan
from ax_jobs.models import AnalysisJobRecord, JobStatus
from ax_jobs.store import get_job_store, reset_job_store
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def memory_store(monkeypatch):
    monkeypatch.setenv("AX_JOB_STORE", "memory")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    reset_job_store()
    yield
    reset_job_store()


@pytest.fixture
def client():
    return TestClient(create_app())


def test_plan_gates_free_blocks_deep():
    assert "deep" in locked_presets_for_plan("free")
    assert not is_preset_allowed("free", "deep")
    assert is_preset_allowed("standard", "deep")


def test_presets_mark_deep_locked_for_free_plan(client, monkeypatch):
    monkeypatch.setenv("AX_BILLING_ENABLED", "true")
    monkeypatch.setenv("AX_DEFAULT_PLAN_ID", "free")
    token = create_access_token(subject="free-user")
    resp = client.get("/api/v1/presets", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    presets = {p["id"]: p for p in resp.json()}
    assert presets["deep"]["locked"] is True
    assert presets["full"]["locked"] is False


def test_create_deep_analysis_forbidden_on_free_plan(client, monkeypatch):
    monkeypatch.setenv("AX_BILLING_ENABLED", "true")
    monkeypatch.setenv("AX_DEFAULT_PLAN_ID", "free")
    token = create_access_token(subject="free-user")
    resp = client.post(
        "/api/v1/analyses",
        headers={"Authorization": f"Bearer {token}"},
        json={"ticker": "AAPL", "analysis_date": "2026-07-29", "preset": "deep"},
    )
    assert resp.status_code == 403
    assert "套餐" in resp.json()["detail"]["message"]


def test_ticker_search_catalog_and_recent(client):
    token = create_access_token(subject="search-user")
    headers = {"Authorization": f"Bearer {token}"}

    client.post(
        "/api/v1/analyses",
        headers=headers,
        json={"ticker": "CUSTOM1", "analysis_date": "2026-07-29", "preset": "quick"},
    )

    resp = client.get("/api/v1/tickers/search?q=茅台", headers=headers)
    assert resp.status_code == 200
    tickers = [item["ticker"] for item in resp.json()]
    assert "600519.SS" in tickers

    resp2 = client.get("/api/v1/tickers/search?q=custom", headers=headers)
    assert any(item["ticker"] == "CUSTOM1" for item in resp2.json())


def test_report_export_zip(client, tmp_path):
    from ax_jobs.store import get_job_store

    root = tmp_path / "report"
    (root / "1_analysts").mkdir(parents=True)
    (root / "1_analysts" / "market.md").write_text("# Market", encoding="utf-8")
    (root / "complete_report.md").write_text("# Complete", encoding="utf-8")

    store = get_job_store()
    job = AnalysisJobRecord.new(
        user_id="export-user",
        ticker="AAPL",
        analysis_date="2026-07-29",
        analysts=["market"],
        research_depth=1,
        preset_id="quick",
    )
    store.create_job(job)
    store.update_job(job.job_id, status=JobStatus.COMPLETED.value, report_path=str(root))

    token = create_access_token(subject="export-user")
    resp = client.get(
        f"/api/v1/analyses/{job.job_id}/report/export",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/zip"

    with zipfile.ZipFile(io.BytesIO(resp.content)) as archive:
        names = archive.namelist()
        assert any("market" in name.lower() or name.endswith(".md") for name in names)


def test_rate_limit_returns_429(client, monkeypatch):
    monkeypatch.setenv("AX_API_RATE_LIMIT_RPM", "2")
    app = create_app()
    limited = TestClient(app)

    for _ in range(2):
        ok = limited.get("/api/v1/llm/providers")
        assert ok.status_code == 200

    blocked = limited.get("/api/v1/llm/providers")
    assert blocked.status_code == 429
    assert "频繁" in blocked.json()["detail"]
