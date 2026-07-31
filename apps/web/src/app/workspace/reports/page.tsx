"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { fetchPresets, fetchReports } from "@/lib/api";
import { formatDateTime } from "@/lib/format";
import { presetLabelZh } from "@/lib/presets";
import { extractRating, ratingBadgeClass, ratingLabel } from "@/lib/rating";
import type { AnalysisJob, Preset } from "@/lib/types";

export default function ReportsLibraryPage() {
  const [reports, setReports] = useState<AnalysisJob[]>([]);
  const [presets, setPresets] = useState<Preset[]>([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([fetchReports(100), fetchPresets()])
      .then(([jobs, presetList]) => {
        setReports(jobs);
        setPresets(presetList);
      })
      .catch((e) => setError((e as Error).message))
      .finally(() => setLoading(false));
  }, []);

  const presetLabels = useMemo(() => {
    const map: Record<string, string> = {};
    for (const p of presets) map[p.id] = p.label;
    return map;
  }, [presets]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return reports;
    return reports.filter((r) => {
      const scheme = presetLabelZh(r.preset_id, presetLabels[r.preset_id || ""]).toLowerCase();
      return (
        r.ticker.toLowerCase().includes(q) ||
        (r.preset_id || "").toLowerCase().includes(q) ||
        scheme.includes(q) ||
        (r.decision_preview || "").toLowerCase().includes(q)
      );
    });
  }, [reports, query, presetLabels]);

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">报告库</h1>
          <p className="text-sm text-[var(--muted)] mt-1">历史分析结论与完整决策报告</p>
        </div>
        <Link
          href="/workspace/analyses/new"
          className="inline-flex items-center justify-center rounded-lg bg-[var(--accent)] px-5 py-2.5 text-sm font-medium text-white hover:opacity-90"
        >
          发起新分析
        </Link>
      </div>

      <input
        type="search"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="搜索标的、方案或结论…"
        className="w-full sm:max-w-md rounded-lg border border-[var(--border)] bg-[var(--surface)] px-4 py-2.5 text-sm placeholder:text-[var(--muted)] focus:outline-none focus:border-[var(--accent)]"
      />

      {error && (
        <div className="rounded-lg border border-[var(--danger)] bg-[var(--danger)]/10 px-4 py-3 text-sm">
          {error}
        </div>
      )}

      {loading ? (
        <p className="text-sm text-[var(--muted)]">加载报告…</p>
      ) : filtered.length === 0 ? (
        <div className="ax-list">
          <div className="px-5 py-10 text-center text-sm text-[var(--muted)]">
            {reports.length === 0
              ? "暂无已完成报告。完成一次分析后，决策摘要将出现在这里。"
              : "没有匹配的报告，试试其他关键词。"}
            {reports.length === 0 && (
              <div className="mt-4">
                <Link
                  href="/workspace/analyses/new"
                  className="inline-flex rounded-lg bg-[var(--accent)] px-5 py-2.5 text-sm font-medium text-white hover:opacity-90"
                >
                  发起第一次分析
                </Link>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="ax-list">
          {filtered.map((job) => (
            <ReportRow
              key={job.job_id}
              job={job}
              presetLabel={presetLabels[job.preset_id || ""]}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function ReportRow({ job, presetLabel }: { job: AnalysisJob; presetLabel?: string }) {
  const rating = extractRating(job.decision_preview || "");
  const label = ratingLabel(rating);
  const scheme = presetLabelZh(job.preset_id, presetLabel);

  return (
    <div className="ax-list-row !items-stretch sm:!items-center flex-col sm:flex-row gap-3 sm:gap-4">
      <Link
        href={`/workspace/analyses/${job.job_id}/report`}
        className="min-w-0 flex-1 space-y-1"
      >
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-base font-semibold tracking-tight">{job.ticker}</span>
          {label && (
            <span
              className={`rounded-full border px-2 py-0.5 text-[11px] font-medium ${ratingBadgeClass(rating)}`}
            >
              {label}
            </span>
          )}
        </div>
        <p className="text-sm text-[var(--muted)]">
          {scheme}
          <span className="mx-1.5 text-[var(--border)]">·</span>
          <time className="tabular-nums">
            {formatDateTime(job.updated_at || job.created_at)}
          </time>
        </p>
        <p className="text-sm text-[var(--muted)] line-clamp-2">
          {previewText(job.decision_preview) || "查看完整决策报告"}
        </p>
      </Link>
      <div className="flex shrink-0 flex-wrap gap-3 text-xs sm:flex-col sm:items-end sm:gap-2">
        <Link
          href={`/workspace/analyses/${job.job_id}/report`}
          className="text-[var(--accent)] hover:underline font-medium"
        >
          查看报告
        </Link>
        <Link
          href={`/workspace/analyses/${job.job_id}`}
          className="text-[var(--muted)] hover:text-[var(--text)] hover:underline"
        >
          分析室
        </Link>
        <Link
          href={`/workspace/analyses/new?ticker=${encodeURIComponent(job.ticker)}`}
          className="text-[var(--muted)] hover:text-[var(--text)] hover:underline"
        >
          再次分析
        </Link>
      </div>
    </div>
  );
}

function previewText(text?: string | null) {
  if (!text) return "";
  return text.replace(/^#+\s*/gm, "").replace(/\*\*/g, "").split("\n").find(Boolean) || "";
}
