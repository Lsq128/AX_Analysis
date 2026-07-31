"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { AuthGuard } from "@/components/AuthGuard";
import { fetchMe, isLoggedIn, logout } from "@/lib/api";
import type { UserMe } from "@/lib/types";

const nav = [
  { href: "/workspace", label: "首页" },
  { href: "/workspace/analyses/new", label: "发起分析" },
  { href: "/workspace/reports", label: "报告库" },
  { href: "/workspace/memory", label: "复盘" },
  { href: "/workspace/billing", label: "套餐" },
];

export default function WorkspaceLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [me, setMe] = useState<UserMe | null>(null);

  useEffect(() => {
    fetchMe().then(setMe).catch(() => setMe(null));
  }, []);

  function onLogout() {
    logout();
    router.push("/login");
  }

  const navItems = me?.is_admin
    ? [...nav, { href: "/workspace/admin", label: "管理" }]
    : nav;

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-[var(--border)] bg-[var(--surface)]/80 backdrop-blur sticky top-0 z-10">
        <div className="mx-auto max-w-6xl px-4 h-14 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <Link href="/" className="font-semibold tracking-tight">
              <span className="text-[var(--accent)]">AX</span>_Analysis
            </Link>
            <nav className="hidden sm:flex gap-5 text-sm text-[var(--muted)]">
              {navItems.map((item) => (
                <Link key={item.href} href={item.href} className="hover:text-[var(--text)]">
                  {item.label}
                </Link>
              ))}
            </nav>
          </div>
          <div className="flex items-center gap-4 text-sm">
            <span className="text-[var(--muted)] hidden sm:inline" id="quota-badge">
              {me
                ? `配额 ${me.points_remaining.toFixed(1)} / ${me.points_limit.toFixed(0)} 点 · ${me.plan_label}`
                : "加载配额…"}
            </span>
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
