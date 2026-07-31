"""Database quota and persistence tests."""

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


@pytest.fixture()
def sqlite_db(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("AX_JOB_STORE", "memory")
    from ax_db.session import get_database_url, get_engine, init_db

    get_database_url.cache_clear()
    init_db()
    yield
    get_database_url.cache_clear()
    if get_engine.__module__:
        import ax_db.session as sess

        sess._engine = None
        sess._SessionLocal = None


def test_user_quota_charge(sqlite_db):
    from ax_db.repository import InsufficientQuotaError, UserRepository
    from ax_db.session import session_scope

    with session_scope() as session:
        user = UserRepository(session).get_or_create("test-user")
        UserRepository(session).charge_points(user.id, 2.5)
        quota = UserRepository(session).get_quota(user.id)
        assert quota is not None
        assert quota.points_used == 2.5

    with session_scope() as session:
        user = UserRepository(session).get_by_external_id("test-user")
        assert user is not None
        with pytest.raises(InsufficientQuotaError):
            UserRepository(session).charge_points(user.id, 100.0)


def test_apply_plan_updates_limit(sqlite_db):
    from ax_db.repository import UserRepository
    from ax_db.session import session_scope

    with session_scope() as session:
        user = UserRepository(session).get_or_create("plan-user")
        UserRepository(session).apply_plan(user.id, "pro")
        quota = UserRepository(session).get_quota(user.id)
        assert quota is not None
        assert quota.plan_id == "pro"
        assert quota.points_limit == 200.0


def test_job_repository_roundtrip(sqlite_db):
    from ax_db.repository import JobRepository, UserRepository
    from ax_db.session import session_scope
    from ax_jobs.models import AnalysisJobRecord

    with session_scope() as session:
        user = UserRepository(session).get_or_create("job-user")
        job = AnalysisJobRecord.new(
            user_id="job-user",
            ticker="AAPL",
            analysis_date="2026-07-29",
            analysts=["market"],
            research_depth=1,
            preset_id="quick",
            run_config={
                "llm_provider": "qwen-cn",
                "shallow_thinker": "qwen-plus",
                "deep_thinker": "qwen-max",
            },
        )
        JobRepository(session).save(job, user_uuid=user.id, points_charged=1.2)
        row = JobRepository(session).get(job.job_id)
        assert row is not None
        assert row.ticker == "AAPL"
        assert row.run_config["llm_provider"] == "qwen-cn"
        assert row.points_charged == 1.2
