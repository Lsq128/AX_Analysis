import Link from "next/link";

export default function MarketingLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-[var(--border)] bg-[var(--surface)]/70 backdrop-blur sticky top-0 z-10">
        <div className="mx-auto max-w-6xl px-4 h-14 flex items-center justify-between">
          <Link href="/" className="font-semibold">
            <span className="text-[var(--accent)]">AX</span>_Analysis
          </Link>
          <nav className="flex items-center gap-4 text-sm">
            <a href="#features" className="text-[var(--muted)] hover:text-[var(--text)]">
              能力
            </a>
            <a href="#pricing" className="text-[var(--muted)] hover:text-[var(--text)]">
              方案
            </a>
            <Link href="/login" className="text-[var(--muted)] hover:text-[var(--text)]">
              登录
            </Link>
            <Link
              href="/workspace"
              className="rounded-lg bg-[var(--accent)] px-4 py-2 text-white font-medium hover:opacity-90"
            >
              进入工作台
            </Link>
          </nav>
        </div>
      </header>
      <main className="flex-1">{children}</main>
      <footer className="border-t border-[var(--border)] py-8 text-center text-xs text-[var(--muted)] space-x-3">
        <span>AX 提供 AI 研究辅助，不构成投资建议 · © AX_Analysis</span>
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
