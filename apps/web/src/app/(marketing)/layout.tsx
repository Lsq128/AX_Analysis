import Link from "next/link";

export default function MarketingLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="sticky top-0 z-10 border-b border-[var(--border)]/80 bg-[var(--bg)]/80 backdrop-blur-md">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
          <Link href="/" className="font-display text-lg font-semibold tracking-tight">
            <span className="text-[var(--accent)]">AX</span>
            <span className="text-[var(--muted)] font-sans text-sm font-medium ml-1.5">Analysis</span>
          </Link>
          <nav className="flex items-center gap-5 text-sm">
            <a href="#features" className="hidden sm:inline text-[var(--muted)] hover:text-[var(--text)]">
              能力
            </a>
            <a href="#pricing" className="hidden sm:inline text-[var(--muted)] hover:text-[var(--text)]">
              方案
            </a>
            <Link href="/login" className="text-[var(--muted)] hover:text-[var(--text)]">
              登录
            </Link>
            <Link href="/workspace" className="ax-btn-primary !px-4 !py-2 text-sm">
              工作台
            </Link>
          </nav>
        </div>
      </header>
      <main className="flex-1">{children}</main>
      <footer className="border-t border-[var(--border)] py-6 text-center text-xs text-[var(--muted)] space-x-3">
        <span>© AX_Analysis</span>
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
