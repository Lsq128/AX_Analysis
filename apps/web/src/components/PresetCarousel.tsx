"use client";

import { useEffect, useMemo, useState } from "react";
import { analystLabelsZh } from "@/lib/presets";
import type { Preset } from "@/lib/types";

type Props = {
  presets: Preset[];
  value: string;
  onChange: (id: string) => void;
};

export function PresetCarousel({ presets, value, onChange }: Props) {
  const unlocked = useMemo(() => presets.filter((p) => !p.locked), [presets]);
  const locked = useMemo(() => presets.filter((p) => p.locked), [presets]);
  const list = unlocked.length ? unlocked : presets;

  const index = Math.max(
    0,
    list.findIndex((p) => p.id === value),
  );
  const current = list[index] || list[0];

  useEffect(() => {
    if (!current) return;
    if (current.id !== value) onChange(current.id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [current?.id]);

  if (!current) {
    return <p className="text-sm text-[var(--muted)]">加载方案…</p>;
  }

  function prev() {
    const next = list[(index - 1 + list.length) % list.length];
    if (next) onChange(next.id);
  }

  function next() {
    const n = list[(index + 1) % list.length];
    if (n) onChange(n.id);
  }

  return (
    <div className="space-y-4">
      <div
        className="relative"
        onKeyDown={(e) => {
          if (e.key === "ArrowLeft") {
            e.preventDefault();
            prev();
          }
          if (e.key === "ArrowRight") {
            e.preventDefault();
            next();
          }
        }}
        tabIndex={0}
      >
        <div className="card min-h-[220px] sm:min-h-[240px] p-6 sm:p-8 flex flex-col justify-between overflow-hidden outline-none">
          <div className="absolute inset-y-0 left-0 w-1 bg-[var(--accent)]" />
          <div className="pl-2">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-xs text-[var(--muted)] tabular-nums">
                  {index + 1} / {list.length}
                </p>
                <h2 className="mt-2 text-2xl sm:text-3xl font-semibold tracking-tight">
                  {current.label}
                </h2>
              </div>
              <div className="text-right shrink-0">
                <div className="text-2xl font-semibold tabular-nums tracking-tight">
                  {current.quota_points}
                  <span className="text-sm font-normal text-[var(--muted)] ml-1">点起</span>
                </div>
                <div className="text-sm text-[var(--muted)] mt-1 tabular-nums">
                  约 {current.eta_minutes} 分钟
                </div>
              </div>
            </div>
            <p className="mt-4 text-[var(--muted)] leading-relaxed max-w-xl">
              {current.description}
            </p>
            <p className="mt-3 text-sm text-[var(--text)]/80">
              覆盖：{analystLabelsZh(current.analysts)}
            </p>
          </div>

          <div className="mt-8 flex items-center justify-between gap-3 pl-2">
            <div className="flex gap-1.5">
              {list.map((p, i) => (
                <button
                  key={p.id}
                  type="button"
                  aria-label={p.label}
                  onClick={() => onChange(p.id)}
                  className={`h-1.5 rounded-full transition-colors ${
                    i === index ? "w-6 bg-[var(--accent)]" : "w-1.5 bg-[var(--border)] hover:bg-[var(--muted)]"
                  }`}
                />
              ))}
            </div>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={prev}
                className="rounded-lg border border-[var(--border)] px-3 py-1.5 text-sm text-[var(--muted)] hover:border-[var(--accent)] hover:text-[var(--text)] active:scale-[0.98]"
              >
                上一个
              </button>
              <button
                type="button"
                onClick={next}
                className="rounded-lg border border-[var(--border)] bg-[var(--surface-2)] px-3 py-1.5 text-sm hover:border-[var(--accent)] active:scale-[0.98]"
              >
                下一个
              </button>
            </div>
          </div>
        </div>
      </div>

      {locked.length > 0 && (
        <p className="text-xs text-[var(--muted)]">
          另有 {locked.length} 个方案需升级套餐后可用
        </p>
      )}
    </div>
  );
}
