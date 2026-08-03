import type {
  AdminStats,
  AdminUser,
  AnalysisJob,
  BillingPlan,
  LlmProvider,
  MemoryEntry,
  MemoryStats,
  Preset,
  QuotaEstimate,
  RecentTicker,
  ReportSection,
  SignedReportUrl,
  TickerSearchResult,
  UserMe,
} from "./types";

const TOKEN_KEY = "ax_access_token";
const USER_KEY = "ax_user_id";
const NAME_KEY = "ax_display_name";

const allowHeaderFallback =
  process.env.NEXT_PUBLIC_AUTH_ALLOW_HEADER !== "false";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

function userId(): string {
  if (typeof window !== "undefined") {
    return localStorage.getItem(USER_KEY) || process.env.NEXT_PUBLIC_DEV_USER_ID || "demo";
  }
  return process.env.NEXT_PUBLIC_DEV_USER_ID || "demo";
}

function authHeaders(json = true): HeadersInit {
  const h: Record<string, string> = {};
  if (json) h["Content-Type"] = "application/json";
  const token = getToken();
  if (token) {
    h["Authorization"] = `Bearer ${token}`;
  } else if (allowHeaderFallback) {
    h["X-User-Id"] = userId();
  }
  return h;
}

const base = "";

/** Dev: bypass Next rewrites for SSE (they buffer / abort long-lived streams). */
function eventsBase(): string {
  if (typeof window === "undefined") return "";
  const configured = process.env.NEXT_PUBLIC_SSE_BASE_URL;
  if (configured) return configured.replace(/\/$/, "");
  if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
    return "http://localhost:8000";
  }
  return "";
}

export type AuthConfig = {
  dev_mode: boolean;
  dev_login: boolean;
  header_fallback: boolean;
  oauth_providers: Array<{ id: string; label: string }>;
  billing_enabled: boolean;
};

export async function fetchAuthConfig(): Promise<AuthConfig> {
  const res = await fetch(`${base}/api/v1/auth/config`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load auth config");
  return res.json();
}

export function oauthStartUrl(provider: string) {
  return `${base}/api/v1/auth/oauth/${provider}/start`;
}

export async function login(userIdValue: string, displayName?: string) {
  const res = await fetch(`${base}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userIdValue, display_name: displayName }),
  });
  if (!res.ok) throw new Error("登录失败");
  const data = await res.json();
  if (typeof window !== "undefined") {
    localStorage.setItem(TOKEN_KEY, data.access_token);
    localStorage.setItem(USER_KEY, data.user_id);
    localStorage.setItem(NAME_KEY, data.display_name || data.user_id);
  }
  return data;
}

export function storeAuthSession(data: {
  access_token: string;
  user_id: string;
  display_name?: string;
}) {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, data.access_token);
  localStorage.setItem(USER_KEY, data.user_id);
  localStorage.setItem(NAME_KEY, data.display_name || data.user_id);
}

export function logout() {
  if (typeof window !== "undefined") {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    localStorage.removeItem(NAME_KEY);
  }
}

export function isLoggedIn() {
  return Boolean(getToken());
}

export async function fetchMe(): Promise<UserMe> {
  const res = await fetch(`${base}/api/v1/me`, { headers: authHeaders(false), cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load profile");
  return res.json();
}

export async function fetchBillingPlans(): Promise<BillingPlan[]> {
  const res = await fetch(`${base}/api/v1/billing/plans`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load billing plans");
  return res.json();
}

export async function fetchAdminStats(): Promise<AdminStats> {
  const res = await fetch(`${base}/api/v1/admin/stats`, { headers: authHeaders(false), cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load admin stats");
  return res.json();
}

export async function fetchAdminUsers(limit = 50, offset = 0): Promise<AdminUser[]> {
  const res = await fetch(`${base}/api/v1/admin/users?limit=${limit}&offset=${offset}`, {
    headers: authHeaders(false),
    cache: "no-store",
  });
  if (!res.ok) throw new Error("Failed to load admin users");
  return res.json();
}

export async function updateUserQuota(
  userId: string,
  body: { plan_id?: string; reset_usage?: boolean; points_limit?: number; points_used?: number },
): Promise<AdminUser> {
  const res = await fetch(`${base}/api/v1/admin/users/${encodeURIComponent(userId)}/quota`, {
    method: "PATCH",
    headers: authHeaders(),
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(typeof err.detail === "string" ? err.detail : "Update failed");
  }
  return res.json();
}

export async function fetchMemoryEntries(
  status: "all" | "pending" | "resolved" = "all",
): Promise<MemoryEntry[]> {
  const res = await fetch(`${base}/api/v1/memory/entries?status=${status}`, {
    headers: authHeaders(false),
    cache: "no-store",
  });
  if (!res.ok) throw new Error("Failed to load memory entries");
  return res.json();
}

export async function fetchMemoryStats(): Promise<MemoryStats> {
  const res = await fetch(`${base}/api/v1/memory/stats`, {
    headers: authHeaders(false),
    cache: "no-store",
  });
  if (!res.ok) throw new Error("Failed to load memory stats");
  return res.json();
}

export async function fetchPresets(): Promise<Preset[]> {
  const res = await fetch(`${base}/api/v1/presets`, { headers: authHeaders(false), cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load presets");
  return res.json();
}

export async function fetchLlmProviders(): Promise<LlmProvider[]> {
  const res = await fetch(`${base}/api/v1/llm/providers`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load LLM providers");
  return res.json();
}

export async function estimateQuota(preset: string, provider: string): Promise<QuotaEstimate> {
  const q = new URLSearchParams({ preset, provider });
  const res = await fetch(`${base}/api/v1/llm/quota-estimate?${q}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to estimate quota");
  return res.json();
}

export async function fetchJobs(limit = 10, status?: string): Promise<AnalysisJob[]> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (status) params.set("status", status);
  const res = await fetch(`${base}/api/v1/analyses?${params}`, {
    headers: authHeaders(false),
    cache: "no-store",
  });
  if (!res.ok) return [];
  return res.json();
}

export async function fetchReports(limit = 50): Promise<AnalysisJob[]> {
  const res = await fetch(`${base}/api/v1/reports?limit=${limit}`, {
    headers: authHeaders(false),
    cache: "no-store",
  });
  if (!res.ok) throw new Error("Failed to load reports");
  return res.json();
}

export async function fetchJob(jobId: string): Promise<AnalysisJob> {
  const res = await fetch(`${base}/api/v1/analyses/${jobId}`, {
    headers: authHeaders(false),
    cache: "no-store",
  });
  if (!res.ok) throw new Error("Job not found");
  return res.json();
}

export async function retryAnalysis(jobId: string): Promise<AnalysisJob> {
  const res = await fetch(`${base}/api/v1/analyses/${jobId}/retry`, {
    method: "POST",
    headers: authHeaders(false),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    const detail = err.detail;
    const msg =
      typeof detail === "string"
        ? detail
        : detail?.message || "重试失败";
    throw new Error(msg);
  }
  return res.json();
}

export async function fetchRecentTickers(limit = 8): Promise<RecentTicker[]> {
  const res = await fetch(`${base}/api/v1/tickers/recent?limit=${limit}`, {
    headers: authHeaders(false),
    cache: "no-store",
  });
  if (!res.ok) return [];
  return res.json();
}

export async function searchTickers(q: string, limit = 8): Promise<TickerSearchResult[]> {
  if (!q.trim()) return [];
  const params = new URLSearchParams({ q: q.trim(), limit: String(limit) });
  const res = await fetch(`${base}/api/v1/tickers/search?${params}`, {
    headers: authHeaders(false),
    cache: "no-store",
  });
  if (!res.ok) return [];
  return res.json();
}

export function reportExportUrl(jobId: string): string {
  return `${base}/api/v1/analyses/${jobId}/report/export`;
}

export async function downloadReportExport(jobId: string): Promise<void> {
  const res = await fetch(reportExportUrl(jobId), { headers: authHeaders(false) });
  if (!res.ok) throw new Error("导出失败");
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `ax-report-${jobId}.zip`;
  anchor.click();
  URL.revokeObjectURL(url);
}

export async function fetchReportSections(jobId: string): Promise<ReportSection[]> {
  const res = await fetch(`${base}/api/v1/analyses/${jobId}/report`, {
    headers: authHeaders(false),
    cache: "no-store",
  });
  if (!res.ok) throw new Error("Report not available");
  return res.json();
}

export async function fetchReportSignedUrls(jobId: string): Promise<SignedReportUrl[]> {
  const res = await fetch(`${base}/api/v1/analyses/${jobId}/report/signed-urls`, {
    headers: authHeaders(false),
    cache: "no-store",
  });
  if (res.status === 501) return [];
  if (!res.ok) throw new Error("Signed URLs not available");
  return res.json();
}

export async function fetchReportSection(jobId: string, sectionKey: string): Promise<string> {
  const res = await fetch(`${base}/api/v1/analyses/${jobId}/report/${sectionKey}`, {
    headers: authHeaders(false),
    cache: "no-store",
  });
  if (!res.ok) throw new Error("Section not found");
  const data = await res.json();
  return data.markdown as string;
}

export async function createAnalysis(body: {
  ticker: string;
  analysis_date: string;
  preset: string;
  llm_provider?: string;
  shallow_thinker?: string;
  deep_thinker?: string;
}): Promise<AnalysisJob> {
  const res = await fetch(`${base}/api/v1/analyses`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    const detail = err.detail;
    const msg =
      typeof detail === "string"
        ? detail
        : detail?.message || JSON.stringify(detail) || "Submit failed";
    throw new Error(msg);
  }
  return res.json();
}

export function subscribeAnalysisEvents(
  jobId: string,
  onEvent: (event: unknown) => void,
  onError?: (err: Error) => void,
): () => void {
  let stopped = false;
  let controller = new AbortController();

  (async () => {
    while (!stopped) {
      controller = new AbortController();
      try {
        const res = await fetch(`${eventsBase()}/api/v1/analyses/${jobId}/events`, {
          headers: { ...authHeaders(false), Accept: "text/event-stream" } as HeadersInit,
          signal: controller.signal,
          cache: "no-store",
        });
        if (!res.ok || !res.body) throw new Error("SSE connection failed");

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let terminal = false;

        while (!stopped) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const parts = buffer.split("\n\n");
          buffer = parts.pop() || "";
          for (const part of parts) {
            const dataLine = part.split("\n").find((l) => l.startsWith("data: "));
            if (!dataLine) continue;
            try {
              const payload = JSON.parse(dataLine.slice(6));
              onEvent(payload);
              if (payload?.type === "completed" || payload?.type === "failed") {
                terminal = true;
              }
            } catch {
              /* ignore */
            }
          }
        }
        if (terminal || stopped) return;
        await new Promise((r) => setTimeout(r, 1000));
      } catch (e) {
        if (stopped) return;
        // React Strict Mode aborts the first mount; a new subscriber replaces us.
        if ((e as Error).name === "AbortError") return;
        onError?.(e as Error);
        await new Promise((r) => setTimeout(r, 1500));
      }
    }
  })();

  return () => {
    stopped = true;
    controller.abort();
  };
}

export function setDevUserId(id: string) {
  if (typeof window !== "undefined") localStorage.setItem(USER_KEY, id);
}

export function getDevUserId() {
  return userId();
}
