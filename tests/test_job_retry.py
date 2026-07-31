"""Job retry and error classification tests."""

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
from ax_jobs.errors import classify_job_error
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


def test_classify_rate_limit():
    info = classify_job_error("OpenAI 429 rate limit exceeded")
    assert info.code == "rate_limited"
    assert info.retryable is True


def test_classify_quota_not_retryable():
    info = classify_job_error("insufficient quota: need 4, remaining 1")
    assert info.code == "quota_exceeded"
    assert info.retryable is False


def test_retry_failed_job(client):
    job = AnalysisJobRecord.new(
        user_id="alice",
        ticker="NVDA",
        analysis_date="2026-07-29",
        analysts=["market"],
        research_depth=1,
    )
    store = get_job_store()
    store.create_job(job)
    store.update_job(job.job_id, status=JobStatus.FAILED.value, error="Connection timeout")

    resp = client.post(
        f"/api/v1/analyses/{job.job_id}/retry",
        headers={"X-User-Id": "alice"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "queued"
    assert data.get("error") is None


def test_retry_non_retryable_rejected(client):
    job = AnalysisJobRecord.new(
        user_id="bob",
        ticker="AAPL",
        analysis_date="2026-07-29",
        analysts=["market"],
        research_depth=1,
    )
    store = get_job_store()
    store.create_job(job)
    store.update_job(job.job_id, status=JobStatus.FAILED.value, error="insufficient quota")

    resp = client.post(
        f"/api/v1/analyses/{job.job_id}/retry",
        headers={"X-User-Id": "bob"},
    )
    assert resp.status_code == 400


def test_recent_tickers(client):
    store = get_job_store()
    for ticker in ("600519.SS", "NVDA", "600519.SS"):
        job = AnalysisJobRecord.new(
            user_id="carol",
            ticker=ticker,
            analysis_date="2026-07-29",
            analysts=["market"],
            research_depth=1,
        )
        store.create_job(job)
        if ticker == "NVDA":
            store.update_job(job.job_id, status=JobStatus.COMPLETED.value, report_path="/tmp/r")

    resp = client.get("/api/v1/tickers/recent", headers={"X-User-Id": "carol"})
    assert resp.status_code == 200
    tickers = [item["ticker"] for item in resp.json()]
    assert tickers[0] in {"NVDA", "600519.SS"}
    assert len(tickers) == 2
