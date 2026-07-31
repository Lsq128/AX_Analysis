"""Pydantic schemas for AX API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, model_validator


class CreateAnalysisRequest(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=32)
    analysis_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    preset: str | None = None
    analysts: list[str] | None = None
    research_depth: int | None = Field(default=None, ge=1, le=5)
    llm_provider: str | None = None
    shallow_thinker: str | None = None
    deep_thinker: str | None = None

    @model_validator(mode="after")
    def preset_or_custom(self) -> CreateAnalysisRequest:
        if self.preset:
            return self
        if not self.analysts:
            raise ValueError("Either preset or analysts must be provided")
        if self.research_depth is None:
            raise ValueError("research_depth is required when preset is omitted")
        return self


class AnalysisJobResponse(BaseModel):
    job_id: str
    user_id: str
    ticker: str
    analysis_date: str
    preset_id: str | None
    analysts: list[str]
    research_depth: int
    status: str
    created_at: str
    updated_at: str
    report_path: str | None = None
    error: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    retryable: bool | None = None
    stats: dict[str, Any] | None = None
    decision_preview: str | None = None
    points_charged: float | None = None


class RecentTickerResponse(BaseModel):
    ticker: str
    last_analysis_date: str
    last_job_id: str
    last_status: str


class TickerSearchResult(BaseModel):
    ticker: str
    name: str | None = None
    market: str | None = None
    source: str = "catalog"


class PresetResponse(BaseModel):
    id: str
    label: str
    analysts: list[str]
    research_depth: int
    quota_points: float
    eta_minutes: int
    description: str
    locked: bool = False


class UserMeResponse(BaseModel):
    user_id: str
    display_name: str
    plan_id: str = "standard"
    plan_label: str = "标准版"
    points_limit: float
    points_used: float
    points_remaining: float
    is_admin: bool = False


class BillingPlanResponse(BaseModel):
    id: str
    label: str
    points_limit: float
    price_cny: float
    description: str


class AdminUserResponse(BaseModel):
    user_id: str
    display_name: str
    plan_id: str
    plan_label: str
    points_limit: float
    points_used: float
    points_remaining: float
    created_at: str | None = None


class AdminStatsResponse(BaseModel):
    user_count: int
    job_count: int
    total_points_used: float


class AdminQuotaUpdateRequest(BaseModel):
    plan_id: str | None = None
    points_limit: float | None = Field(default=None, ge=0)
    points_used: float | None = Field(default=None, ge=0)
    reset_usage: bool = False


class MemoryEntryResponse(BaseModel):
    id: str
    date: str
    ticker: str
    rating: str
    rating_label: str
    pending: bool
    raw_return: str | None = None
    alpha_return: str | None = None
    holding_days: int | None = None
    decision: str
    reflection: str


class MemoryStatsResponse(BaseModel):
    total_entries: int
    pending_count: int
    resolved_count: int
    tickers_pending: list[str]
