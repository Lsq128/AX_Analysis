"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { MarkdownView } from "@/components/MarkdownView";
import { fetchReportSection } from "@/lib/api";
import type { ReportSection } from "@/lib/types";

type Props = {
  jobId: string;
  sections: ReportSection[];
  initialKey?: string;
};

export function ReportSectionPager({ jobId, sections, initialKey }: Props) {
  const tabsRef = useRef<HTMLDivElement>(null);
  const touchStartX = useRef<number | null>(null);
  const sectionKeyList = useMemo(() => sections.map((s) => s.key).join(","), [sections]);

  const initialIndex = useMemo(() => {
    const preferred =
      sections.findIndex((s) => s.key === initialKey) >= 0
        ? sections.findIndex((s) => s.key === initialKey)
        : sections.findIndex((s) => s.key === "decision") >= 0
          ? sections.findIndex((s) => s.key === "decision")
          : sections.findIndex((s) => s.key === "complete") >= 0
            ? sections.findIndex((s) => s.key === "complete")
            : 0;
    return Math.max(0, preferred);
  }, [sections, initialKey]);

  const [index, setIndex] = useState(initialIndex);
  const [contents, setContents] = useState<Record<string, string>>({});
  const [ready, setReady] = useState(false);

  useEffect(() => {
    setIndex(initialIndex);
  }, [initialIndex, sectionKeyList]);

  useEffect(() => {
    if (!jobId || !sections.length) return;
    let cancelled = false;
    setReady(false);
    (async () => {
      const entries = await Promise.all(
        sections.map(async (s) => {
          try {
            const md = await fetchReportSection(jobId, s.key);
            return [s.key, md] as const;
          } catch {
            return [s.key, "该章节不可用。"] as const;
          }
        }),
      );
      if (cancelled) return;
      setContents(Object.fromEntries(entries));
      setReady(true);
    })();
    return () => {
      cancelled = true;
    };
  }, [jobId, sectionKeyList, sections]);

  const active = sections[index];

  useEffect(() => {
    const el = tabsRef.current;
    if (!el || !active) return;
    const btn = el.querySelector<HTMLElement>(`[data-key="${active.key}"]`);
    btn?.scrollIntoView({ inline: "center", block: "nearest", behavior: "auto" });
  }, [active?.key]);

  function go(delta: number) {
    setIndex((i) => Math.max(0, Math.min(sections.length - 1, i + delta)));
  }

  if (!sections.length) return null;

  return (
    <div className="space-y-4">
      <div ref={tabsRef} className="ax-pill-tabs" role="tablist" aria-label="报告章节">
        {sections.map((s, i) => (
          <button
            key={s.key}
            type="button"
            role="tab"
            data-key={s.key}
            aria-selected={i === index}
            data-active={i === index}
            className="ax-pill-tab"
            onClick={() => setIndex(i)}
          >
            {s.label}
          </button>
        ))}
      </div>

      <div
        className="card overflow-hidden"
        onTouchStart={(e) => {
          touchStartX.current = e.changedTouches[0]?.clientX ?? null;
        }}
        onTouchEnd={(e) => {
          const start = touchStartX.current;
          const end = e.changedTouches[0]?.clientX;
          touchStartX.current = null;
          if (start == null || end == null) return;
          const dx = end - start;
          if (Math.abs(dx) < 48) return;
          go(dx < 0 ? 1 : -1);
        }}
      >
        <div className="ax-section-stage p-6 max-w-none min-h-[28rem]">
          {!ready || !active ? (
            <p className="text-[var(--muted)]">加载章节…</p>
          ) : (
            <MarkdownView content={contents[active.key] || "该章节不可用。"} />
          )}
        </div>
        <div className="flex items-center justify-between gap-3 border-t border-[var(--border)] px-4 py-2.5 text-xs text-[var(--muted)]">
          <button
            type="button"
            disabled={index <= 0}
            onClick={() => go(-1)}
            className="hover:text-[var(--text)] disabled:opacity-30"
          >
            ← 上一章
          </button>
          <span className="tabular-nums">
            {index + 1} / {sections.length}
          </span>
          <button
            type="button"
            disabled={index >= sections.length - 1}
            onClick={() => go(1)}
            className="hover:text-[var(--text)] disabled:opacity-30"
          >
            下一章 →
          </button>
        </div>
      </div>
    </div>
  );
}
