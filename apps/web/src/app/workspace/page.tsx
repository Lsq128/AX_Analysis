"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { fetchJobs, fetchMe, fetchPresets } from "@/lib/api";
import { useBillingEnabled } from "@/hooks/useBillingEnabled";
import { formatDateTime } from "@/lib/format";
import { presetLabelZh } from "@/lib/presets";
import type { AnalysisJob, Preset, UserMe } from "@/lib/types";

export default function WorkspaceDashboard() {
  const billingEnabled = useBillingEnabled();
  const [me, setMe] = useState<UserMe | null>(null);
  const [jobs, setJobs] = useState<AnalysisJob[]>([]);
  const [presets, setPresets] = useState<Preset[]>([]);

  useEffect(() => {
    fetchMe().then(setMe).catch(console.error);
    fetchJobs(12).then(setJobs).catch(console.error);
    fetchPresets().then(setPresets).catch(console.error);
  }, []);

  const running = jobs.filter((j) => j.status === "running" || j.status === "queued");
  const recent = jobs.filter((j) => j.status === "completed").slice(0, 8);

  return (
    <div className="space-y-10">
      <section className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div>
          <h1 className="font-display text-2xl font-medium tracking-tight">
            早上好，{me?.display_name || "投资者"}
          </h1>
          <p className="text-[var(--muted)] mt-1 text-sm">
            {billingEnabled
              ? me
                ? `剩余 ${me.points_remaining.toFixed(1)} 点 · 本月套餐 ${me.plan_label}`
                : "加载账户信息…"
              : "个人模式 · 无限分析"}
          </p>
        </div>
        <Link href="/workspace/analyses/new" className="ax-btn-primary text-sm !px-5 !py-2.5">
          发起分析
        </Link>
      </section>

      {running.length > 0 && (
        <section className="space-y-3">
          <h2 className="text-xs font-medium uppercase tracking-wider text-[var(--muted)]">
            进行中
          </h2>
          <div className="ax-list">
            {running.map((job) => (
              <Link
                key={job.job_id}
                href={`/workspace/analyses/${job.job_id}`}
                className="ax-list-row"
              >
                <div className="min-w-0 flex-1">
                  <div className="font-medium">
                    {job.ticker}
                    <span className="text-[var(--muted)] font-normal">
                      {" "}
                      · {presetLabelZh(job.preset_id)}
                    </span>
                  </div>
                  <div className="text-xs text-[var(--muted)] mt-0.5">
                    {job.analysis_date} · {formatDateTime(job.updated_at || job.created_at)}
                  </div>
                </div>
                <span className={`badge badge-${job.status}`}>{statusLabel(job.status)}</span>
              </Link>
            ))}
          </div>
        </section>
      )}

      <section className="space-y-3">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-xs font-medium uppercase tracking-wider text-[var(--muted)]">
            最近结论
          </h2>
          <Link href="/workspace/reports" className="text-xs text-[var(--accent)] hover:underline">
            查看全部
          </Link>
        </div>
        {recent.length === 0 ? (
          <p className="text-sm text-[var(--muted)]">暂无已完成分析，发起第一次研判吧。</p>
        ) : (
          <div className="ax-list">
            {recent.map((job) => (
              <Link
                key={job.job_id}
                href={`/workspace/analyses/${job.job_id}/report`}
                className="ax-list-row"
              >
                <div className="min-w-0 flex-1">
                  <div className="font-medium">
                    {job.ticker}
                    <span className="text-[var(--muted)] font-normal">
                      {" "}
                      · {presetLabelZh(job.preset_id)}
                    </span>
                  </div>
                  <p className="text-sm text-[var(--muted)] mt-0.5 line-clamp-1">
                    {previewText(job.decision_preview) || "查看报告"}
                  </p>
                </div>
                <time className="shrink-0 text-xs text-[var(--muted)] tabular-nums">
                  {formatDateTime(job.updated_at || job.created_at)}
                </time>
              </Link>
            ))}
          </div>
        )}
      </section>

      <section className="space-y-3">
        <h2 className="text-xs font-medium uppercase tracking-wider text-[var(--muted)]">
          分析方案
        </h2>
        {presets.length === 0 ? (
          <p className="text-sm text-[var(--muted)]">加载方案…</p>
        ) : (
          <div className="ax-list">
            {presets.map((p) => (
              <Link
                key={p.id}
                href={`/workspace/analyses/new?preset=${p.id}`}
                className="ax-list-row"
                aria-disabled={(billingEnabled && p.locked) || undefined}
                style={billingEnabled && p.locked ? { opacity: 0.45, pointerEvents: "none" } : undefined}
              >
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{p.label}</span>
                    {billingEnabled && p.locked && (
                      <span className="text-xs text-[var(--warning)]">需升级</span>
                    )}
                  </div>
                  <p className="text-sm text-[var(--muted)] mt-0.5 line-clamp-1">
                    {p.description}
                  </p>
                </div>
                <div className="shrink-0 text-right text-xs text-[var(--muted)] tabular-nums leading-relaxed">
                  <div>约 {p.eta_minutes} 分钟</div>
                  {billingEnabled && <div>{p.quota_points} 点起</div>}
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

function statusLabel(s: string) {
  return { queued: "排队中", running: "运行中", completed: "已完成", failed: "失败" }[s] || s;
}

function previewText(text?: string | null) {
  if (!text) return "";
  return text.replace(/^#+\s*/gm, "").replace(/\*\*/g, "").split("\n").find(Boolean) || "";
}
