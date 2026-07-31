# A-share OHLCV: Tencent-first (free, no key)

**Status:** Approved 2026-07-31  
**Constraint:** Free sources only; no Tushare / paid keys.

## Problem

AKShare A-share daily history uses East Money `push2his.eastmoney.com`. On some networks the host returns empty replies / disconnects, so A-share analysis fails before fundamentals/news.

## Decision

Inside `packages/ax_dataflows` `fetch_a_share_ohlcv`:

1. **Primary:** Tencent via AKShare `stock_zh_a_hist_tx` (`proxy.finance.qq.com`)
2. **Secondary (optional):** East Money `stock_zh_a_hist` with short timeout; log and continue on failure
3. **Engine fallback:** existing vendor chain `akshare,yfinance` unchanged

Indicators keep using `fetch_a_share_ohlcv` + stockstats. Fundamentals/news stay on current EM/CCTV paths; failures still fall through to yfinance.

## Non-goals

- No `stock-open-api`
- No new vendor name in `data_vendors` (still registered as `akshare`)
- No HK/US path changes

## Acceptance

`scripts/smoke_a_share.py --ticker 600519.SS --no-save` succeeds on OHLCV/indicators when East Money is unreachable.
