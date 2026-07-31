"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { fetchAuthConfig, isLoggedIn, login, oauthStartUrl } from "@/lib/api";
import type { AuthConfig } from "@/lib/api";

function safeNext(raw: string | null): string {
  if (!raw || !raw.startsWith("/") || raw.startsWith("//")) return "/workspace";
  return raw;
}

function LoginForm() {
  const router = useRouter();
  const search = useSearchParams();
  const nextPath = safeNext(search.get("next"));
  const [config, setConfig] = useState<AuthConfig | null>(null);
  const [userId, setUserId] = useState("demo");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isLoggedIn()) {
      router.replace(nextPath);
      return;
    }
    fetchAuthConfig().then(setConfig).catch(console.error);
  }, [router, nextPath]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await login(userId.trim(), displayName.trim() || undefined);
      router.push(nextPath);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  const oauthProviders = config?.oauth_providers || [];
  const showDevLogin = config?.dev_login ?? true;

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="card w-full max-w-md p-8 space-y-5 shadow-sm">
        <div>
          <p className="font-display text-3xl font-semibold tracking-tight">
            <span className="text-[var(--accent)]">AX</span>
          </p>
          <h1 className="mt-3 text-lg font-semibold">登录后继续分析</h1>
          <p className="text-sm text-[var(--muted)] mt-1">
            {oauthProviders.length
              ? "使用 OAuth 登录，或在开发模式下使用本地账号"
              : "登录后进入 AI 投研工作台"}
          </p>
        </div>

        {oauthProviders.length > 0 && (
          <div className="space-y-2">
            {oauthProviders.map((provider) => (
              <a
                key={provider.id}
                href={oauthStartUrl(provider.id)}
                className="block w-full rounded-full border border-[var(--border)] py-2.5 text-center text-sm hover:border-[var(--accent)]"
              >
                使用 {provider.label} 登录
              </a>
            ))}
          </div>
        )}

        {showDevLogin && (
          <form onSubmit={onSubmit} className="space-y-4">
            {oauthProviders.length > 0 && (
              <div className="text-xs text-[var(--muted)] text-center">— 或开发模式登录 —</div>
            )}
            <label className="block space-y-1 text-sm">
              <span className="text-[var(--muted)]">用户 ID</span>
              <input
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
                className="w-full rounded-xl border border-[var(--border)] bg-[var(--surface)] px-3 py-2.5 outline-none focus:border-[var(--accent)]"
                required
              />
            </label>
            <label className="block space-y-1 text-sm">
              <span className="text-[var(--muted)]">显示名称（可选）</span>
              <input
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                className="w-full rounded-xl border border-[var(--border)] bg-[var(--surface)] px-3 py-2.5 outline-none focus:border-[var(--accent)]"
              />
            </label>
            {error && <p className="text-sm text-[var(--danger)]">{error}</p>}
            <button type="submit" disabled={loading} className="ax-btn-primary w-full !rounded-xl">
              {loading ? "登录中…" : "进入"}
            </button>
          </form>
        )}

        {!showDevLogin && oauthProviders.length === 0 && (
          <p className="text-sm text-[var(--danger)]">未配置 OAuth 提供商，请联系管理员。</p>
        )}

        <Link href="/" className="block text-center text-sm text-[var(--muted)] hover:text-[var(--text)]">
          返回首页
        </Link>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="min-h-screen" />}>
      <LoginForm />
    </Suspense>
  );
}
