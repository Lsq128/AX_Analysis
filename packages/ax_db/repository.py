"""User and job persistence."""

from __future__ import annotations

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from ax_billing.plans import default_plan_id, get_plan
from ax_db.models import AnalysisJob, User, UserQuota
from ax_jobs.models import AnalysisJobRecord, JobStatus, utc_now_iso


class UserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_or_create(self, external_id: str, *, display_name: str | None = None) -> User:
        user = self.session.scalar(select(User).where(User.external_id == external_id))
        if user:
            return user
        plan = get_plan(default_plan_id())
        user = User(
            external_id=external_id,
            display_name=display_name or external_id,
        )
        self.session.add(user)
        self.session.flush()
        quota = UserQuota(
            user_id=user.id,
            plan_id=plan.id,
            points_limit=plan.points_limit,
            points_used=0.0,
        )
        self.session.add(quota)
        self.session.flush()
        return user

    def get_by_external_id(self, external_id: str) -> User | None:
        return self.session.scalar(select(User).where(User.external_id == external_id))

    def get_quota(self, user_id: str) -> UserQuota | None:
        return self.session.get(UserQuota, user_id)

    def charge_points(self, user_id: str, amount: float) -> UserQuota:
        quota = self.session.get(UserQuota, user_id)
        if quota is None:
            raise ValueError(f"quota not found for user {user_id}")
        if quota.points_used + amount > quota.points_limit:
            raise InsufficientQuotaError(
                remaining=quota.points_limit - quota.points_used,
                required=amount,
            )
        quota.points_used += amount
        self.session.flush()
        return quota

    def apply_plan(self, user_id: str, plan_id: str) -> UserQuota:
        plan = get_plan(plan_id)
        quota = self.session.get(UserQuota, user_id)
        if quota is None:
            raise ValueError(f"quota not found for user {user_id}")
        quota.plan_id = plan.id
        quota.points_limit = plan.points_limit
        self.session.flush()
        return quota

    def set_quota(
        self,
        user_id: str,
        *,
        plan_id: str | None = None,
        points_limit: float | None = None,
        points_used: float | None = None,
    ) -> UserQuota:
        quota = self.session.get(UserQuota, user_id)
        if quota is None:
            raise ValueError(f"quota not found for user {user_id}")
        if plan_id is not None:
            plan = get_plan(plan_id)
            quota.plan_id = plan.id
            quota.points_limit = plan.points_limit
        if points_limit is not None:
            quota.points_limit = float(points_limit)
        if points_used is not None:
            quota.points_used = max(0.0, float(points_used))
        self.session.flush()
        return quota

    def reset_usage(self, user_id: str) -> UserQuota:
        quota = self.session.get(UserQuota, user_id)
        if quota is None:
            raise ValueError(f"quota not found for user {user_id}")
        quota.points_used = 0.0
        self.session.flush()
        return quota

    def list_users(self, *, limit: int = 50, offset: int = 0) -> list[User]:
        stmt = select(User).order_by(desc(User.created_at)).offset(offset).limit(limit)
        return list(self.session.scalars(stmt))

    def count_users(self) -> int:
        return int(self.session.scalar(select(func.count()).select_from(User)) or 0)

    def sum_points_used(self) -> float:
        value = self.session.scalar(select(func.coalesce(func.sum(UserQuota.points_used), 0.0)))
        return float(value or 0.0)

    def count_jobs(self) -> int:
        return int(self.session.scalar(select(func.count()).select_from(AnalysisJob)) or 0)


class InsufficientQuotaError(Exception):
    def __init__(self, *, remaining: float, required: float) -> None:
        self.remaining = remaining
        self.required = required
        super().__init__(f"insufficient quota: need {required}, remaining {remaining}")


class JobRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, job: AnalysisJobRecord, *, user_uuid: str, points_charged: float = 0.0) -> None:
        row = AnalysisJob(
            job_id=job.job_id,
            user_id=user_uuid,
            ticker=job.ticker,
            analysis_date=job.analysis_date,
            preset_id=job.preset_id,
            analysts=job.analysts,
            research_depth=job.research_depth,
            status=job.status.value if isinstance(job.status, JobStatus) else job.status,
            points_charged=points_charged,
            report_path=job.report_path,
            error=job.error,
            stats=job.stats,
            decision_preview=job.decision_preview,
            run_config=job.run_config,
        )
        self.session.merge(row)
        self.session.flush()

    def get(self, job_id: str) -> AnalysisJob | None:
        return self.session.get(AnalysisJob, job_id)

    def get_for_user(self, job_id: str, user_uuid: str) -> AnalysisJob | None:
        row = self.get(job_id)
        if row and row.user_id == user_uuid:
            return row
        return None

    def list_for_user(
        self,
        user_uuid: str,
        *,
        limit: int = 20,
        status: str | None = None,
    ) -> list[AnalysisJob]:
        stmt = select(AnalysisJob).where(AnalysisJob.user_id == user_uuid)
        if status:
            stmt = stmt.where(AnalysisJob.status == status)
        stmt = stmt.order_by(desc(AnalysisJob.created_at)).limit(limit)
        return list(self.session.scalars(stmt))

    def update(self, job_id: str, **fields) -> AnalysisJob | None:
        row = self.get(job_id)
        if not row:
            return None
        for key, value in fields.items():
            if key == "status" and isinstance(value, JobStatus):
                value = value.value
            setattr(row, key, value)
        self.session.flush()
        return row


def job_row_to_record(row: AnalysisJob, *, external_user_id: str) -> AnalysisJobRecord:
    return AnalysisJobRecord(
        job_id=row.job_id,
        user_id=external_user_id,
        ticker=row.ticker,
        analysis_date=row.analysis_date,
        preset_id=row.preset_id,
        analysts=list(row.analysts or []),
        research_depth=row.research_depth,
        status=JobStatus(row.status),
        created_at=row.created_at.isoformat() if row.created_at else utc_now_iso(),
        updated_at=row.updated_at.isoformat() if row.updated_at else utc_now_iso(),
        report_path=row.report_path,
        error=row.error,
        stats=row.stats,
        decision_preview=row.decision_preview,
        run_config=row.run_config,
    )