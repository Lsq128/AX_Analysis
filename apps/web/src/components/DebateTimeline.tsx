"use client";

import { AGENT_LABELS } from "@/lib/types";
import type { DebateTimelineEntry } from "@/lib/types";
import { MarkdownView } from "./MarkdownView";

const SIDE_META: Record<string, { icon: string; label: string; tone: string }> = {
  bull: { icon: "🐂", label: "多头", tone: "text-emerald-300" },
  bear: { icon: "🐻", label: "空头", tone: "text-rose-300" },
  aggressive: { icon: "🔥", label: "激进", tone: "text-orange-300" },
  conservative: { icon: "🛡️", label: "保守", tone: "text-sky-300" },
  neutral: { icon: "⚖️", label: "中性", tone: "text-violet-300" },
};

const ACT_LABELS: Record<string, string> = {
  research: "研究团队 · 多空辩论",
  risk: "风控团队 · 三方辩论",
  decision: "最终决策",
};

type DebateTimelineProps = {
  entries: DebateTimelineEntry[];
  compact?: boolean;
};

export function DebateTimeline({ entries, compact = false }: DebateTimelineProps) {
  const debateEntries = entries.filter((e) => e.act === "research" || e.act === "risk" || e.act === "decision");
  if (!debateEntries.length) {
    return null;
  }

  const groups: Array<{ act: string; items: DebateTimelineEntry[] }> = [];
  for (const entry of debateEntries) {
    const last = groups[groups.length - 1];
    if (last && last.act === entry.act) {
      last.items.push(entry);
    } else {
      groups.push({ act: entry.act, items: [entry] });
    }
  }

  return (
    <div className="space-y-4">
      {groups.map((group) => (
        <section key={group.act} className="rounded-lg border border-[var(--border)] bg-[var(--surface-2)] p-4">
          <h3 className="text-sm font-medium mb-3">{ACT_LABELS[group.act] || group.act}</h3>
          <div className="space-y-4">
            {group.items.map((entry) => (
              <TimelineItem key={entry.id} entry={entry} compact={compact} />
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}

function TimelineItem({ entry, compact }: { entry: DebateTimelineEntry; compact: boolean }) {
  const side = entry.side ? SIDE_META[entry.side] : null;
  const label = AGENT_LABELS[entry.agent] || entry.agent;
  const isDecision = entry.kind === "decision";

  return (
    <article className={`border-l-2 pl-4 ${isDecision ? "border-[var(--accent)]" : "border-[var(--border)]"}`}>
      <header className="flex flex-wrap items-center gap-2 mb-2 text-sm">
        {side && <span>{side.icon}</span>}
        <span className={side?.tone || "text-[var(--text)]"}>{side?.label || label}</span>
        <span className="text-[var(--muted)]">· {label}</span>
        {entry.round && entry.round > 1 && (
          <span className="text-xs text-[var(--muted)]">第 {entry.round} 轮</span>
        )}
        {isDecision && (
          <span className="text-xs rounded-full bg-[var(--accent-dim)] text-[var(--accent)] px-2 py-0.5">
            结论
          </span>
        )}
      </header>
      <div className={compact ? "max-h-40 overflow-y-auto" : ""}>
        <MarkdownView content={entry.content} />
      </div>
    </article>
  );
}
