"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { fetchAuthConfig, isLoggedIn, login, oauthStartUrl } from "@/lib/api";
import type { AuthConfig } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [config, setConfig] = useState<AuthConfig | null>(null);
  const [userId, setUserId] = useState("demo");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isLoggedIn()) {
      router.replace("/workspace");
      return;
    }
    fetchAuthConfig().then(setConfig).catch(console.error);
  }, [router]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await login(userId.trim(), displayName.trim() || undefined);
      router.push("/workspace");
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
      <div className="card w-full max-w-md p-8 space-y-5">
        <div>
          <h1 className="text-xl font-semibold">登录 AX_Analysis</h1>
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
                className="block w-full rounded-lg border border-[var(--border)] py-2.5 text-center text-sm hover:border-[var(--accent)]"
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
                className="w-full rounded-lg border border-[var(--border)] bg-[var(--surface-2)] px-3 py-2"
                required
              />
            </label>
            <label className="block space-y-1 text-sm">
              <span className="text-[var(--muted)]">显示名称（可选）</span>
              <input
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                className="w-full rounded-lg border border-[var(--border)] bg-[var(--surface-2)] px-3 py-2"
              />
            </label>
            {error && <p className="text-sm text-[var(--danger)]">{error}</p>}
            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-lg bg-[var(--accent)] py-2.5 text-sm font-medium text-white disabled:opacity-50"
            >
              {loading ? "登录中…" : "进入工作台"}
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
