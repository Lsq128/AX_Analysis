"""Billing feature flag (personal default: off)."""

from __future__ import annotations

import os


def is_billing_enabled() -> bool:
    """Return True when SaaS plan gates and point charging are active.

    Default is False (personal / self-hosted). Enable with AX_BILLING_ENABLED=1|true|yes.
    """
    raw = (os.environ.get("AX_BILLING_ENABLED") or "").strip().lower()
    if not raw:
        return False
    return raw in {"1", "true", "yes", "on"}
