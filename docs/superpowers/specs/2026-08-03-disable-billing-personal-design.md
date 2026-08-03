# Disable billing for personal use (flag-gated)

**Status:** Approved 2026-08-03  
**Scope:** Keep auth/users; turn off plans/points by default; hide billing UI. Reversible via env flag.

## Problem

AX_Analysis was designed as a SaaS product with plans (free/standard/pro), point quotas, plan gates (e.g. free blocks deep), billing page, and admin quota tools. For personal/self-hosted use, purchasing plans and consuming points are unwanted, but login and per-user data isolation should remain.

## Goals

1. Default mode: no plan gates, no point charges, no billing/admin UI.
2. Auth (JWT / OAuth / dev login) and user-scoped jobs/reports unchanged.
3. Reversible: set `AX_BILLING_ENABLED=true` to restore SaaS billing behavior.
4. Do not delete `ax_billing` package or drop `UserQuota` schema.

## Non-goals

- Removing authentication
- Payment integration
- Hard-deleting billing modules/tables
- Multi-user seat licensing changes

## Decision

Add **`AX_BILLING_ENABLED`** (default **`false`**). When false, bypass metering/gates and hide commercial UI. When true, existing behavior remains.

### Backend (`AX_BILLING_ENABLED=false`)

| Surface | Behavior |
|---------|----------|
| `POST /api/v1/analyses` | Skip `is_preset_allowed`; skip `charge_points`; persist `points_charged=0` (or null) |
| `GET /api/v1/presets` | All presets `locked=false` (including deep) |
| `GET /api/v1/me` | May still return plan/points fields for compatibility; UI ignores them |
| `GET /api/v1/billing/*` | 404 or 410 |
| Admin quota endpoints under `/api/v1/admin/*` | 404 or 410 when billing off (or whole admin quota surface disabled) |
| `GET /api/v1/llm/quota-estimate` | 404 (preferred) or keep estimate-only without affecting create |
| `User` / `UserQuota` bootstrap | May still create quota rows on `get_or_create`; unused when billing off |

Expose `billing_enabled: bool` on **`GET /api/v1/auth/config`** (existing endpoint) so the Web app can decide UI without a build-time `NEXT_PUBLIC_*` flag.

Helper (conceptual): `ax_billing.is_billing_enabled() -> bool` reading `AX_BILLING_ENABLED` (truthy: `1`/`true`/`yes`; default false).

### Frontend (when `billing_enabled` is false)

| Surface | Behavior |
|---------|----------|
| Nav «套餐» / «管理» | Not rendered |
| Header points / plan label | Hidden (keep logout / login) |
| `/workspace/billing`, `/workspace/admin` | Redirect to `/workspace` |
| New-analysis wizard | No locked preset block, no insufficient-points guard, no «本次消耗 N 点» / «查看套餐» |
| `PresetCarousel` | Hide upgrade / locked messaging and point badges |
| `JobStatsPanel` «消耗点数» | Hidden |
| Workspace home quota card | Hidden |

Keep page files under `apps/web/.../billing` and `admin` for easy re-enable; they are unreachable via nav and redirect when billing is off.

### Config / docs

- `.env.example`: `AX_BILLING_ENABLED=false` with short comment
- Docker demo / personal deploy docs: default off
- `docs/features.md`, `docs/architecture.md`, README: note personal default; how to set `true` for SaaS mode
- Do not erase plan catalog docs; mark as «optional / flag-gated»

### Tests

- Billing off: create with `deep` succeeds; no charge path; presets unlocked
- Billing on: existing quota / gate tests still pass
- Auth config returns `billing_enabled`
- Optional: web/layout or wizard does not show billing chrome when flag false (if covered by existing frontend test patterns)

## Acceptance

1. Fresh `.env` from example has billing off; user can run deep analysis without points/plan errors.
2. Web shows no 套餐/管理/点数 chrome in default mode.
3. `AX_BILLING_ENABLED=true` restores charge + gate + billing UI paths.
4. Login and per-user job ownership still work.

## Out of scope follow-ups

- Schema migration to drop `UserQuota` / `points_charged`
- Deleting `packages/ax_billing`
- Single-user / no-login mode (product choice A from brainstorming)
