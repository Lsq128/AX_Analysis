"""Report markdown routes."""

from __future__ import annotations

import io
import zipfile
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ax_api.deps import assert_job_owner, get_current_user_id, get_store
from ax_reports.reader import REPORT_TABS, ReportAccessError, list_available_sections, list_signed_section_urls, read_section
from ax_storage.settings import get_storage_settings

router = APIRouter(prefix="/analyses", tags=["reports"])


class ReportSectionMeta(BaseModel):
    key: str
    label: str
    path: str


class ReportSectionContent(BaseModel):
    key: str
    label: str
    markdown: str


class SignedReportUrl(BaseModel):
    key: str
    label: str
    path: str
    url: str
    expires_at: str


@router.get("/{job_id}/report", response_model=list[ReportSectionMeta])
def list_report_sections(
    job_id: str,
    user_id: Annotated[str, Depends(get_current_user_id)],
    store=Depends(get_store),
) -> list[ReportSectionMeta]:
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Analysis job not found")
    assert_job_owner(job.user_id, user_id)
    if job.status != "completed" or not job.report_path:
        raise HTTPException(status_code=409, detail="Report not ready")
    try:
        sections = list_available_sections(job.report_path)
    except ReportAccessError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return [ReportSectionMeta(**s) for s in sections]


@router.get("/{job_id}/report/signed-urls", response_model=list[SignedReportUrl])
def get_report_signed_urls(
    job_id: str,
    user_id: Annotated[str, Depends(get_current_user_id)],
    store=Depends(get_store),
    expires: Annotated[int, Query(ge=60, le=86400)] | None = None,
) -> list[SignedReportUrl]:
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Analysis job not found")
    assert_job_owner(job.user_id, user_id)
    if job.status != "completed" or not job.report_path:
        raise HTTPException(status_code=409, detail="Report not ready")

    ttl = expires or get_storage_settings()["signed_url_ttl"]
    try:
        urls = list_signed_section_urls(job.report_path, expires=ttl)
    except ReportAccessError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc
    return [SignedReportUrl(**item) for item in urls]


@router.get("/{job_id}/report/export")
def export_report_zip(
    job_id: str,
    user_id: Annotated[str, Depends(get_current_user_id)],
    store=Depends(get_store),
) -> StreamingResponse:
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Analysis job not found")
    assert_job_owner(job.user_id, user_id)
    if job.status != "completed" or not job.report_path:
        raise HTTPException(status_code=409, detail="Report not ready")

    try:
        sections = list_available_sections(job.report_path)
    except ReportAccessError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        for section in sections:
            try:
                data = read_section(job.report_path, section["key"])
            except ReportAccessError:
                continue
            filename = REPORT_TABS.get(section["key"], (section["key"], section["path"]))[1]
            archive.writestr(filename.replace("/", "_"), data["markdown"])
    buf.seek(0)
    safe_ticker = job.ticker.replace("/", "_")
    filename = f"ax-report-{safe_ticker}-{job.analysis_date}.zip"
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{job_id}/report/{section_key}", response_model=ReportSectionContent)
def get_report_section(
    job_id: str,
    section_key: str,
    user_id: Annotated[str, Depends(get_current_user_id)],
    store=Depends(get_store),
) -> ReportSectionContent:
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Analysis job not found")
    assert_job_owner(job.user_id, user_id)
    if not job.report_path:
        raise HTTPException(status_code=409, detail="Report not ready")
    try:
        data = read_section(job.report_path, section_key)
    except ReportAccessError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ReportSectionContent(**data)
