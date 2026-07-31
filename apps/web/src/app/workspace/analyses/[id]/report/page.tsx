"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { BackToTop } from "@/components/BackToTop";
import { ReportSectionPager } from "@/components/ReportSectionPager";
import { ReportSummaryCards } from "@/components/ReportSummaryCards";
import {
  downloadReportExport,
  fetchJob,
  fetchPresets,
  fetchReportSection,
  fetchReportSections,
  fetchReportSignedUrls,
} from "@/lib/api";
import { formatDateOnly, formatDateTime } from "@/lib/format";
import { presetLabelZh } from "@/lib/presets";
import { buildReportSummary } from "@/lib/reportSummary";
import { extractRating, ratingBadgeClass, ratingColor, ratingLabel } from "@/lib/rating";
import type { AnalysisJob, Preset, ReportSection, SignedReportUrl } from "@/lib/types";
import type { ReportSummary } from "@/lib/reportSummary";

export default function ReportPage() {
  const params = useParams();
  const jobId = params.id as string;
  const [job, setJob] = useState<AnalysisJob | null>(null);
  const [presets, setPresets] = useState<Preset[]>([]);
  const [sections, setSections] = useState<ReportSection[]>([]);
  const [signedUrls, setSignedUrls] = useState<SignedReportUrl[]>([]);
  const [exporting, setExporting] = useState(false);
  const [summary, setSummary] = useState<ReportSummary | null>(null);
  const [decisionMd, setDecisionMd] = useState("");

  useEffect(() => {
    fetchJob(jobId).then(setJob).catch(console.error);
    fetchPresets().then(setPresets).catch(() => setPresets([]));
    fetchReportSections(jobId).then(setSections).catch(console.error);
    fetchReportSignedUrls(jobId).then(setSignedUrls).catch(() => setSignedUrls([]));

    Promise.allSettled([
      fetchReportSection(jobId, "decision").catch(() => ""),
      fetchReportSection(jobId, "trader").catch(() => ""),
      fetchReportSection(jobId, "research_manager").catch(() => ""),
    ]).then((results) => {
      const [decision, trader, manager] = results.map((r) =>
        r.status === "fulfilled" ? r.value : "",
      );
      setDecisionMd(typeof decision === "string" ? decision : "");
      setSummary(buildReportSummary(decision as string, trader as string, manager as string));
    });
  }, [jobId]);

  if (!job) {
    return <div className="text-[var(--muted)]">加载报告…</div>;
  }

  const presetFromApi = presets.find((p) => p.id === job.preset_id)?.label;
  const scheme = presetLabelZh(job.preset_id, presetFromApi);
  const rating = extractRating(job.decision_preview || decisionMd || summary?.researchRating || "");
  const ratingText = ratingLabel(rating);

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <Link
        href="/workspace/reports"
        className="text-sm text-[var(--muted)] hover:text-[var(--text)]"
      >
        ← 报告库
      </Link>

      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight">
          {job.ticker}
          <span className="text-[var(--muted)] font-normal"> · {scheme}</span>
        </h1>
        <p className="text-sm text-[var(--muted)] tabular-nums">
          分析时点 {formatDateOnly(job.analysis_date)}
          <span className="mx-1.5 text-[var(--border)]">·</span>
          完成于 {formatDateTime(job.updated_at || job.created_at)}
        </p>
      </header>

      {ratingText && (
        <div className="ax-list">
          <div className="flex items-center justify-between gap-4 px-5 py-4">
            <div>
              <div className="text-xs uppercase tracking-wider text-[var(--muted)]">最终评级</div>
              <div
                className="mt-1 text-xl font-semibold tracking-tight"
                style={{ color: ratingColor(rating) }}
              >
                {ratingText}
              </div>
            </div>
            <span
              className={`rounded-full border px-3 py-1 text-xs font-medium ${ratingBadgeClass(rating)}`}
            >
              {ratingText}
            </span>
          </div>
          <div
            className="h-0.5 w-full"
            style={{ background: ratingColor(rating), opacity: 0.55 }}
          />
        </div>
      )}

      {summary && <ReportSummaryCards summary={summary} />}

      <div className="flex flex-wrap gap-2 items-center text-sm">
        <button
          type="button"
          disabled={exporting}
          onClick={async () => {
            setExporting(true);
            try {
              await downloadReportExport(jobId);
            } catch (e) {
              console.error(e);
            } finally {
              setExporting(false);
            }
          }}
          className="rounded-full border border-[var(--border)] px-4 py-1.5 hover:border-[var(--accent)] disabled:opacity-50"
        >
          {exporting ? "打包中…" : "导出 Markdown 压缩包"}
        </button>
        {signedUrls.map((item) => (
          <a
            key={item.key}
            href={item.url}
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-full border border-[var(--border)] px-3 py-1.5 text-[var(--muted)] hover:border-[var(--accent)] hover:text-[var(--text)]"
          >
            {item.label}
          </a>
        ))}
      </div>

      {sections.length > 0 && (
        <ReportSectionPager jobId={jobId} sections={sections} initialKey="decision" />
      )}

      <p className="text-xs text-[var(--muted)] text-center">
        研究辅助，不构成投资建议。数据截至分析时点，市场有风险。
      </p>

      <BackToTop />
    </div>
  );
}
