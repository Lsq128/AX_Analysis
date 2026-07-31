"""UI analysis presets → engine parameters."""

from __future__ import annotations

from dataclasses import dataclass

from ax_engine.models import ANALYST_ORDER


@dataclass(frozen=True)
class AnalysisPreset:
    id: str
    label: str
    analysts: tuple[str, ...]
    research_depth: int
    quota_points: float
    eta_minutes: int
    description: str = ""


PRESETS: dict[str, AnalysisPreset] = {
    "quick": AnalysisPreset("quick", "快速诊股", ("market",), 1, 1.0, 5, "技术面快速扫描"),
    "technical": AnalysisPreset("technical", "技术趋势", ("market",), 1, 1.0, 5, "趋势与关键价位"),
    "news_sentiment": AnalysisPreset(
        "news_sentiment", "资讯舆情", ("news", "social"), 1, 1.5, 8, "新闻与市场情绪"
    ),
    "value": AnalysisPreset(
        "value", "价值深挖", ("market", "fundamentals"), 3, 2.0, 12, "基本面 + 技术面"
    ),
    "full": AnalysisPreset(
        "full",
        "全面研判",
        tuple(ANALYST_ORDER),
        3,
        2.5,
        15,
        "四维分析师 + 多空辩论 + 风控",
    ),
    "deep": AnalysisPreset(
        "deep", "深度推演", tuple(ANALYST_ORDER), 5, 4.0, 25, "最高深度，适合重大决策"
    ),
    "crypto": AnalysisPreset(
        "crypto", "数字资产快览", ("market", "news", "social"), 1, 1.0, 8, "加密资产专项"
    ),
}


def get_preset(preset_id: str) -> AnalysisPreset:
    try:
        return PRESETS[preset_id]
    except KeyError as exc:
        valid = ", ".join(sorted(PRESETS))
        raise KeyError(f"Unknown preset {preset_id!r}. Valid: {valid}") from exc


def expand_preset(preset_id: str) -> dict[str, object]:
    preset = get_preset(preset_id)
    return {
        "analysts": list(preset.analysts),
        "research_depth": preset.research_depth,
        "preset_id": preset.id,
        "preset_label": preset.label,
        "quota_points": preset.quota_points,
    }


def preset_quota_points(preset_id: str) -> float:
    return get_preset(preset_id).quota_points


def list_presets() -> list[dict[str, object]]:
    return [
        {
            "id": p.id,
            "label": p.label,
            "analysts": list(p.analysts),
            "research_depth": p.research_depth,
            "quota_points": p.quota_points,
            "eta_minutes": p.eta_minutes,
            "description": p.description,
        }
        for p in PRESETS.values()
    ]
