"use client";

import { useEffect, useMemo, useRef, type CSSProperties } from "react";
import { analystLabelsZh } from "@/lib/presets";
import type { Preset } from "@/lib/types";

type Props = {
  presets: Preset[];
  value: string;
  onChange: (id: string) => void;
  /** When false (personal mode), hide points badges and upgrade hints. */
  showBilling?: boolean;
};

/** Signed circular distance from active index into (-n/2, n/2]. */
function relativeOffset(i: number, active: number, n: number): number {
  let d = i - active;
  if (d > n / 2) d -= n;
  if (d < -n / 2) d += n;
  return d;
}

function slotStyle(offset: number): CSSProperties {
  // Only animate near cards; far cards tuck away behind center.
  if (offset === 0) {
    return {
      transform: "translateX(-50%) translateY(0) rotate(0deg) scale(1)",
      opacity: 1,
      filter: "blur(0)",
      zIndex: 5,
      pointerEvents: "auto",
    };
  }
  if (offset === -1) {
    return {
      transform: "translateX(calc(-50% - 34%)) translateY(18px) rotate(-14deg) scale(0.86)",
      opacity: 0.78,
      filter: "blur(2px)",
      zIndex: 2,
      pointerEvents: "auto",
    };
  }
  if (offset === 1) {
    return {
      transform: "translateX(calc(-50% + 34%)) translateY(18px) rotate(14deg) scale(0.86)",
      opacity: 0.78,
      filter: "blur(2px)",
      zIndex: 2,
      pointerEvents: "auto",
    };
  }
  const side = offset < 0 ? -1 : 1;
  return {
    transform: `translateX(calc(-50% + ${side * 48}%)) translateY(36px) rotate(${side * 22}deg) scale(0.72)`,
    opacity: 0,
    filter: "blur(4px)",
    zIndex: 0,
    pointerEvents: "none",
  };
}

function CardFace({
  preset,
  indexLabel,
  total,
  active,
  showBilling = true,
}: {
  preset: Preset;
  indexLabel: string;
  total: number;
  active: boolean;
  showBilling?: boolean;
}) {
  const chips = analystLabelsZh(preset.analysts)
    .split(" · ")
    .map((s) => s.trim())
    .filter(Boolean);

  return (
    <div
      className={`ax-preset-card relative flex h-full min-h-[248px] flex-col justify-between overflow-hidden rounded-[1.35rem] text-left ${
        active ? "ax-preset-card--active" : ""
      }`}
    >
      {/* Atmosphere */}
      <div className="pointer-events-none absolute inset-0" aria-hidden>
        <div className="absolute -right-8 -top-10 h-40 w-40 rounded-full bg-[var(--accent)]/[0.08] blur-2xl" />
        <div className="absolute -bottom-12 -left-6 h-36 w-36 rounded-full bg-slate-400/10 blur-2xl" />
        <span className="absolute -right-1 top-2 font-display text-[7rem] leading-none font-semibold text-[var(--text)]/[0.045] select-none tabular-nums">
          {indexLabel.padStart(2, "0")}
        </span>
      </div>

      <div className="relative z-[1] p-5 sm:p-6">
        <div className="flex items-center justify-between gap-3">
          <span className="rounded-full border border-[var(--border)] bg-white/70 px-2.5 py-0.5 text-[11px] font-medium tracking-wide text-[var(--muted)] backdrop-blur-sm tabular-nums">
            {indexLabel} / {total}
          </span>
          {active && (
            <span className="rounded-full bg-[var(--accent)] px-2.5 py-0.5 text-[11px] font-medium text-white">
              当前
            </span>
          )}
        </div>

        <h2 className="mt-4 font-display text-[1.65rem] sm:text-[1.85rem] font-semibold tracking-tight text-[var(--text)] line-clamp-2">
          {preset.label}
        </h2>
        <p className="mt-2 text-sm leading-relaxed text-[var(--muted)] line-clamp-2">
          {preset.description}
        </p>

        <div className="mt-4 flex flex-wrap gap-1.5">
          {chips.slice(0, 4).map((chip) => (
            <span
              key={chip}
              className="rounded-md bg-[var(--text)]/[0.05] px-2 py-1 text-[11px] text-[var(--text)]/75"
            >
              {chip}
            </span>
          ))}
        </div>
      </div>

      <div className="relative z-[1] mx-5 mb-5 sm:mx-6 sm:mb-6 flex items-center justify-between gap-3 rounded-2xl border border-[var(--border)]/80 bg-white/75 px-4 py-3 backdrop-blur-sm">
        {showBilling ? (
          <div>
            <div className="font-display text-2xl font-semibold tabular-nums tracking-tight text-[var(--text)]">
              {preset.quota_points}
              <span className="ml-1 font-sans text-xs font-medium text-[var(--muted)]">点起</span>
            </div>
          </div>
        ) : (
          <div className="text-sm text-[var(--muted)]">分析方案</div>
        )}
        <div className="text-right">
          <div className="text-[11px] uppercase tracking-wider text-[var(--muted)]">预计</div>
          <div className="text-sm font-medium tabular-nums text-[var(--text)]">{preset.eta_minutes} 分钟</div>
        </div>
      </div>
    </div>
  );
}

export function PresetCarousel({ presets, value, onChange, showBilling = true }: Props) {
  const unlocked = useMemo(
    () => (showBilling ? presets.filter((p) => !p.locked) : presets),
    [presets, showBilling],
  );
  const locked = useMemo(
    () => (showBilling ? presets.filter((p) => p.locked) : []),
    [presets, showBilling],
  );
  const list = unlocked.length ? unlocked : presets;
  const n = list.length;

  const index = Math.max(0, list.findIndex((p) => p.id === value));
  const current = list[index] || list[0];

  const touchX = useRef<number | null>(null);

  useEffect(() => {
    if (!current) return;
    if (current.id !== value) onChange(current.id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [current?.id]);

  if (!current || n === 0) {
    return <p className="text-sm text-[var(--muted)]">加载方案…</p>;
  }

  function selectOffset(delta: number) {
    if (n < 2) return;
    const next = list[(index + delta + n) % n];
    if (next) onChange(next.id);
  }

  return (
    <div className="space-y-5">
      <div
        className="relative outline-none"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "ArrowLeft") {
            e.preventDefault();
            selectOffset(-1);
          }
          if (e.key === "ArrowRight") {
            e.preventDefault();
            selectOffset(1);
          }
        }}
        onTouchStart={(e) => {
          touchX.current = e.changedTouches[0]?.clientX ?? null;
        }}
        onTouchEnd={(e) => {
          const start = touchX.current;
          const end = e.changedTouches[0]?.clientX;
          touchX.current = null;
          if (start == null || end == null) return;
          const dx = end - start;
          if (Math.abs(dx) < 48) return;
          selectOffset(dx > 0 ? -1 : 1);
        }}
      >
        <div className="ax-hand-stage relative mx-auto h-[300px] sm:h-[320px] max-w-3xl overflow-visible">
          {list.map((preset, i) => {
            const offset = relativeOffset(i, index, n);
            // Keep ±2 in DOM so exit/enter can animate; rest stay hidden.
            if (Math.abs(offset) > 2 && n > 5) return null;
            const active = offset === 0;
            return (
              <button
                key={preset.id}
                type="button"
                aria-label={preset.label}
                aria-current={active ? "true" : undefined}
                className="ax-hand-card absolute left-1/2 top-2 w-[min(360px,72%)] border-0 bg-transparent p-0 text-left"
                style={slotStyle(n === 1 ? 0 : offset)}
                onClick={() => {
                  if (!active) onChange(preset.id);
                }}
              >
                <CardFace
                  preset={preset}
                  indexLabel={String(i + 1)}
                  total={n}
                  active={active}
                  showBilling={showBilling}
                />
              </button>
            );
          })}
        </div>

        <div className="mt-3 flex items-center justify-center gap-4">
          <button
            type="button"
            onClick={() => selectOffset(-1)}
            disabled={n < 2}
            className="rounded-full border border-[var(--border)] bg-[var(--surface)] px-4 py-1.5 text-sm text-[var(--muted)] hover:border-[var(--accent)] hover:text-[var(--text)] disabled:opacity-40 active:scale-[0.98]"
          >
            上一个
          </button>
          <div className="flex gap-1.5">
            {list.map((p, i) => (
              <button
                key={p.id}
                type="button"
                aria-label={p.label}
                onClick={() => onChange(p.id)}
                className={`h-1.5 rounded-full transition-all duration-300 ${
                  i === index ? "w-6 bg-[var(--accent)]" : "w-1.5 bg-[var(--border)] hover:bg-[var(--muted)]"
                }`}
              />
            ))}
          </div>
          <button
            type="button"
            onClick={() => selectOffset(1)}
            disabled={n < 2}
            className="rounded-full border border-[var(--border)] bg-[var(--surface)] px-4 py-1.5 text-sm text-[var(--muted)] hover:border-[var(--accent)] hover:text-[var(--text)] disabled:opacity-40 active:scale-[0.98]"
          >
            下一个
          </button>
        </div>
      </div>

      {locked.length > 0 && (
        <p className="text-xs text-[var(--muted)]">另有 {locked.length} 个方案需升级套餐后可用</p>
      )}
    </div>
  );
}
