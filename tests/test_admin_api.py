"""Admin and billing API tests."""

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
from ax_jobs.store import reset_job_store
from fastapi.testclient import TestClient


@pytest.fixture()
def sqlite_db(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    from ax_db.session import get_database_url, get_engine, init_db

    get_database_url.cache_clear()
    init_db()
    yield
    get_database_url.cache_clear()
    import ax_db.session as sess

    sess._engine = None
    sess._SessionLocal = None


@pytest.fixture(autouse=True)
def memory_store(monkeypatch):
    monkeypatch.setenv("AX_JOB_STORE", "memory")
    monkeypatch.setenv("AX_BILLING_ENABLED", "true")
    monkeypatch.delenv("AX_ADMIN_USER_IDS", raising=False)
    monkeypatch.delenv("AX_ADMIN_API_KEY", raising=False)
    reset_job_store()
    yield
    reset_job_store()


@pytest.fixture
def client(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    return TestClient(create_app())


@pytest.fixture
def db_client(sqlite_db):
    return TestClient(create_app())


def test_billing_plans_public(client):
    resp = client.get("/api/v1/billing/plans")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3
    assert {p["id"] for p in data} == {"free", "standard", "pro"}


def test_admin_forbidden_without_role(client):
    resp = client.get("/api/v1/admin/users", headers={"X-User-Id": "regular-user"})
    assert resp.status_code == 403


def test_admin_users_with_api_key(db_client, monkeypatch):
    monkeypatch.setenv("AX_ADMIN_API_KEY", "secret-admin-key")
    resp = db_client.get("/api/v1/admin/users", headers={"X-Admin-Key": "secret-admin-key"})
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_admin_users_with_admin_user_id(db_client, monkeypatch):
    monkeypatch.setenv("AX_ADMIN_USER_IDS", "admin-alice")
    token = create_access_token(subject="admin-alice")
    resp = db_client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


def test_admin_update_user_plan(db_client, monkeypatch):
    monkeypatch.setenv("AX_ADMIN_API_KEY", "admin-key")
    from ax_db.repository import UserRepository
    from ax_db.session import session_scope

    with session_scope() as session:
        UserRepository(session).get_or_create("bob", display_name="Bob")

    resp = db_client.patch(
        "/api/v1/admin/users/bob/quota",
        headers={"X-Admin-Key": "admin-key"},
        json={"plan_id": "pro"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["plan_id"] == "pro"
    assert data["points_limit"] == 200.0


def test_me_includes_plan_and_admin_flag(db_client, monkeypatch):
    monkeypatch.setenv("AX_ADMIN_USER_IDS", "carol")
    token = create_access_token(subject="carol", claims={"name": "Carol"})
    resp = db_client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["plan_id"] == "standard"
    assert data["plan_label"] == "标准版"
    assert data["is_admin"] is True
