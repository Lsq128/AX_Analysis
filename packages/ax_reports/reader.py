"""Safe read access to analysis report trees (local path or object storage key)."""

from __future__ import annotations

from pathlib import Path

from ax_storage import get_report_storage, is_storage_key

REPORT_TABS: dict[str, tuple[str, str]] = {
    "complete": ("完整报告", "complete_report.md"),
    "market": ("技术面", "1_analysts/market.md"),
    "sentiment": ("舆情", "1_analysts/sentiment.md"),
    "news": ("资讯", "1_analysts/news.md"),
    "fundamentals": ("基本面", "1_analysts/fundamentals.md"),
    "bull": ("多头", "2_research/bull.md"),
    "bear": ("空头", "2_research/bear.md"),
    "research_manager": ("研究经理", "2_research/manager.md"),
    "trader": ("交易全文", "3_trading/trader.md"),
    "risk_aggressive": ("激进风控", "4_risk/aggressive.md"),
    "risk_conservative": ("保守风控", "4_risk/conservative.md"),
    "risk_neutral": ("中性风控", "4_risk/neutral.md"),
    "decision": ("决策摘要", "5_portfolio/decision.md"),
}


class ReportAccessError(Exception):
    pass


def _resolve_report_root(report_path: str) -> Path:
    root = Path(report_path).expanduser().resolve()
    if not root.exists():
        raise ReportAccessError("Report directory not found")
    if not root.is_dir():
        root = root.parent
    return root


def _safe_join(root: Path, relative: str) -> Path:
    target = (root / relative).resolve()
    if root not in target.parents and target != root:
        raise ReportAccessError("Invalid report path")
    return target


def list_available_sections(report_path: str) -> list[dict[str, str]]:
    if is_storage_key(report_path):
        storage = get_report_storage()
        sections: list[dict[str, str]] = []
        for key, (label, rel) in REPORT_TABS.items():
            if storage.exists(report_path, rel):
                sections.append({"key": key, "label": label, "path": rel})
        return sections

    root = _resolve_report_root(report_path)
    sections = []
    for key, (label, rel) in REPORT_TABS.items():
        path = _safe_join(root, rel)
        if path.is_file():
            sections.append({"key": key, "label": label, "path": rel})
    return sections


def read_section(report_path: str, section_key: str) -> dict[str, str]:
    if section_key not in REPORT_TABS:
        raise ReportAccessError(f"Unknown section: {section_key}")
    label, rel = REPORT_TABS[section_key]

    if is_storage_key(report_path):
        storage = get_report_storage()
        try:
            markdown = storage.read_text(report_path, rel)
        except FileNotFoundError as exc:
            raise ReportAccessError("Section not available for this run") from exc
        return {"key": section_key, "label": label, "markdown": markdown}

    root = _resolve_report_root(report_path)
    path = _safe_join(root, rel)
    if not path.is_file():
        raise ReportAccessError("Section not available for this run")
    return {
        "key": section_key,
        "label": label,
        "markdown": path.read_text(encoding="utf-8"),
    }


def list_signed_section_urls(report_path: str, *, expires: int) -> list[dict[str, str]]:
    """Return presigned download URLs for available sections."""
    if not is_storage_key(report_path):
        raise ReportAccessError("Signed URLs require object storage reports")

    storage = get_report_storage()
    if not storage.supports_signed_urls():
        raise ReportAccessError("Signed URLs are not supported for this storage backend")

    expires_at = storage.presigned_url_expires_at(expires)
    expires_iso = expires_at.isoformat() if expires_at else ""

    out: list[dict[str, str]] = []
    for key, (label, rel) in REPORT_TABS.items():
        if not storage.exists(report_path, rel):
            continue
        url = storage.presigned_url(report_path, rel, expires=expires)
        out.append(
            {
                "key": key,
                "label": label,
                "path": rel,
                "url": url,
                "expires_at": expires_iso,
            }
        )
    return out
