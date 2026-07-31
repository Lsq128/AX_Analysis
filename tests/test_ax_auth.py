"""Production auth settings and OAuth tests."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
for sub in ("services/ai_server", "packages", "apps/api", "apps/worker"):
    p = str(ROOT / sub)
    if p not in sys.path:
        sys.path.insert(0, p)

import os

os.environ["AX_JOB_STORE"] = "memory"

from ax_api.main import create_app
from ax_auth.jwt_utils import create_access_token
from ax_auth.oauth import create_oauth_state, verify_oauth_state
from ax_jobs.store import reset_job_store
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


def test_auth_config_defaults(client):
    resp = client.get("/api/v1/auth/config")
    assert resp.status_code == 200
    data = resp.json()
    assert data["dev_mode"] is True
    assert data["dev_login"] is True
    assert data["header_fallback"] is True


def test_header_fallback_disabled(client, monkeypatch):
    monkeypatch.setenv("AX_AUTH_ALLOW_HEADER", "false")
    resp = client.get("/api/v1/me", headers={"X-User-Id": "someone"})
    assert resp.status_code == 401


def test_dev_login_disabled_in_production(client, monkeypatch):
    monkeypatch.setenv("AX_AUTH_DEV_MODE", "false")
    monkeypatch.setenv("AX_AUTH_DEV_LOGIN", "false")
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    resp = client.post(
        "/api/v1/auth/login",
        json={"user_id": "alice", "display_name": "Alice"},
    )
    assert resp.status_code == 403


def test_oauth_state_roundtrip():
    state = create_oauth_state("github")
    verify_oauth_state(state, "github")


@patch("ax_auth.oauth.httpx.Client")
def test_github_oauth_callback(mock_client_cls, client, monkeypatch):
    monkeypatch.setenv("AX_OAUTH_PROVIDERS", "github")
    monkeypatch.setenv("OAUTH_GITHUB_CLIENT_ID", "cid")
    monkeypatch.setenv("OAUTH_GITHUB_CLIENT_SECRET", "secret")
    monkeypatch.setenv("AX_WEB_URL", "http://localhost:3000")
    monkeypatch.setenv("JWT_SECRET", "test-secret")

    mock_client = MagicMock()
    mock_client_cls.return_value.__enter__.return_value = mock_client
    mock_client.post.return_value.json.return_value = {"access_token": "gh-token"}
    mock_client.post.return_value.raise_for_status = MagicMock()
    mock_client.get.return_value.json.return_value = {
        "id": 42,
        "login": "alice",
        "name": "Alice",
        "email": "alice@example.com",
    }
    mock_client.get.return_value.raise_for_status = MagicMock()

    state = create_oauth_state("github")
    resp = client.get(
        f"/api/v1/auth/oauth/github/callback?code=abc&state={state}",
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert "/login/callback?" in resp.headers["location"]
    assert "access_token=" in resp.headers["location"]
    assert "github%3A42" in resp.headers["location"] or "github:42" in resp.headers["location"]


def test_oauth_start_redirects(client, monkeypatch):
    monkeypatch.setenv("AX_OAUTH_PROVIDERS", "github")
    monkeypatch.setenv("OAUTH_GITHUB_CLIENT_ID", "cid")
    monkeypatch.setenv("OAUTH_GITHUB_CLIENT_SECRET", "secret")
    monkeypatch.setenv("JWT_SECRET", "test-secret")

    resp = client.get("/api/v1/auth/oauth/github/start", follow_redirects=False)
    assert resp.status_code == 302
    assert "github.com/login/oauth/authorize" in resp.headers["location"]
