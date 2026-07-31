"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { DebateTimeline } from "@/components/DebateTimeline";
import { JobStatsPanel } from "@/components/JobStatsPanel";
import { MarkdownView } from "@/components/MarkdownView";
import { fetchJob, retryAnalysis, subscribeAnalysisEvents } from "@/lib/api";
import { jobErrorMessage, jobIsRetryable } from "@/lib/jobErrors";
import { presetLabelZh } from "@/lib/presets";
import {
  AGENT_ACTS,
  AGENT_LABELS,
  type AnalysisJob,
  type DebateTimelineEntry,
  type ProgressEvent,
} from "@/lib/types";

type LiveTab = "live" | "debate" | "log";

const REPORT_KEY_BY_AGENT: Record<string, string> = {
  "Market Analyst": "market_report",
  "Sentiment Analyst": "sentiment_report",
  "News Analyst": "news_report",
  "Fundamentals Analyst": "fundamentals_report",
  Trader: "trader_investment_plan",
  "Portfolio Manager": "final_trade_decision",
};

export default function AnalysisRoomPage() {
  const params = useParams();
  const jobId = params.id as string;
  const [job, setJob] = useState<AnalysisJob | null>(null);
  const [agentStatus, setAgentStatus] = useState<Record<string, string>>({});
  const [reportSections, setReportSections] = useState<Record<string, string>>({});
  const [debateTimeline, setDebateTimeline] = useState<DebateTimelineEntry[]>([]);
  const [messages, setMessages] = useState<Array<{ role: string; content: string }>>([]);
  const [toolCalls, setToolCalls] = useState<Array<{ name: string; args?: Record<string, unknown> }>>([]);
  const [tab, setTab] = useState<LiveTab>("live");
  const [error, setError] = useState("");

  useEffect(() => {
    fetchJob(jobId).then(setJob).catch((e) => setError(e.message));
  }, [jobId]);

  useEffect(() => {
    if (!jobId) return;
    const unsub = subscribeAnalysisEvents(
      jobId,
      (raw) => {
        const event = raw as ProgressEvent;
        if (event.status && (event.type === "status" || event.type === "queued" || event.type === "started")) {
          setJob((j) => (j ? { ...j, status: event.status as AnalysisJob["status"] } : j));
        }
        // Late-join status payloads may omit type but include job fields.
        if (!event.type && event.status && (event as { job_id?: string }).job_id) {
          setJob((j) => (j ? { ...j, status: event.status as AnalysisJob["status"] } : j));
        }
        if (event.type === "progress") {
          if (event.agent_status) setAgentStatus(event.agent_status);
          if (event.report_sections) setReportSections(event.report_sections);
          if (event.debate_timeline) setDebateTimeline(event.debate_timeline);
        }
        if (event.type === "message" && event.content) {
          setMessages((m) => [...m.slice(-80), { role: event.role || "Agent", content: event.content! }]);
        }
        if (event.type === "tool_call" && event.name) {
          setToolCalls((t) => [...t.slice(-30), { name: event.name!, args: event.args }]);
        }
        if (event.type === "completed" || event.type === "failed") {
          fetchJob(jobId).then(setJob).catch(console.error);
        }
      },
      (e) => setError(e.message),
    );
    return unsub;
  }, [jobId]);

  const activeAgent = useMemo(() => {
    const entry = Object.entries(agentStatus).find(([, s]) => s === "in_progress");
    return entry?.[0] || null;
  }, [agentStatus]);

  const liveMarkdown = useMemo(() => {
    if (activeAgent) {
      const key = REPORT_KEY_BY_AGENT[activeAgent];
      if (key && reportSections[key]) return reportSections[key];
    }
    const sections = Object.values(reportSections).filter(Boolean);
    if (sections.length) return sections[sections.length - 1] as string;
    const lastTimeline = debateTimeline[debateTimeline.length - 1];
    return lastTimeline?.content || "";
  }, [activeAgent, reportSections, debateTimeline]);

  const hasDebate = debateTimeline.some((e) => e.act === "research" || e.act === "risk" || e.act === "decision");

  if (!job && !error) {
    return <div className="text-[var(--muted)]">加载分析室…</div>;
  }

  if (error && !job) {
    return <div className="text-[var(--danger)]">{error}</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
        <div>
          <Link href="/workspace" className="text-sm text-[var(--muted)] hover:text-[var(--text)]">
            ← 返回
          </Link>
          <h1 className="text-xl font-semibold mt-1 tracking-tight">
            {job?.ticker}
            <span className="text-[var(--muted)] font-normal">
              {" "}
              · {presetLabelZh(job?.preset_id)} · {job?.analysis_date}
            </span>
          </h1>
        </div>
        <span className={`badge badge-${job?.status || "queued"}`}>{statusLabel(job?.status)}</span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-4">
        <aside className="card p-4 space-y-4 h-fit">
          <h2 className="text-sm font-medium text-[var(--muted)]">五幕进度</h2>
          {AGENT_ACTS.map((act) => (
            <div key={act.id}>
              <div className="text-xs font-medium mb-2">{act.title}</div>
              <ul className="space-y-1.5">
                {act.agents.map((agent) => {
                  const included = isAgentIncluded(agent, job?.analysts || []);
                  const status = agentStatus[agent] || "pending";
                  if (!included && act.id === "analysts") return null;
                  return (
                    <li key={agent} className="flex items-center gap-2 text-sm">
                      <StatusDot status={included ? status : "skipped"} />
                      <span className={status === "in_progress" ? "text-[var(--accent)]" : "text-[var(--muted)]"}>
                        {AGENT_LABELS[agent] || agent}
                      </span>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </aside>

        <section className="card p-5 min-h-[420px] space-y-4">
          {job?.status === "completed" ? (
            <CompletedPanel job={job} debateTimeline={debateTimeline} />
          ) : job?.status === "failed" ? (
            <FailedPanel job={job} onRetried={() => fetchJob(jobId).then(setJob).catch(console.error)} />
          ) : (
            <>
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="text-sm text-[var(--muted)]">
                  {activeAgent
                    ? `${AGENT_LABELS[activeAgent] || activeAgent} · 进行中`
                    : job?.status === "running"
                      ? "分析进行中，同步 Agent 进度…"
                      : job?.status === "queued"
                        ? "排队中，等待 Worker 领取…"
                        : "连接实时通道…"}
                </div>
                <div className="flex gap-1 rounded-lg border border-[var(--border)] p-1 text-xs">
                  <TabButton active={tab === "live"} onClick={() => setTab("live")}>
                    Live 报告
                  </TabButton>
                  <TabButton active={tab === "debate"} onClick={() => setTab("debate")} disabled={!hasDebate}>
                    辩论时间线
                  </TabButton>
                  <TabButton active={tab === "log"} onClick={() => setTab("log")}>
                    活动日志
                  </TabButton>
                </div>
              </div>

              {tab === "live" && (
                <div className="rounded-lg bg-[var(--surface-2)] p-4 max-h-[420px] overflow-y-auto">
                  {liveMarkdown ? (
                    <MarkdownView content={liveMarkdown} />
                  ) : (
                    <p className="text-sm text-[var(--muted)]">Live 报告片段将在此流式展示…</p>
                  )}
                </div>
              )}

              {tab === "debate" && <DebateTimeline entries={debateTimeline} />}

              {tab === "log" && (
                <div className="space-y-3 max-h-[420px] overflow-y-auto text-xs">
                  {toolCalls.map((t, i) => (
                    <div key={`tool-${i}`} className="rounded border border-[var(--border)] px-3 py-2">
                      <span className="text-[var(--accent)]">工具</span> {t.name}
                    </div>
                  ))}
                  {messages.slice(-20).map((m, i) => (
                    <div key={`msg-${i}`} className="text-[var(--muted)]">
                      <span className="text-[var(--accent)]">[{m.role}]</span> {m.content.slice(0, 400)}
                    </div>
                  ))}
                  {!toolCalls.length && !messages.length && (
                    <p className="text-[var(--muted)]">工具调用与 Agent 消息将在此显示</p>
                  )}
                </div>
              )}
            </>
          )}
        </section>
      </div>
    </div>
  );
}

function CompletedPanel({
  job,
  debateTimeline,
}: {
  job: AnalysisJob;
  debateTimeline: DebateTimelineEntry[];
}) {
  return (
    <div className="space-y-4">
      <div className="text-[var(--success)] font-medium">✅ 分析完成</div>
      <JobStatsPanel job={job} />
      <MarkdownView content={job.decision_preview || "决策已生成"} />
      {debateTimeline.length > 0 && <DebateTimeline entries={debateTimeline} compact />}
      <div className="flex flex-wrap gap-3">
        <Link
          href={`/workspace/analyses/${job.job_id}/report`}
          className="rounded-lg bg-[var(--accent)] px-4 py-2 text-sm text-white"
        >
          查看决策摘要报告
        </Link>
        <Link href="/workspace/reports" className="rounded-lg border border-[var(--border)] px-4 py-2 text-sm">
          报告库
        </Link>
        <Link
          href={`/workspace/analyses/new?ticker=${encodeURIComponent(job.ticker)}`}
          className="rounded-lg border border-[var(--border)] px-4 py-2 text-sm"
        >
          对 {job.ticker} 再分析
        </Link>
      </div>
    </div>
  );
}

function FailedPanel({ job, onRetried }: { job: AnalysisJob; onRetried: () => void }) {
  const [retrying, setRetrying] = useState(false);
  const [retryError, setRetryError] = useState("");

  async function onRetry() {
    setRetrying(true);
    setRetryError("");
    try {
      await retryAnalysis(job.job_id);
      onRetried();
    } catch (e) {
      setRetryError((e as Error).message);
    } finally {
      setRetrying(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="rounded-lg border border-[var(--danger)]/40 bg-[var(--danger)]/10 p-4">
        <div className="font-medium text-[var(--danger)]">分析失败</div>
        <p className="text-sm mt-2">{jobErrorMessage(job)}</p>
        {job.error_code && (
          <p className="text-xs text-[var(--muted)] mt-2">错误码：{job.error_code}</p>
        )}
      </div>
      {retryError && <p className="text-sm text-[var(--danger)]">{retryError}</p>}
      <div className="flex flex-wrap gap-3">
        {jobIsRetryable(job) && (
          <button
            type="button"
            disabled={retrying}
            onClick={onRetry}
            className="rounded-lg bg-[var(--accent)] px-4 py-2 text-sm text-white disabled:opacity-50"
          >
            {retrying ? "重新排队…" : "重试（不重复扣点）"}
          </button>
        )}
        <Link
          href={`/workspace/analyses/new?ticker=${encodeURIComponent(job.ticker)}`}
          className="rounded-lg border border-[var(--border)] px-4 py-2 text-sm"
        >
          重新发起分析
        </Link>
      </div>
    </div>
  );
}

function TabButton({
  active,
  onClick,
  disabled,
  children,
}: {
  active: boolean;
  onClick: () => void;
  disabled?: boolean;
  children: ReactNode;
}) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={`rounded-md px-3 py-1.5 transition-colors disabled:opacity-40 ${
        active ? "bg-[var(--accent)] text-white" : "text-[var(--muted)] hover:text-[var(--text)]"
      }`}
    >
      {children}
    </button>
  );
}

function StatusDot({ status }: { status: string }) {
  const color =
    status === "completed"
      ? "bg-[var(--success)]"
      : status === "in_progress"
        ? "bg-[var(--accent)] animate-pulse"
        : status === "skipped"
          ? "bg-transparent border border-[var(--border)]"
          : "bg-[var(--border)]";
  return <span className={`inline-block w-2 h-2 rounded-full ${color}`} />;
}

function isAgentIncluded(agent: string, analysts: string[]) {
  const map: Record<string, string> = {
    "Market Analyst": "market",
    "Sentiment Analyst": "social",
    "News Analyst": "news",
    "Fundamentals Analyst": "fundamentals",
  };
  const key = map[agent];
  return !key || analysts.includes(key);
}

function statusLabel(s?: string) {
  return { queued: "排队中", running: "运行中", completed: "已完成", failed: "失败" }[s || ""] || s;
}
