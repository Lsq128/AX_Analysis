import Link from "next/link";
import { HomeTickerInput } from "@/components/HomeTickerInput";
import { MarketingPresets } from "@/components/MarketingPresets";

const pillars = [
  { title: "多 Agent 推演", desc: "技术、舆情、资讯、基本面到辩论与风控，全程可追踪。" },
  { title: "Live 分析室", desc: "实时进度流，看见每个角色在做什么。" },
  { title: "A / H / 美股", desc: "一套工作流覆盖主要市场，默认中文输出。" },
];

export default function MarketingHome() {
  return (
    <>
      <section className="relative flex min-h-[calc(100vh-3.5rem)] flex-col items-center justify-center px-4 pb-16 pt-10 text-center">
        <div className="ax-hero-enter max-w-3xl">
          <p className="font-display text-6xl sm:text-7xl md:text-8xl font-semibold tracking-tight text-[var(--text)]">
            <span className="text-[var(--accent)]">AX</span>
          </p>
          <h1 className="mt-5 font-display text-2xl sm:text-3xl font-medium tracking-tight text-[var(--text)]">
            输入一只股票，开始机构级推演
          </h1>
          <p className="mx-auto mt-3 max-w-md text-base text-[var(--muted)] leading-relaxed">
            AI 多 Agent 投研工作台 · 分析室实时可见 · 结构化决策报告
          </p>
        </div>

        <div className="ax-hero-enter-delay mt-10 w-full">
          <HomeTickerInput />
          <p className="mt-4 text-xs text-[var(--muted)]">
            支持 A 股、港股、美股代码。提交后进入分析向导。
          </p>
        </div>
      </section>

      <section id="features" className="border-t border-[var(--border)] bg-[var(--surface)]/70 py-20">
        <div className="mx-auto max-w-5xl px-4">
          <h2 className="font-display text-center text-2xl font-medium tracking-tight">为什么是 AX</h2>
          <div className="mt-12 grid gap-10 md:grid-cols-3">
            {pillars.map((p) => (
              <div key={p.title} className="text-center md:text-left">
                <h3 className="font-medium">{p.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-[var(--muted)]">{p.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <MarketingPresets />

      <section className="border-t border-[var(--border)] py-16 text-center px-4">
        <p className="text-sm text-[var(--muted)] max-w-lg mx-auto leading-relaxed">
          AX 提供 AI 研究辅助，不构成投资建议。
          <Link href="/legal/disclaimer" className="ml-1 text-[var(--accent)] hover:underline">
            免责声明
          </Link>
        </p>
      </section>
    </>
  );
}
