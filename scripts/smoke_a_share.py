#!/usr/bin/env python3
"""Smoke test: A-share quick analysis (600519.SS 贵州茅台)."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for sub in ("services/ai_server", "packages"):
    p = str(ROOT / sub)
    if p not in sys.path:
        sys.path.insert(0, p)

from ax_engine import AnalysisRequest, load_ax_env, run_analysis_job
from ax_dataflows import is_a_share


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="A-share smoke test")
    parser.add_argument("--ticker", default="600519.SS")
    parser.add_argument("--date", default=str(date.today()))
    parser.add_argument("--analysts", default="market", help="Comma-separated analyst keys")
    parser.add_argument("--no-save", action="store_true")
    args = parser.parse_args()

    if not is_a_share(args.ticker):
        print(f"Ticker {args.ticker} is not A-share")
        return 1

    try:
        import akshare  # noqa: F401
    except ImportError:
        print("Install akshare: pip install 'ax-analysis[cn]'")
        return 1

    load_ax_env()
    analysts = [a.strip() for a in args.analysts.split(",") if a.strip()]
    req = AnalysisRequest(
        ticker=args.ticker,
        analysis_date=args.date,
        analysts=analysts,
        research_depth=1,
        save_reports=not args.no_save,
    )
    print(f"Running A-share smoke: {req.ticker} @ {req.analysis_date}")
    result = run_analysis_job(req)
    print("Done:", result.ticker, result.stats)
    preview = (result.final_state.get("final_trade_decision") or "")[:400]
    if preview:
        print("\nDecision preview:\n", preview)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
