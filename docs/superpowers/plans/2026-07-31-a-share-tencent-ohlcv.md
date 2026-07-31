# A-share Tencent-first OHLCV Implementation Plan

> **For agentic workers:** Implement task-by-task. Steps use checkbox syntax.

**Goal:** Make A-share OHLCV/indicators work when East Money `push2his` is unreachable, using free Tencent history first.

**Architecture:** Change only `fetch_a_share_ohlcv` in `ax_dataflows`; keep vendor name `akshare` and inject chain `akshare,yfinance`.

**Tech Stack:** AKShare `stock_zh_a_hist_tx`, existing stockstats indicators, pytest mocks.

**Spec:** `docs/superpowers/specs/2026-07-31-a-share-tencent-ohlcv-design.md`

## Global Constraints

- Free sources only (no Tushare key)
- Do not change HK/US vendor defaults
- Prefer Tencent; East Money optional with short timeout

---

### Task 1: Symbol helper + OHLCV fallback

**Files:** `packages/ax_dataflows/symbols.py`, `packages/ax_dataflows/vendors/stock.py`, `tests/test_ax_dataflows.py`, `packages/ax_dataflows/README.md`

- [x] Add `to_tx_symbol` (`sh600519` / `sz000001`)
- [x] `fetch_a_share_ohlcv`: Tencent → East Money → raise
- [x] Normalize both TX and EM column shapes to Date/OHLCV
- [x] Update unit test to prefer `stock_zh_a_hist_tx` mock; add EM-fallback and TX-success cases
- [x] Run `pytest tests/test_ax_dataflows.py -q`
- [x] Smoke: `.venv/bin/python scripts/smoke_a_share.py --ticker 600519.SS --no-save` (optional live)
