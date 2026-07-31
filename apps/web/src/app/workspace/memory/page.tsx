"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { MarkdownView } from "@/components/MarkdownView";
import { fetchMemoryEntries, fetchMemoryStats } from "@/lib/api";
import type { MemoryEntry, MemoryStats } from "@/lib/types";
import { RATING_COLORS } from "@/lib/types";

type Filter = "all" | "pending" | "resolved";

export default function MemoryReviewPage() {
  const [filter, setFilter] = useState<Filter>("all");
  const [entries, setEntries] = useState<MemoryEntry[]>([]);
  const [stats, setStats] = useState<MemoryStats | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    setError("");
    Promise.all([fetchMemoryEntries(filter), fetchMemoryStats()])
      .then(([list, summary]) => {
        setEntries(list);
        setStats(summary);
      })
      .catch((e) => setError((e as Error).message))
      .finally(() => setLoading(false));
  }, [filter]);

  const emptyHint = useMemo(() => {
    if (filter === "pending") return "暂无待验证决策。完成一次分析后会在此显示。";
    if (filter === "resolved") return "暂无已复盘记录。再次分析同一标的后将自动验证历史决策。";
    return "暂无复盘记录。完成分析后，系统会记住你的决策并在下次分析同标的时复盘。";
  }, [filter]);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold">复盘中心</h1>
        <p className="text-sm text-[var(--muted)] mt-1">
          追踪历史决策表现，查看 AI 团队的复盘反思
        </p>
      </div>

      {stats && (
        <section className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <StatCard label="累计决策" value={String(stats.total_entries)} />
          <StatCard label="待验证" value={String(stats.pending_count)} accent="warning" />
          <StatCard label="已复盘" value={String(stats.resolved_count)} accent="success" />
        </section>
      )}

      <section className="flex flex-wrap gap-2">
        {(
          [
            ["all", "全部"],
            ["pending", "待验证"],
            ["resolved", "已复盘"],
          ] as const
        ).map(([id, label]) => (
          <button
            key={id}
            type="button"
            onClick={() => setFilter(id)}
            className={`rounded-lg px-4 py-2 text-sm border transition-colors ${
              filter === id
                ? "border-[var(--accent)] bg-[var(--accent-dim)] text-[var(--text)]"
                : "border-[var(--border)] text-[var(--muted)] hover:border-[var(--accent)]"
            }`}
          >
            {label}
          </button>
        ))}
      </section>

      {error && (
        <div className="rounded-lg border border-[var(--danger)] bg-[var(--danger)]/10 px-4 py-3 text-sm">
          {error}
        </div>
      )}

      {loading ? (
        <p className="text-sm text-[var(--muted)]">加载复盘记录…</p>
      ) : entries.length === 0 ? (
        <div className="card p-8 text-center">
          <p className="text-sm text-[var(--muted)]">{emptyHint}</p>
          <Link
            href="/workspace/analyses/new"
            className="inline-flex mt-4 rounded-lg bg-[var(--accent)] px-5 py-2.5 text-sm font-medium text-white hover:opacity-90"
          >
            发起第一次分析
          </Link>
        </div>
      ) : (
        <section className="space-y-4">
          {entries.map((entry) => {
            const expanded = expandedId === entry.id;
            return (
              <article key={entry.id} className="card overflow-hidden">
                <button
                  type="button"
                  className="w-full text-left p-4 hover:bg-[var(--surface-2)]/40 transition-colors"
                  onClick={() => setExpandedId(expanded ? null : entry.id)}
                >
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                    <div>
                      <div className="flex items-center gap-3 flex-wrap">
                        <span className="font-medium text-lg">{entry.ticker}</span>
                        <span
                          className={`text-sm font-medium ${RATING_COLORS[entry.rating] || "text-[var(--muted)]"}`}
                        >
                          {entry.rating_label}
                        </span>
                        <StatusBadge pending={entry.pending} />
                      </div>
                      <div className="text-sm text-[var(--muted)] mt-1">
                        分析日期 {entry.date}
                        {!entry.pending && entry.raw_return && (
                          <>
                            {" · "}
                            收益 {entry.raw_return}
                            {entry.alpha_return ? ` · 超额 ${entry.alpha_return}` : ""}
                            {entry.holding_days != null ? ` · ${entry.holding_days} 天` : ""}
                          </>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-3 text-sm">
                      <Link
                        href={`/workspace/analyses/new?ticker=${encodeURIComponent(entry.ticker)}`}
                        className="text-[var(--accent)] hover:underline"
                        onClick={(e) => e.stopPropagation()}
                      >
                        再次分析
                      </Link>
                      <span className="text-[var(--muted)]">{expanded ? "收起" : "展开"}</span>
                    </div>
                  </div>
                  {!expanded && entry.decision && (
                    <p className="text-sm text-[var(--muted)] mt-3 line-clamp-2">
                      {previewText(entry.decision)}
                    </p>
                  )}
                </button>

                {expanded && (
                  <div className="border-t border-[var(--border)] p-4 space-y-6 bg-[var(--surface-2)]/20">
                    <div>
                      <h3 className="text-sm font-medium text-[var(--muted)] mb-2">当时决策</h3>
                      <MarkdownView content={entry.decision} />
                    </div>
                    {entry.reflection ? (
                      <div>
                        <h3 className="text-sm font-medium text-[var(--muted)] mb-2">复盘反思</h3>
                        <MarkdownView content={entry.reflection} />
                      </div>
                    ) : entry.pending ? (
                      <p className="text-sm text-[var(--muted)]">
                        待验证：下次分析 {entry.ticker} 时，系统将对比实际走势并生成复盘。
                      </p>
                    ) : null}
                  </div>
                )}
              </article>
            );
          })}
        </section>
      )}
    </div>
  );
}

function StatCard({
  label,
  value,
  accent,
}: {
  label: string;
  value: string;
  accent?: "success" | "warning";
}) {
  const color =
    accent === "success"
      ? "text-[var(--success)]"
      : accent === "warning"
        ? "text-[var(--warning)]"
        : "";
  return (
    <div className="card p-4">
      <div className="text-sm text-[var(--muted)]">{label}</div>
      <div className={`text-2xl font-semibold mt-1 ${color}`}>{value}</div>
    </div>
  );
}

function StatusBadge({ pending }: { pending: boolean }) {
  if (pending) {
    return (
      <span className="rounded-full border border-[var(--warning)]/40 bg-[var(--warning)]/10 px-2 py-0.5 text-xs text-[var(--warning)]">
        待验证
      </span>
    );
  }
  return (
    <span className="rounded-full border border-[var(--success)]/40 bg-[var(--success)]/10 px-2 py-0.5 text-xs text-[var(--success)]">
      已复盘
    </span>
  );
}

function previewText(markdown: string) {
  return markdown.replace(/^#+\s*/gm, "").replace(/\*\*/g, "").split("\n").find(Boolean) || "";
}
