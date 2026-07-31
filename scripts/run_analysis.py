#!/usr/bin/env python3
"""Run a single AX analysis job from the command line (dev / smoke test)."""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

# Allow running before `pip install -e .`
_ROOT = Path(__file__).resolve().parents[1]
for sub in ("services/ai_server", "packages"):
    p = str(_ROOT / sub)
    if p not in sys.path:
        sys.path.insert(0, p)

from ax_engine import AnalysisRequest, load_ax_env, run_analysis_job
from ax_presets import expand_preset, list_presets


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Run one AX analysis job")
    parser.add_argument("ticker", nargs="?", default="NVDA", help="Ticker symbol")
    parser.add_argument(
        "--date",
        default=str(date.today()),
        help="Analysis date YYYY-MM-DD",
    )
    parser.add_argument(
        "--preset",
        default="quick",
        help=f"Preset id ({', '.join(p['id'] for p in list_presets())})",
    )
    parser.add_argument("--user-id", default=None, help="Tenant user id for isolated paths")
    parser.add_argument("--no-save", action="store_true", help="Skip write_report_tree")
    parser.add_argument("--json-events", action="store_true", help="Print stream events as JSON lines")
    args = parser.parse_args()

    load_ax_env()
    preset = expand_preset(args.preset)

    request = AnalysisRequest(
        ticker=args.ticker,
        analysis_date=args.date,
        analysts=list(preset["analysts"]),  # type: ignore[arg-type]
        research_depth=int(preset["research_depth"]),
        user_id=args.user_id,
        save_reports=not args.no_save,
    )

    def on_event(event: dict) -> None:
        if args.json_events:
            print(json.dumps(event, ensure_ascii=False, default=str))

    print(f"Running preset={args.preset} ticker={request.ticker} date={request.analysis_date}")
    result = run_analysis_job(request, on_event=on_event if args.json_events else None)

    print("\n--- Done ---")
    print(f"Ticker: {result.ticker}")
    print(f"Report: {result.report_path or '(not saved)'}")
    print(
        f"Stats: llm={result.stats.llm_calls} tools={result.stats.tool_calls} "
        f"tokens_in={result.stats.tokens_in} tokens_out={result.stats.tokens_out}"
    )
    decision = result.final_state.get("final_trade_decision", "")
    if decision:
        preview = decision[:500] + ("..." if len(decision) > 500 else "")
        print(f"\nDecision preview:\n{preview}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
