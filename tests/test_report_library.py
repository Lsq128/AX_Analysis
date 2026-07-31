"""Report library API tests."""

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


def _completed_job(user_id: str, ticker: str, *, report_path: str | None) -> AnalysisJobRecord:
    job = AnalysisJobRecord.new(
        user_id=user_id,
        ticker=ticker,
        analysis_date="2026-07-29",
        analysts=["market"],
        research_depth=1,
        preset_id="full",
    )
    store = get_job_store()
    store.create_job(job)
    store.update_job(
        job.job_id,
        status=JobStatus.COMPLETED.value,
        report_path=report_path,
        decision_preview="Rating: Overweight\n建议分批布局。",
    )
    return job


def test_list_reports_only_completed_with_path(client):
    _completed_job("alice", "AAPL", report_path="/tmp/report-aapl")
    _completed_job("alice", "NVDA", report_path=None)
    running = AnalysisJobRecord.new(
        user_id="alice",
        ticker="TSLA",
        analysis_date="2026-07-29",
        analysts=["market"],
        research_depth=1,
    )
    get_job_store().create_job(running)

    resp = client.get("/api/v1/reports", headers={"X-User-Id": "alice"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["ticker"] == "AAPL"
    assert data[0]["report_path"] == "/tmp/report-aapl"


def test_list_analyses_memory_store(client):
    _completed_job("bob", "600519.SS", report_path="/tmp/report-maotai")

    resp = client.get("/api/v1/analyses", headers={"X-User-Id": "bob"})
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = client.get("/api/v1/analyses?status=completed", headers={"X-User-Id": "bob"})
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = client.get("/api/v1/analyses?status=running", headers={"X-User-Id": "bob"})
    assert resp.status_code == 200
    assert resp.json() == []


def test_reports_scoped_to_user(client):
    _completed_job("alice", "AAPL", report_path="/tmp/a")
    _completed_job("carol", "MSFT", report_path="/tmp/b")

    resp = client.get("/api/v1/reports", headers={"X-User-Id": "carol"})
    assert resp.status_code == 200
    tickers = {item["ticker"] for item in resp.json()}
    assert tickers == {"MSFT"}
