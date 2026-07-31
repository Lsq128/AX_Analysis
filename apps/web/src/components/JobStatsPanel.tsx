"use client";

import type { AnalysisJob } from "@/lib/types";

export function JobStatsPanel({ job }: { job: AnalysisJob }) {
  const stats = job.stats;
  if (!stats || Object.keys(stats).length === 0) return null;

  const llmCalls = num(stats, "llm_calls");
  const toolCalls = num(stats, "tool_calls");
  const tokensIn = num(stats, "tokens_in");
  const tokensOut = num(stats, "tokens_out");
  const points = job.points_charged;

  return (
    <div className="card p-4 grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
      <Stat label="LLM 调用" value={String(llmCalls)} />
      <Stat label="工具调用" value={String(toolCalls)} />
      <Stat label="Token 入/出" value={`${tokensIn} / ${tokensOut}`} />
      <Stat label="消耗点数" value={points != null ? points.toFixed(1) : "—"} />
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-[var(--muted)] text-xs">{label}</div>
      <div className="font-medium mt-0.5">{value}</div>
    </div>
  );
}

function num(stats: Record<string, number>, key: string) {
  return typeof stats[key] === "number" ? stats[key] : 0;
}
