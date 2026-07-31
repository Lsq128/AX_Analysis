"""Memory log reader and API tests."""

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
from ax_jobs.store import reset_job_store
from fastapi.testclient import TestClient

SAMPLE_MEMORY = """\
[2026-07-20 | AAPL | Overweight | pending]

DECISION:
Rating: Overweight
建议分批布局。

<!-- ENTRY_END -->

[2026-07-10 | NVDA | Hold | +12.3% | +4.1% | 14d]

DECISION:
Rating: Hold
观望等待财报。

REFLECTION:
批价逻辑基本正确，但低估了 AI  capex 增速。

<!-- ENTRY_END -->
"""


@pytest.fixture(autouse=True)
def memory_store(monkeypatch):
    monkeypatch.setenv("AX_JOB_STORE", "memory")
    reset_job_store()
    yield
    reset_job_store()


@pytest.fixture
def data_root(tmp_path, monkeypatch):
    monkeypatch.setenv("AX_DATA_ROOT", str(tmp_path))
    return tmp_path


@pytest.fixture
def client():
    return TestClient(create_app())


def _write_user_memory(root: Path, user_id: str, content: str) -> None:
    log_path = root / "users" / user_id / "memory" / "trading_memory.md"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(content, encoding="utf-8")


def test_load_user_entries_newest_first(data_root):
    _write_user_memory(data_root, "alice", SAMPLE_MEMORY)
    from ax_memory import load_user_entries, memory_stats

    entries = load_user_entries("alice")
    assert len(entries) == 2
    assert entries[0]["ticker"] == "AAPL"
    assert entries[0]["pending"] is True
    assert entries[0]["rating_label"] == "增持"
    assert entries[1]["ticker"] == "NVDA"
    assert entries[1]["pending"] is False
    assert entries[1]["raw_return"] == "+12.3%"
    assert entries[1]["holding_days"] == 14
    assert "批价逻辑" in entries[1]["reflection"]

    stats = memory_stats(entries)
    assert stats["total_entries"] == 2
    assert stats["pending_count"] == 1
    assert stats["resolved_count"] == 1
    assert stats["tickers_pending"] == ["AAPL"]


def test_memory_api_list_and_filter(data_root, client):
    _write_user_memory(data_root, "bob", SAMPLE_MEMORY)
    headers = {"X-User-Id": "bob"}

    resp = client.get("/api/v1/memory/entries", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2

    resp = client.get("/api/v1/memory/entries?status=pending", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["ticker"] == "AAPL"

    resp = client.get("/api/v1/memory/stats", headers=headers)
    assert resp.status_code == 200
    stats = resp.json()
    assert stats["pending_count"] == 1
    assert stats["resolved_count"] == 1


def test_memory_api_empty_for_new_user(data_root, client):
    resp = client.get("/api/v1/memory/entries", headers={"X-User-Id": "new-user"})
    assert resp.status_code == 200
    assert resp.json() == []

    resp = client.get("/api/v1/memory/stats", headers={"X-User-Id": "new-user"})
    assert resp.status_code == 200
    assert resp.json()["total_entries"] == 0
