"""Analysis job runner — stream path with memory + reports (completeness-audit §7)."""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

from ax_engine.build_config import build_config
from ax_engine.env import ensure_ax_env_loaded
from ax_engine.models import AnalysisRequest, AnalysisResult, RunStats
from ax_engine.progress import RunProgress, process_stream_chunk
from ax_engine.stats import StatsCallbackHandler
from ax_engine.ticker import normalize_ticker_symbol
from tradingagents.graph.analyst_execution import build_analyst_execution_plan, get_initial_analyst_node
from tradingagents.graph.checkpointer import (
    checkpoint_step,
    clear_checkpoint,
    get_checkpointer,
    thread_id,
)
from tradingagents.graph.trading_graph import TradingAgentsGraph

logger = logging.getLogger(__name__)


def run_analysis_job(
    request: AnalysisRequest,
    *,
    on_event: Callable[[dict[str, Any]], None] | None = None,
) -> AnalysisResult:
    """Execute one analysis with graph.stream(), memory log, and report export."""
    ensure_ax_env_loaded()

    ticker = normalize_ticker_symbol(request.ticker)
    config, selections = build_config(
        AnalysisRequest(**{**request.__dict__, "ticker": ticker})
    )

    selected_analyst_keys = selections["analysts"]
    analyst_execution_plan = build_analyst_execution_plan(selected_analyst_keys)
    stats_handler = StatsCallbackHandler()

    graph = TradingAgentsGraph(
        selected_analysts=selected_analyst_keys,
        config=config,
        callbacks=[stats_handler],
    )

    asset_type = selections["asset_type"]
    analysis_date = selections["analysis_date"]
    checkpointer_ctx = None

    try:
        graph._resolve_pending_entries(ticker)

        if config.get("checkpoint_enabled"):
            checkpointer_ctx = get_checkpointer(config["data_cache_dir"], ticker)
            saver = checkpointer_ctx.__enter__()
            graph.graph = graph.workflow.compile(checkpointer=saver)
            step = checkpoint_step(
                config["data_cache_dir"],
                ticker,
                str(analysis_date),
                graph._run_signature(asset_type),
            )
            if step is not None:
                logger.info("Resuming from step %d for %s on %s", step, ticker, analysis_date)
            else:
                logger.info("Starting fresh for %s on %s", ticker, analysis_date)

        past_context = graph.memory_log.get_past_context(ticker)
        instrument_context = graph.resolve_instrument_context(ticker, asset_type)
        init_agent_state = graph.propagator.create_initial_state(
            ticker,
            analysis_date,
            asset_type=asset_type,
            past_context=past_context,
            instrument_context=instrument_context,
        )
        args = graph.propagator.get_graph_args(callbacks=[stats_handler])

        if config.get("checkpoint_enabled"):
            tid = thread_id(ticker, str(analysis_date), graph._run_signature(asset_type))
            args.setdefault("config", {}).setdefault("configurable", {})["thread_id"] = tid

        progress = RunProgress(selected_analyst_keys)
        first_analyst = get_initial_analyst_node(analyst_execution_plan)
        progress.update_agent_status(first_analyst, "in_progress")

        if on_event:
            on_event(
                {
                    "type": "started",
                    "ticker": ticker,
                    "analysis_date": analysis_date,
                    "analysts": selected_analyst_keys,
                }
            )

        trace: list[dict[str, Any]] = []
        for chunk in graph.graph.stream(init_agent_state, **args):
            process_stream_chunk(progress, chunk, on_event=on_event)
            trace.append(chunk)

        final_state: dict[str, Any] = {}
        for chunk in trace:
            final_state.update(chunk)

        for agent in progress.agent_status:
            progress.update_agent_status(agent, "completed")

        decision = final_state.get("final_trade_decision", "")
        if decision:
            graph.memory_log.store_decision(
                ticker=ticker,
                trade_date=analysis_date,
                final_trade_decision=decision,
            )

        report_path: str | None = None
        if request.save_reports:
            report_path = str(graph.save_reports(final_state, ticker))

        if config.get("checkpoint_enabled"):
            clear_checkpoint(
                config["data_cache_dir"],
                ticker,
                str(analysis_date),
                graph._run_signature(asset_type),
            )

        result = AnalysisResult(
            ticker=ticker,
            analysis_date=analysis_date,
            final_state=final_state,
            report_path=report_path,
            stats=RunStats.from_dict(stats_handler.get_stats()),
            job_id=request.job_id,
        )

        if on_event:
            on_event({"type": "completed", "report_path": report_path, "stats": result.stats})

        return result

    finally:
        if checkpointer_ctx is not None:
            checkpointer_ctx.__exit__(None, None, None)
            graph.graph = graph.workflow.compile()


def default_report_path(config: dict[str, Any], ticker: str) -> Path:
    from tradingagents.dataflows.utils import safe_ticker_component

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return (
        Path(config["results_dir"])
        / "reports"
        / f"{safe_ticker_component(ticker)}_{stamp}"
    )
