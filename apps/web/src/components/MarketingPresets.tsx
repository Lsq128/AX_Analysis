"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { fetchPresets } from "@/lib/api";
import type { Preset } from "@/lib/types";

/** Fallback when API is unavailable (matches ax_presets). */
const FALLBACK: Preset[] = [
  { id: "quick", label: "快速诊股", analysts: ["market"], research_depth: 1, quota_points: 1, eta_minutes: 5, description: "技术面快速扫描" },
  { id: "technical", label: "技术趋势", analysts: ["market"], research_depth: 1, quota_points: 1, eta_minutes: 5, description: "趋势与关键价位" },
  { id: "news_sentiment", label: "资讯舆情", analysts: ["news", "social"], research_depth: 1, quota_points: 1.5, eta_minutes: 8, description: "新闻与市场情绪" },
  { id: "value", label: "价值深挖", analysts: ["market", "fundamentals"], research_depth: 3, quota_points: 2, eta_minutes: 12, description: "基本面 + 技术面" },
  { id: "full", label: "全面研判", analysts: ["market", "social", "news", "fundamentals"], research_depth: 3, quota_points: 2.5, eta_minutes: 15, description: "四维分析师 + 多空辩论 + 风控" },
  { id: "deep", label: "深度推演", analysts: ["market", "social", "news", "fundamentals"], research_depth: 5, quota_points: 4, eta_minutes: 25, description: "最高深度，适合重大决策" },
  { id: "crypto", label: "数字资产快览", analysts: ["market", "news", "social"], research_depth: 1, quota_points: 1, eta_minutes: 8, description: "加密资产专项" },
];

export function MarketingPresets() {
  const [presets, setPresets] = useState<Preset[]>(FALLBACK);

  useEffect(() => {
    fetchPresets()
      .then((list) => {
        if (list.length) setPresets(list);
      })
      .catch(() => undefined);
  }, []);

  return (
    <section id="pricing" className="py-16 mx-auto max-w-6xl px-4">
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3 mb-8">
        <div>
          <h2 className="font-display text-2xl font-medium tracking-tight">分析方案</h2>
          <p className="text-[var(--muted)] mt-2 text-sm">
            按点数消耗。首页输入代码后，可在向导中选择深度。
          </p>
        </div>
        <Link
          href="/workspace/analyses/new"
          className="text-sm text-[var(--accent)] hover:underline shrink-0"
        >
          全部方案 →
        </Link>
      </div>

      <div className="ax-list">
        {presets.map((p) => (
          <Link
            key={p.id}
            href={`/workspace/analyses/new?preset=${p.id}`}
            className="ax-list-row group"
          >
            <div className="min-w-0 flex-1">
              <div className="font-medium group-hover:text-[var(--accent)] transition-colors">
                {p.label}
              </div>
              <p className="text-sm text-[var(--muted)] mt-0.5 line-clamp-1">{p.description}</p>
            </div>
            <div className="shrink-0 text-right text-xs text-[var(--muted)] tabular-nums leading-relaxed">
              <div className="text-sm text-[var(--text)] font-medium">{p.quota_points} 点起</div>
              <div>约 {p.eta_minutes} 分钟</div>
            </div>
          </Link>
        ))}
      </div>
    </section>
  );
}
