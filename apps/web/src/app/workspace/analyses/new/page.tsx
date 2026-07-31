"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useMemo, useState } from "react";
import {
  createAnalysis,
  estimateQuota,
  fetchLlmProviders,
  fetchMe,
  fetchPresets,
  fetchRecentTickers,
  searchTickers,
} from "@/lib/api";
import { PresetCarousel } from "@/components/PresetCarousel";
import type { LlmProvider, Preset, QuotaEstimate, RecentTicker, TickerSearchResult, UserMe } from "@/lib/types";

function WizardContent() {
  const router = useRouter();
  const params = useSearchParams();
  const [step, setStep] = useState(1);
  const [presets, setPresets] = useState<Preset[]>([]);
  const [providers, setProviders] = useState<LlmProvider[]>([]);
  const [me, setMe] = useState<UserMe | null>(null);
  const [presetId, setPresetId] = useState(params.get("preset") || "full");
  const [ticker, setTicker] = useState("");
  const [useToday, setUseToday] = useState(true);
  const [analysisDate, setAnalysisDate] = useState(todayStr());
  const [providerId, setProviderId] = useState("deepseek");
  const [shallowModel, setShallowModel] = useState("");
  const [deepModel, setDeepModel] = useState("");
  const [estimate, setEstimate] = useState<QuotaEstimate | null>(null);
  const [agreed, setAgreed] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [recentTickers, setRecentTickers] = useState<RecentTicker[]>([]);
  const [searchResults, setSearchResults] = useState<TickerSearchResult[]>([]);

  const selected = useMemo(
    () => presets.find((p) => p.id === presetId) || presets[0],
    [presets, presetId],
  );

  const selectedProvider = useMemo(
    () => providers.find((p) => p.id === providerId) || providers[0],
    [providers, providerId],
  );

  useEffect(() => {
    fetchPresets().then(setPresets).catch(console.error);
    fetchLlmProviders()
      .then((list) => {
        setProviders(list);
        const first = list[0];
        if (first) {
          setProviderId(first.id);
          setShallowModel(first.defaults.quick);
          setDeepModel(first.defaults.deep);
        }
      })
      .catch(console.error);
    fetchMe().then(setMe).catch(console.error);
    fetchRecentTickers(8).then(setRecentTickers).catch(() => setRecentTickers([]));
  }, []);

  useEffect(() => {
    const p = params.get("preset");
    if (p) setPresetId(p);
    const t = params.get("ticker");
    if (t) setTicker(t);
  }, [params]);

  useEffect(() => {
    if (!presetId || !providerId) return;
    estimateQuota(presetId, providerId)
      .then(setEstimate)
      .catch(() => setEstimate(null));
  }, [presetId, providerId]);

  useEffect(() => {
    if (!selectedProvider) return;
    setShallowModel(selectedProvider.defaults.quick);
    setDeepModel(selectedProvider.defaults.deep);
  }, [selectedProvider?.id]);

  useEffect(() => {
    if (!ticker.trim() || ticker.trim().length < 2) {
      setSearchResults([]);
      return;
    }
    const handle = setTimeout(() => {
      searchTickers(ticker.trim(), 6).then(setSearchResults).catch(() => setSearchResults([]));
    }, 250);
    return () => clearTimeout(handle);
  }, [ticker]);

  async function submit() {
    if (!selected || !ticker.trim() || selected.locked) return;
    setSubmitting(true);
    setError("");
    try {
      const job = await createAnalysis({
        ticker: ticker.trim(),
        analysis_date: useToday ? todayStr() : analysisDate,
        preset: selected.id,
        llm_provider: providerId,
        shallow_thinker: shallowModel || undefined,
        deep_thinker: deepModel || undefined,
      });
      router.push(`/workspace/analyses/${job.job_id}`);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSubmitting(false);
    }
  }

  const points = estimate?.total_points ?? selected?.quota_points ?? 0;
  const remaining = me?.points_remaining ?? 0;

  return (
    <div className="max-w-3xl mx-auto">
      <div className="mb-8 flex items-baseline justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">发起分析</h1>
          <p className="text-sm text-[var(--muted)] mt-1">选择方案、标的与模型，提交后进入分析室</p>
        </div>
        <span className="text-xs text-[var(--muted)] tabular-nums">步骤 {step} / 4</span>
      </div>

      {step === 1 && (
        <section className="space-y-4">
          <p className="text-sm text-[var(--muted)]">左右手牌切换方案，点中间两侧或按钮后进入下一步</p>
          <PresetCarousel presets={presets} value={presetId} onChange={setPresetId} />
          {selected?.locked && (
            <p className="text-sm text-[var(--warning)]">
              「{selected.label}」需要更高套餐。
              <Link href="/workspace/billing" className="text-[var(--accent)] hover:underline ml-1">
                查看套餐
              </Link>
            </p>
          )}
        </section>
      )}

      {step === 2 && (
        <section className="space-y-4">
          <label className="block text-sm text-[var(--muted)]">股票代码 / 名称</label>
          <input
            value={ticker}
            onChange={(e) => setTicker(e.target.value)}
            placeholder="600519 / 0700.HK / NVDA"
            className="w-full rounded-full border border-[var(--border)] bg-[var(--surface)] px-4 py-3 outline-none focus:border-[var(--accent)] shadow-sm"
          />
          {searchResults.length > 0 && (
            <div className="card divide-y divide-[var(--border)] overflow-hidden">
              {searchResults.map((item) => (
                <button
                  key={`${item.source}-${item.ticker}`}
                  type="button"
                  onClick={() => {
                    setTicker(item.ticker);
                    setSearchResults([]);
                  }}
                  className="w-full text-left px-4 py-3 hover:bg-[var(--surface-2)] text-sm"
                >
                  <span className="font-medium">{item.ticker}</span>
                  {item.name && (
                    <span className="text-[var(--muted)] ml-2">
                      {item.name}
                      {item.market ? ` · ${item.market}` : ""}
                    </span>
                  )}
                </button>
              ))}
            </div>
          )}
          {recentTickers.length > 0 && (
            <div>
              <div className="text-xs text-[var(--muted)] mb-2">最近分析</div>
              <div className="flex flex-wrap gap-2">
                {recentTickers.map((item) => (
                  <button
                    key={item.ticker}
                    type="button"
                    onClick={() => setTicker(item.ticker)}
                    className={`rounded-lg border px-3 py-1.5 text-sm transition-colors ${
                      ticker === item.ticker
                        ? "border-[var(--accent)] bg-[var(--accent-dim)]"
                        : "border-[var(--border)] hover:border-[var(--accent)]"
                    }`}
                  >
                    {item.ticker}
                  </button>
                ))}
              </div>
            </div>
          )}
          <p className="text-xs text-[var(--muted)]">支持 A 股、港股、美股 Yahoo 代码</p>
        </section>
      )}

      {step === 3 && (
        <section className="space-y-4">
          <label className="flex items-center gap-3 card p-4 cursor-pointer">
            <input type="radio" checked={useToday} onChange={() => setUseToday(true)} />
            <div>
              <div className="font-medium">当前时点（推荐）</div>
              <div className="text-sm text-[var(--muted)]">以今日可见信息分析</div>
            </div>
          </label>
          <label className="flex items-center gap-3 card p-4 cursor-pointer">
            <input type="radio" checked={!useToday} onChange={() => setUseToday(false)} />
            <div className="flex-1">
              <div className="font-medium">指定历史日期</div>
              <input
                type="date"
                value={analysisDate}
                onChange={(e) => setAnalysisDate(e.target.value)}
                disabled={useToday}
                className="mt-2 rounded border border-[var(--border)] bg-[var(--surface-2)] px-3 py-2 text-sm"
              />
            </div>
          </label>
        </section>
      )}

      {step === 4 && selected && (
        <section className="space-y-4">
          <div>
            <p className="text-sm text-[var(--muted)] mb-3">选择推理引擎（影响点数系数）</p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {providers.map((p) => (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => setProviderId(p.id)}
                  className={`card p-4 text-left transition-colors ${
                    providerId === p.id ? "border-[var(--accent)] ring-1 ring-[var(--accent)]" : ""
                  }`}
                >
                  <div className="font-medium">{p.label}</div>
                  <div className="text-xs text-[var(--muted)] mt-1">{p.description}</div>
                  <div className="text-sm mt-2 text-[var(--accent)]">×{p.quota_factor} 系数</div>
                </button>
              ))}
            </div>
          </div>

          {selectedProvider && (
            <div className="card p-4 grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
              <label className="block">
                <span className="text-[var(--muted)]">快速模型</span>
                <select
                  value={shallowModel}
                  onChange={(e) => setShallowModel(e.target.value)}
                  className="mt-1 w-full rounded border border-[var(--border)] bg-[var(--surface-2)] px-3 py-2"
                >
                  {selectedProvider.models.quick.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block">
                <span className="text-[var(--muted)]">深度模型</span>
                <select
                  value={deepModel}
                  onChange={(e) => setDeepModel(e.target.value)}
                  className="mt-1 w-full rounded border border-[var(--border)] bg-[var(--surface-2)] px-3 py-2"
                >
                  {selectedProvider.models.deep.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          )}

          <div className="card p-5 space-y-2 text-sm">
            <div>方案：{selected.label}</div>
            <div>标的：{ticker.toUpperCase()}</div>
            <div>时点：{useToday ? todayStr() + "（当前）" : analysisDate}</div>
            <div>引擎：{selectedProvider?.label ?? providerId}</div>
          </div>
          <div className="card p-5">
            <div className="text-lg font-medium">本次消耗 {points} 点</div>
            {estimate && (
              <div className="text-xs text-[var(--muted)] mt-1">
                {estimate.base_points} 点（方案） × {estimate.provider_factor}（引擎）
              </div>
            )}
            <div className="text-sm text-[var(--muted)] mt-2">剩余配额 {remaining.toFixed(1)} 点</div>
          </div>
          <label className="flex items-start gap-2 text-sm">
            <input type="checkbox" checked={agreed} onChange={(e) => setAgreed(e.target.checked)} />
            我已阅读并理解：AX 提供 AI 研究辅助，不构成投资建议。
          </label>
          {error && <p className="text-sm text-[var(--danger)]">{error}</p>}
        </section>
      )}

      <div className="mt-8 flex justify-between">
        {step > 1 ? (
          <button
            type="button"
            onClick={() => setStep((s) => s - 1)}
            className="rounded-lg border border-[var(--border)] px-4 py-2 text-sm"
          >
            上一步
          </button>
        ) : (
          <Link href="/workspace" className="text-sm text-[var(--muted)] py-2">
            取消
          </Link>
        )}
        {step < 4 ? (
          <button
            type="button"
            disabled={(step === 1 && selected?.locked) || (step === 2 && !ticker.trim())}
            onClick={() => setStep((s) => s + 1)}
            className="rounded-lg bg-[var(--accent)] px-5 py-2 text-sm text-white disabled:opacity-40"
          >
            下一步
          </button>
        ) : (
          <button
            type="button"
            disabled={!agreed || submitting || remaining < points}
            onClick={submit}
            className="rounded-lg bg-[var(--accent)] px-5 py-2 text-sm text-white disabled:opacity-40"
          >
            {submitting ? "提交中…" : "开始分析 — 进入分析室"}
          </button>
        )}
      </div>
    </div>
  );
}

export default function NewAnalysisPage() {
  return (
    <Suspense fallback={<div className="text-[var(--muted)]">加载向导…</div>}>
      <WizardContent />
    </Suspense>
  );
}

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}
