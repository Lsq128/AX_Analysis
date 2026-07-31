"""Unit tests for ax_engine and ax_presets (no LLM calls)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for sub in ("services/ai_server", "packages"):
    p = str(ROOT / sub)
    if p not in sys.path:
        sys.path.insert(0, p)

from ax_engine.build_config import build_config, selections_from_request
from ax_engine.models import AnalysisRequest
from ax_engine.paths import safe_path_component, user_data_paths
from ax_engine.progress import RunProgress, process_stream_chunk, update_analyst_statuses
from ax_engine.ticker import detect_asset_type, filter_analysts_for_asset_type, order_analyst_keys
from ax_presets import expand_preset, get_preset, list_presets


def test_expand_preset_full():
    params = expand_preset("full")
    assert params["research_depth"] == 3
    assert set(params["analysts"]) == {"market", "social", "news", "fundamentals"}


def test_get_preset_unknown_raises():
    try:
        get_preset("not-a-preset")
        assert False, "expected KeyError"
    except KeyError as exc:
        assert "not-a-preset" in str(exc)


def test_list_presets_non_empty():
    assert len(list_presets()) >= 5


def test_order_analyst_keys():
    assert order_analyst_keys(["fundamentals", "market"]) == ["market", "fundamentals"]


def test_filter_crypto_drops_fundamentals():
    filtered = filter_analysts_for_asset_type(
        ["market", "fundamentals", "news"], "crypto"
    )
    assert "fundamentals" not in filtered


def test_detect_btc_is_crypto():
    assert detect_asset_type("BTC-USD").value == "crypto"


def test_build_config_respects_research_depth(monkeypatch):
    monkeypatch.delenv("TRADINGAGENTS_MAX_DEBATE_ROUNDS", raising=False)
    monkeypatch.delenv("TRADINGAGENTS_MAX_RISK_ROUNDS", raising=False)
    req = AnalysisRequest(ticker="AAPL", analysis_date="2026-07-29", research_depth=5)
    config, selections = build_config(req)
    assert config["max_debate_rounds"] == 5
    assert config["max_risk_discuss_rounds"] == 5
    assert selections["asset_type"] == "stock"


def test_user_paths_isolated(tmp_path):
    paths_a = user_data_paths("user-a", base_dir=tmp_path)
    paths_b = user_data_paths("user-b", base_dir=tmp_path)
    assert paths_a["memory_log_path"] != paths_b["memory_log_path"]
    assert "user-a" in paths_a["data_cache_dir"]
    assert "user-b" in paths_b["data_cache_dir"]


def test_build_config_applies_user_paths(tmp_path, monkeypatch):
    monkeypatch.setenv("AX_DATA_ROOT", str(tmp_path))
    req = AnalysisRequest(
        ticker="0700.HK",
        analysis_date="2026-07-29",
        user_id="u1",
    )
    config, _ = build_config(req)
    assert "/users/u1/" in config["data_cache_dir"].replace("\\", "/")


def test_safe_path_component_rejects_empty():
    try:
        safe_path_component("   ")
        assert False
    except ValueError:
        pass


def test_progress_marks_analyst_completed_on_report():
    progress = RunProgress(["market", "news"])
    update_analyst_statuses(progress, {"market_report": "rsi looks strong"})
    assert progress.agent_status["Market Analyst"] == "completed"
    assert progress.agent_status["News Analyst"] == "in_progress"


def test_process_stream_chunk_emits_events():
    progress = RunProgress(["market"])
    events: list[dict] = []
    process_stream_chunk(
        progress,
        {"market_report": "hello"},
        on_event=events.append,
    )
    assert any(e.get("type") == "progress" for e in events)


def test_debate_timeline_from_research_and_risk():
    progress = RunProgress(["market"])
    chunk = {
        "market_report": "## Market\nStrong trend",
        "investment_debate_state": {
            "bull_history": "Bull case for growth",
            "bear_history": "Bear case on valuation",
            "judge_decision": "**Rating**: Overweight",
            "count": 2,
        },
        "trader_investment_plan": "Buy on dips",
        "risk_debate_state": {
            "aggressive_history": "Go bigger",
            "conservative_history": "Reduce risk",
            "neutral_history": "Balanced view",
            "judge_decision": "Final hold",
            "count": 3,
        },
    }
    process_stream_chunk(progress, chunk)
    ids = {entry["id"] for entry in progress.debate_timeline}
    assert "market_report" in ids
    assert "research-bull" in ids
    assert "research-bear" in ids
    assert "research-manager" in ids
    assert "trader-plan" in ids
    assert "risk-aggressive" in ids
    assert "portfolio-decision" in ids
    bull = next(e for e in progress.debate_timeline if e["id"] == "research-bull")
    assert bull["side"] == "bull"
    assert bull["act"] == "research"
