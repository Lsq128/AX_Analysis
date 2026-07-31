"""Report object storage tests."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for sub in ("services/ai_server", "packages", "apps/api", "apps/worker"):
    p = str(ROOT / sub)
    if p not in sys.path:
        sys.path.insert(0, p)

from ax_reports.reader import list_available_sections, list_signed_section_urls, read_section
from ax_storage import reset_report_storage_cache, upload_report_tree
from ax_storage.keys import report_key_prefix
from ax_storage.local import LocalReportStorage


class FakeSignedStorage(LocalReportStorage):
    def presigned_url(self, key_prefix: str, relative: str, *, expires: int) -> str:
        return f"https://signed.example/{key_prefix}/{relative}?exp={expires}"

    def presigned_url_expires_at(self, expires: int) -> datetime:
        return datetime(2026, 7, 29, 12, 0, tzinfo=timezone.utc)

    def supports_signed_urls(self) -> bool:
        return True


@pytest.fixture(autouse=True)
def reset_storage(monkeypatch):
    monkeypatch.delenv("AX_REPORT_STORAGE", raising=False)
    monkeypatch.delenv("AX_S3_BUCKET", raising=False)
    reset_report_storage_cache()
    yield
    reset_report_storage_cache()


def test_local_upload_and_read(tmp_path, monkeypatch):
    monkeypatch.setenv("AX_REPORT_LOCAL_ROOT", str(tmp_path / "store"))
    reset_report_storage_cache()

    src = tmp_path / "src"
    (src / "1_analysts").mkdir(parents=True)
    (src / "1_analysts" / "market.md").write_text("# Market", encoding="utf-8")
    (src / "complete_report.md").write_text("# Complete", encoding="utf-8")

    key = upload_report_tree(src, user_id="alice", job_id="job-1")
    assert key == report_key_prefix(user_id="alice", job_id="job-1")

    sections = list_available_sections(key)
    assert {s["key"] for s in sections} == {"market", "complete"}

    content = read_section(key, "market")
    assert "Market" in content["markdown"]


def test_legacy_local_path_still_works(tmp_path):
    root = tmp_path / "report"
    (root / "1_analysts").mkdir(parents=True)
    (root / "1_analysts" / "market.md").write_text("# Market", encoding="utf-8")
    sections = list_available_sections(str(root))
    assert any(s["key"] == "market" for s in sections)


def test_signed_urls_require_storage_key(tmp_path, monkeypatch):
    monkeypatch.setenv("AX_REPORT_LOCAL_ROOT", str(tmp_path / "store"))
    reset_report_storage_cache()

    with pytest.raises(Exception, match="Signed URLs require object storage"):
        list_signed_section_urls("/tmp/local/path", expires=3600)


def test_signed_urls_with_fake_storage(tmp_path, monkeypatch):
    monkeypatch.setenv("AX_REPORT_LOCAL_ROOT", str(tmp_path / "store"))
    reset_report_storage_cache()

    src = tmp_path / "src"
    (src / "5_portfolio").mkdir(parents=True)
    (src / "5_portfolio" / "decision.md").write_text("# Decision", encoding="utf-8")

    key = upload_report_tree(src, user_id="bob", job_id="job-2")

    import ax_reports.reader as reader_module

    fake = FakeSignedStorage(tmp_path / "store")
    monkeypatch.setattr(reader_module, "get_report_storage", lambda: fake)

    urls = list_signed_section_urls(key, expires=900)
    assert len(urls) == 1
    assert urls[0]["key"] == "decision"
    assert "signed.example" in urls[0]["url"]
    assert urls[0]["expires_at"]
