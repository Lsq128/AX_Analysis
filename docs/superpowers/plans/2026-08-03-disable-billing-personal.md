# Disable Billing (Personal Default) Implementation Plan

> **For agentic workers:** Execute task-by-task. Checkboxes track progress. Prefer inline execution in this session (user said 开始吧).

**Goal:** Default `AX_BILLING_ENABLED=false` bypasses plan gates and point charges, hides billing UI, keeps auth; `true` restores SaaS behavior.

**Architecture:** Single helper `is_billing_enabled()` in `ax_billing`; API routes branch on it; `auth/config` exposes `billing_enabled` for the Web app.

**Tech Stack:** Python/FastAPI, Next.js, pytest.

**Spec:** `docs/superpowers/specs/2026-08-03-disable-billing-personal-design.md`

## Global Constraints

- Default billing **off** (`false` / unset).
- Do not delete `ax_billing` or drop `UserQuota`.
- Auth unchanged.
- No commit unless user asks.
- Truthy values for enable: `1`, `true`, `yes` (case-insensitive).

---

### Task 1: `is_billing_enabled` + auth config + API bypass

**Files:**
- Create: `packages/ax_billing/settings.py`
- Modify: `packages/ax_billing/__init__.py`
- Modify: `apps/api/ax_api/routes/auth.py` (add `billing_enabled`)
- Modify: `apps/api/ax_api/routes/analyses.py`, `presets.py`, `billing.py`, `admin.py`, `llm.py`
- Create: `tests/test_billing_enabled_flag.py`
- Modify: `.env.example`

### Task 2: Web hide billing chrome

**Files:**
- Modify: `apps/web/src/lib/api.ts`, `types.ts` (AuthConfig)
- Modify: `apps/web/src/app/workspace/layout.tsx`
- Modify: `apps/web/src/app/workspace/billing/page.tsx`, `admin/page.tsx` (redirect)
- Modify: `apps/web/src/app/workspace/analyses/new/page.tsx`
- Modify: `apps/web/src/app/workspace/page.tsx` (quota card if any)
- Modify: `apps/web/src/components/PresetCarousel.tsx`, `JobStatsPanel.tsx`

### Task 3: Docs

**Files:** `README.md`, `docs/features.md`, `docs/architecture.md` (brief notes)
