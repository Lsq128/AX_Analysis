"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { AuthGuard } from "@/components/AuthGuard";
import { useBillingEnabled } from "@/hooks/useBillingEnabled";
import { fetchMe, isLoggedIn, logout } from "@/lib/api";
import type { UserMe } from "@/lib/types";

const baseNav = [
  { href: "/workspace", label: "首页" },
  { href: "/workspace/analyses/new", label: "发起分析" },
  { href: "/workspace/reports", label: "报告库" },
  { href: "/workspace/memory", label: "复盘" },
];

export default function WorkspaceLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [me, setMe] = useState<UserMe | null>(null);
  const billingEnabled = useBillingEnabled();

  useEffect(() => {
    fetchMe().then(setMe).catch(() => setMe(null));
  }, []);

  function onLogout() {
    logout();
    router.push("/login");
  }

  const navItems = useMemo(() => {
    const items = [...baseNav];
    if (billingEnabled) {
      items.push({ href: "/workspace/billing", label: "套餐" });
      if (me?.is_admin) {
        items.push({ href: "/workspace/admin", label: "管理" });
      }
    }
    return items;
  }, [billingEnabled, me?.is_admin]);

  return (
    <div className="min-h-screen flex flex-col">
      <header className="sticky top-0 z-10 border-b border-[var(--border)]/80 bg-[var(--bg)]/85 backdrop-blur-md">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
          <div className="flex items-center gap-8">
            <Link href="/" className="font-display text-lg font-semibold tracking-tight">
              <span className="text-[var(--accent)]">AX</span>
              <span className="ml-1.5 font-sans text-sm font-medium text-[var(--muted)]">Analysis</span>
            </Link>
            <nav className="hidden sm:flex gap-1 text-sm">
              {navItems.map((item) => {
                const active =
                  item.href === "/workspace"
                    ? pathname === "/workspace"
                    : pathname === item.href || pathname.startsWith(`${item.href}/`);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`rounded-full px-3 py-1.5 transition-colors ${
                      active
                        ? "bg-[var(--accent-dim)] text-[var(--accent)] font-medium"
                        : "text-[var(--muted)] hover:text-[var(--text)]"
                    }`}
                  >
                    {item.label}
                  </Link>
                );
              })}
            </nav>
          </div>
          <div className="flex items-center gap-4 text-sm">
            {billingEnabled && (
              <span className="text-[var(--muted)] hidden sm:inline tabular-nums">
                {me
                  ? `${me.points_remaining.toFixed(1)} / ${me.points_limit.toFixed(0)} 点 · ${me.plan_label}`
                  : "…"}
              </span>
            )}
            {isLoggedIn() ? (
              <button type="button" onClick={onLogout} className="text-[var(--muted)] hover:text-[var(--text)]">
                退出
              </button>
            ) : (
              <Link href="/login" className="text-[var(--muted)] hover:text-[var(--text)]">
                登录
              </Link>
            )}
          </div>
        </div>
      </header>
      <main className="flex-1 mx-auto w-full max-w-6xl px-4 py-8">
        <AuthGuard>{children}</AuthGuard>
      </main>
      <footer className="border-t border-[var(--border)] py-4 text-center text-xs text-[var(--muted)] space-x-3">
        <span>AX 提供 AI 研究辅助，不构成投资建议</span>
        <Link href="/legal/disclaimer" className="hover:text-[var(--text)]">
          免责声明
        </Link>
        <Link href="/legal/data" className="hover:text-[var(--text)]">
          数据说明
        </Link>
      </footer>
    </div>
  );
}
