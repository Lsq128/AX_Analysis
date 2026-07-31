# AX UI redesign — CleanMySEO-structure, new palette

**Status:** Approved 2026-07-31 (approach A)  
**Reference structure:** [CleanMySEO](https://www.cleanmyseo.com/) centered single input — **not** its background.

## Goals

1. Marketing `/` first viewport: brand + one line + one ticker input (+ CTA).
2. Whole product shares one light token system (workspace, wizard, reports, login).
3. Avoid: purple gradients, cream+terracotta, default dark theme, Inter/Roboto, card-heavy heroes.

## Tokens

| Token | Value | Role |
|-------|--------|------|
| `--bg` | `#F4F6F8` | Page wash |
| `--bg-glow` | soft cool radial | Atmosphere only |
| `--surface` | `#FFFFFF` | Panels |
| `--text` | `#0F172A` | Ink |
| `--muted` | `#64748B` | Secondary |
| `--accent` | `#0B6E99` | CTA / brand mark |
| `--border` | `#E2E8F0` | Hairlines |

**Type:** Fraunces (display) + IBM Plex Sans (UI) + PingFang SC / system Chinese.

## Homepage

- Full-bleed light field; brand **AX** hero-level.
- Centered ticker field → `/workspace/analyses/new?ticker=` or login with `next`.
- Below fold: short capability strip + disclaimer; presets not in first viewport.

## Product chrome

- Shared light header, same accent, less card chrome.
- Flows unchanged; visual language only.

## Out of scope

- New product features, API changes, dark-mode toggle.
