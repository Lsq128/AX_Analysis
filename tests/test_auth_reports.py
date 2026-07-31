"""Auth and report API tests."""

from __future__ import annotations

import sys
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
from ax_auth.jwt_utils import create_access_token, subject_from_token
from ax_jobs.store import reset_job_store
from ax_reports.reader import list_available_sections, read_section
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


def test_jwt_roundtrip():
    token = create_access_token(subject="alice", claims={"name": "Alice"})
    assert subject_from_token(token) == "alice"


def test_login_returns_token(client):
    resp = client.post("/api/v1/auth/login", json={"user_id": "alice", "display_name": "Alice"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["user_id"] == "alice"


def test_bearer_auth_for_me(client):
    token = create_access_token(subject="bob")
    resp = client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["user_id"] == "bob"


def test_report_reader(tmp_path):
    root = tmp_path / "report"
    (root / "1_analysts").mkdir(parents=True)
    (root / "1_analysts" / "market.md").write_text("# Market", encoding="utf-8")
    (root / "complete_report.md").write_text("# Complete", encoding="utf-8")

    sections = list_available_sections(str(root))
    keys = {s["key"] for s in sections}
    assert "market" in keys
    assert "complete" in keys

    content = read_section(str(root), "market")
    assert "Market" in content["markdown"]


def test_report_api_requires_completed_job(client):
    # create job
    resp = client.post(
        "/api/v1/analyses",
        headers={"Authorization": f"Bearer {create_access_token(subject='u1')}"},
        json={"ticker": "AAPL", "analysis_date": "2026-07-29", "preset": "quick"},
    )
    job_id = resp.json()["job_id"]
    resp2 = client.get(
        f"/api/v1/analyses/{job_id}/report",
        headers={"Authorization": f"Bearer {create_access_token(subject='u1')}"},
    )
    assert resp2.status_code == 409


def test_signed_urls_not_available_for_local_report(client, tmp_path, monkeypatch):
    from ax_jobs.models import AnalysisJobRecord, JobStatus
    from ax_jobs.store import get_job_store

    root = tmp_path / "report"
    (root / "1_analysts").mkdir(parents=True)
    (root / "1_analysts" / "market.md").write_text("# Market", encoding="utf-8")

    store = get_job_store()
    job = AnalysisJobRecord.new(
        user_id="u1",
        ticker="AAPL",
        analysis_date="2026-07-29",
        analysts=["market"],
        research_depth=1,
        preset_id="quick",
    )
    store.create_job(job)
    store.update_job(job.job_id, status=JobStatus.COMPLETED.value, report_path=str(root))

    resp = client.get(
        f"/api/v1/analyses/{job.job_id}/report/signed-urls",
        headers={"Authorization": f"Bearer {create_access_token(subject='u1')}"},
    )
    assert resp.status_code == 501
