"""API + worker integration tests (memory store, mocked engine)."""

from __future__ import annotations

import os
import sys
import threading
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
for sub in ("services/ai_server", "packages", "apps/api", "apps/worker"):
    p = str(ROOT / sub)
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ["AX_JOB_STORE"] = "memory"

from ax_api.main import create_app
from ax_engine.models import AnalysisResult, RunStats
from ax_jobs.store import get_job_store, reset_job_store
from ax_worker.consumer import process_job
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def memory_store(monkeypatch):
    monkeypatch.setenv("AX_JOB_STORE", "memory")
    reset_job_store()
    yield
    reset_job_store()


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_list_presets(client):
    resp = client.get("/api/v1/presets")
    assert resp.status_code == 200
    data = resp.json()
    assert any(p["id"] == "quick" for p in data)


def test_list_llm_providers(client):
    resp = client.get("/api/v1/llm/providers")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3
    assert data[0]["id"] in {"deepseek", "qwen-cn", "kimi"}


def test_quota_estimate(client):
    resp = client.get("/api/v1/llm/quota-estimate?preset=full&provider=qwen-cn")
    assert resp.status_code == 200
    data = resp.json()
    assert data["preset_id"] == "full"
    assert data["base_points"] == 2.5
    assert data["provider_factor"] == 1.2
    assert data["total_points"] == 3.0


def test_create_job_with_llm_provider(client):
    resp = client.post(
        "/api/v1/analyses",
        headers={"X-User-Id": "user-1"},
        json={
            "ticker": "600519",
            "analysis_date": "2026-07-29",
            "preset": "full",
            "llm_provider": "qwen-cn",
        },
    )
    assert resp.status_code == 202
    job_id = resp.json()["job_id"]
    job = get_job_store().get_job(job_id)
    assert job is not None
    assert job.run_config is not None
    assert job.run_config["llm_provider"] == "qwen-cn"
    assert job.run_config["shallow_thinker"]
    assert job.run_config["deep_thinker"]


def test_create_and_get_job(client):
    resp = client.post(
        "/api/v1/analyses",
        headers={"X-User-Id": "user-1"},
        json={
            "ticker": "NVDA",
            "analysis_date": "2026-07-29",
            "preset": "quick",
        },
    )
    assert resp.status_code == 202
    job = resp.json()
    assert job["status"] == "queued"
    job_id = job["job_id"]

    resp2 = client.get(f"/api/v1/analyses/{job_id}", headers={"X-User-Id": "user-1"})
    assert resp2.status_code == 200
    assert resp2.json()["job_id"] == job_id


def test_job_not_visible_to_other_user(client):
    resp = client.post(
        "/api/v1/analyses",
        headers={"X-User-Id": "user-1"},
        json={"ticker": "AAPL", "analysis_date": "2026-07-29", "preset": "quick"},
    )
    job_id = resp.json()["job_id"]
    resp2 = client.get(f"/api/v1/analyses/{job_id}", headers={"X-User-Id": "user-2"})
    assert resp2.status_code == 404


@patch("ax_worker.consumer.run_analysis_job")
def test_worker_passes_llm_run_config(mock_run, client):
    mock_run.return_value = AnalysisResult(
        ticker="NVDA",
        analysis_date="2026-07-29",
        final_state={},
        report_path="/tmp/report",
        stats=RunStats(),
        job_id="ignored",
    )
    resp = client.post(
        "/api/v1/analyses",
        headers={"X-User-Id": "user-1"},
        json={
            "ticker": "NVDA",
            "analysis_date": "2026-07-29",
            "preset": "quick",
            "llm_provider": "kimi",
            "shallow_thinker": "kimi-k2-turbo-preview",
            "deep_thinker": "kimi-k2-0711-preview",
        },
    )
    job_id = resp.json()["job_id"]
    process_job(job_id)
    req = mock_run.call_args[0][0]
    assert req.llm_provider == "kimi"
    assert req.shallow_thinker == "kimi-k2-turbo-preview"
    assert req.deep_thinker == "kimi-k2-0711-preview"


@patch("ax_worker.consumer.run_analysis_job")
def test_worker_completes_job(mock_run, client):
    mock_run.return_value = AnalysisResult(
        ticker="NVDA",
        analysis_date="2026-07-29",
        final_state={"final_trade_decision": "**Rating**: Hold\n\nDetails..."},
        report_path="/tmp/report",
        stats=RunStats(llm_calls=1, tool_calls=2, tokens_in=100, tokens_out=50),
        job_id="ignored",
    )

    resp = client.post(
        "/api/v1/analyses",
        headers={"X-User-Id": "user-1"},
        json={"ticker": "NVDA", "analysis_date": "2026-07-29", "preset": "quick"},
    )
    job_id = resp.json()["job_id"]

    thread = threading.Thread(target=process_job, args=(job_id,))
    thread.start()
    thread.join(timeout=10)

    job = get_job_store().get_job(job_id)
    assert job is not None
    assert job.status.value == "completed"
    assert job.report_path == "/tmp/report"
    assert job.decision_preview is not None

    resp2 = client.get(f"/api/v1/analyses/{job_id}", headers={"X-User-Id": "user-1"})
    assert resp2.json()["status"] == "completed"
