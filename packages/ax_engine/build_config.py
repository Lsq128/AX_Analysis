"""Map Web/Worker selections into TradingAgents DEFAULT_CONFIG."""

from __future__ import annotations

import os
from typing import Any

from ax_dataflows.inject import apply_a_share_vendors
from ax_engine.models import AnalysisRequest
from ax_engine.paths import apply_user_paths, ensure_directories
from ax_engine.ticker import detect_asset_type, filter_analysts_for_asset_type, order_analyst_keys
from tradingagents.default_config import DEFAULT_CONFIG


def selections_from_request(request: AnalysisRequest) -> dict[str, Any]:
    ticker = request.ticker.strip()
    asset_type = request.asset_type or detect_asset_type(ticker).value
    analysts = order_analyst_keys(filter_analysts_for_asset_type(request.analysts, asset_type))

    selections: dict[str, Any] = {
        "ticker": ticker,
        "analysis_date": request.analysis_date,
        "asset_type": asset_type,
        "analysts": analysts,
        "research_depth": request.research_depth,
        "llm_provider": request.llm_provider or DEFAULT_CONFIG["llm_provider"],
        "shallow_thinker": request.shallow_thinker or DEFAULT_CONFIG["quick_think_llm"],
        "deep_thinker": request.deep_thinker or DEFAULT_CONFIG["deep_think_llm"],
        "backend_url": request.backend_url if request.backend_url is not None else DEFAULT_CONFIG.get("backend_url"),
        "output_language": request.output_language or DEFAULT_CONFIG.get("output_language", "English"),
    }
    return selections


def build_config(request: AnalysisRequest) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return (engine_config, selections) with per-user paths applied."""
    selections = selections_from_request(request)
    config = _build_run_config(selections, request.checkpoint)
    config = apply_a_share_vendors(config, selections["ticker"])
    config = apply_user_paths(config, request.user_id)
    ensure_directories(config)
    return config, selections


def _build_run_config(selections: dict[str, Any], checkpoint: bool | None) -> dict[str, Any]:
    """Port of cli/main.py::_build_run_config."""
    config = DEFAULT_CONFIG.copy()
    if not os.environ.get("TRADINGAGENTS_MAX_DEBATE_ROUNDS"):
        config["max_debate_rounds"] = selections["research_depth"]
    if not os.environ.get("TRADINGAGENTS_MAX_RISK_ROUNDS"):
        config["max_risk_discuss_rounds"] = selections["research_depth"]
    config["quick_think_llm"] = selections["shallow_thinker"]
    config["deep_think_llm"] = selections["deep_thinker"]
    config["backend_url"] = selections["backend_url"]
    config["llm_provider"] = str(selections["llm_provider"]).lower()
    config["output_language"] = selections.get("output_language", "English")
    if checkpoint is not None:
        config["checkpoint_enabled"] = checkpoint
    return config
