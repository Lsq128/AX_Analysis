"""Domain models for AX analysis jobs (mirrors cli/models.py, AX-owned)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AnalystType(str, Enum):
    MARKET = "market"
    SOCIAL = "social"
    NEWS = "news"
    FUNDAMENTALS = "fundamentals"


class AssetType(str, Enum):
    STOCK = "stock"
    CRYPTO = "crypto"


ANALYST_ORDER = ["market", "social", "news", "fundamentals"]


@dataclass
class AnalysisRequest:
    """Worker-facing input for a single analysis run."""

    ticker: str
    analysis_date: str
    analysts: list[str] = field(default_factory=lambda: ["market"])
    research_depth: int = 1
    asset_type: str | None = None
    llm_provider: str | None = None
    shallow_thinker: str | None = None
    deep_thinker: str | None = None
    backend_url: str | None = None
    output_language: str | None = None
    user_id: str | None = None
    checkpoint: bool | None = None
    save_reports: bool = True
    job_id: str | None = None


@dataclass
class RunStats:
    llm_calls: int = 0
    tool_calls: int = 0
    tokens_in: int = 0
    tokens_out: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RunStats:
        return cls(
            llm_calls=int(data.get("llm_calls", 0)),
            tool_calls=int(data.get("tool_calls", 0)),
            tokens_in=int(data.get("tokens_in", 0)),
            tokens_out=int(data.get("tokens_out", 0)),
        )


@dataclass
class AnalysisResult:
    ticker: str
    analysis_date: str
    final_state: dict[str, Any]
    report_path: str | None
    stats: RunStats
    job_id: str | None = None
