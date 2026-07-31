"use client";

import type { ReportSummary } from "@/lib/reportSummary";
import { extractRating, ratingBadgeClass, ratingLabel } from "@/lib/rating";

export function ReportSummaryCards({ summary }: { summary: ReportSummary }) {
  const rating = summary.researchRating || "";
  const ratingText = ratingLabel(rating) || rating;

  const hasResearch = Boolean(ratingText || summary.researchView || summary.executiveSummary);
  const hasTrader = Boolean(
    summary.traderAction || summary.traderEntry || summary.traderStop || summary.traderPosition,
  );

  if (!hasResearch && !hasTrader) return null;

  return (
    <div className="space-y-4">
      {summary.executiveSummary && (
        <div className="card p-5">
          <div className="text-sm text-[var(--muted)] mb-2">执行摘要</div>
          <p className="text-sm leading-relaxed">{summary.executiveSummary}</p>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {hasTrader && (
          <div className="card p-5 space-y-2">
            <div className="text-sm font-medium">交易提案</div>
            <SummaryRow label="动作" value={summary.traderAction} />
            <SummaryRow label="参考入场" value={summary.traderEntry} />
            <SummaryRow label="止损" value={summary.traderStop} />
            <SummaryRow label="仓位" value={summary.traderPosition} />
          </div>
        )}
        {hasResearch && (
          <div className="card p-5 space-y-2">
            <div className="text-sm font-medium">研究经理观点</div>
            {ratingText && (
              <span
                className={`inline-block rounded-full border px-2.5 py-1 text-xs font-medium ${ratingBadgeClass(rating)}`}
              >
                {ratingText}
              </span>
            )}
            <p className="text-sm text-[var(--muted)] leading-relaxed">
              {summary.researchView || "见下方完整报告"}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

function SummaryRow({ label, value }: { label: string; value: string }) {
  if (!value) return null;
  return (
    <div className="text-sm">
      <span className="text-[var(--muted)]">{label}：</span>
      {value}
    </div>
  );
}

export function extractSummaryRating(text: string) {
  return extractRating(text);
}
