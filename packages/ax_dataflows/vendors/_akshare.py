"""Shared AKShare import helper."""

from __future__ import annotations


def require_akshare():
    try:
        import akshare as ak  # noqa: F401
    except ImportError as exc:
        raise ImportError(
            "akshare is required for A-share data. Install with: pip install 'ax-analysis[cn]'"
        ) from exc
    import akshare as ak

    return ak
