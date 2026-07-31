export type Preset = {
  id: string;
  label: string;
  analysts: string[];
  research_depth: number;
  quota_points: number;
  eta_minutes: number;
  description: string;
  locked?: boolean;
};

export type AnalysisJob = {
  job_id: string;
  user_id: string;
  ticker: string;
  analysis_date: string;
  preset_id: string | null;
  analysts: string[];
  research_depth: number;
  status: "queued" | "running" | "completed" | "failed";
  created_at: string;
  updated_at: string;
  report_path?: string | null;
  error?: string | null;
  error_code?: string | null;
  error_message?: string | null;
  retryable?: boolean | null;
  stats?: Record<string, number> | null;
  decision_preview?: string | null;
  points_charged?: number | null;
};

export type UserMe = {
  user_id: string;
  display_name: string;
  plan_id: string;
  plan_label: string;
  points_limit: number;
  points_used: number;
  points_remaining: number;
  is_admin: boolean;
};

export type BillingPlan = {
  id: string;
  label: string;
  points_limit: number;
  price_cny: number;
  description: string;
};

export type AdminUser = {
  user_id: string;
  display_name: string;
  plan_id: string;
  plan_label: string;
  points_limit: number;
  points_used: number;
  points_remaining: number;
  created_at?: string | null;
};

export type AdminStats = {
  user_count: number;
  job_count: number;
  total_points_used: number;
};

export type MemoryEntry = {
  id: string;
  date: string;
  ticker: string;
  rating: string;
  rating_label: string;
  pending: boolean;
  raw_return?: string | null;
  alpha_return?: string | null;
  holding_days?: number | null;
  decision: string;
  reflection: string;
};

export type MemoryStats = {
  total_entries: number;
  pending_count: number;
  resolved_count: number;
  tickers_pending: string[];
};

export type RecentTicker = {
  ticker: string;
  last_analysis_date: string;
  last_job_id: string;
  last_status: string;
};

export type TickerSearchResult = {
  ticker: string;
  name?: string | null;
  market?: string | null;
  source: string;
};

export const RATING_COLORS: Record<string, string> = {
  Buy: "text-[var(--success)]",
  Overweight: "text-[var(--success)]",
  Hold: "text-[var(--muted)]",
  Underweight: "text-[var(--warning)]",
  Sell: "text-[var(--danger)]",
};

export type LlmModelOption = {
  label: string;
  id: string;
};

export type LlmProvider = {
  id: string;
  label: string;
  quota_factor: number;
  description: string;
  models: {
    quick: LlmModelOption[];
    deep: LlmModelOption[];
  };
  defaults: {
    quick: string;
    deep: string;
  };
};

export type QuotaEstimate = {
  preset_id: string;
  preset_label: string;
  base_points: number;
  provider_id: string;
  provider_factor: number;
  total_points: number;
};

export type ReportSection = {
  key: string;
  label: string;
  path: string;
};

export type SignedReportUrl = {
  key: string;
  label: string;
  path: string;
  url: string;
  expires_at: string;
};

export type ProgressEvent = {
  type: string;
  job_id?: string;
  status?: string;
  role?: string;
  content?: string;
  name?: string;
  args?: Record<string, unknown>;
  agent_status?: Record<string, string>;
  report_sections?: Record<string, string>;
  debate_timeline?: DebateTimelineEntry[];
  error?: string;
  report_path?: string;
};

export type DebateTimelineEntry = {
  id: string;
  act: "analysts" | "research" | "trading" | "risk" | "decision";
  agent: string;
  content: string;
  kind: "report" | "debate" | "decision" | "tool";
  side?: "bull" | "bear" | "aggressive" | "conservative" | "neutral";
  round?: number;
};

export const ANALYST_LABELS: Record<string, string> = {
  market: "技术面研判",
  social: "市场情绪",
  news: "资讯与宏观",
  fundamentals: "基本面体检",
};

export const AGENT_ACTS = [
  {
    id: "analysts",
    title: "第一幕 · 分析师团队",
    agents: ["Market Analyst", "Sentiment Analyst", "News Analyst", "Fundamentals Analyst"],
  },
  {
    id: "research",
    title: "第二幕 · 研究团队",
    agents: ["Bull Researcher", "Bear Researcher", "Research Manager"],
  },
  {
    id: "trading",
    title: "第三幕 · 交易团队",
    agents: ["Trader"],
  },
  {
    id: "risk",
    title: "第四幕 · 风控团队",
    agents: ["Aggressive Analyst", "Conservative Analyst", "Neutral Analyst"],
  },
  {
    id: "decision",
    title: "第五幕 · 最终决策",
    agents: ["Portfolio Manager"],
  },
];

export const AGENT_LABELS: Record<string, string> = {
  "Market Analyst": "技术面研判",
  "Sentiment Analyst": "市场情绪",
  "News Analyst": "资讯与宏观",
  "Fundamentals Analyst": "基本面体检",
  "Bull Researcher": "多头研究员",
  "Bear Researcher": "空头研究员",
  "Research Manager": "研究经理",
  Trader: "交易员",
  "Aggressive Analyst": "激进分析师",
  "Conservative Analyst": "保守分析师",
  "Neutral Analyst": "中性分析师",
  "Portfolio Manager": "组合经理",
};
