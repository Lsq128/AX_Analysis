import Link from "next/link";
import { MarketingPresets } from "@/components/MarketingPresets";

const features = [
  {
    title: "多 Agent 五幕推演",
    desc: "技术面、舆情、资讯、基本面到多空辩论、交易员、风控与组合经理，全流程可追踪。",
  },
  {
    title: "Live 分析室",
    desc: "SSE 实时进度，看见每个 Agent 在做什么，而不是黑盒等待。",
  },
  {
    title: "A 股 · 港股 · 美股",
    desc: "一套工作流覆盖主要市场，默认中文输出，面向国内个人投资者。",
  },
];

export default function MarketingHome() {
  return (
    <>
      <section className="mx-auto max-w-6xl px-4 py-20 grid lg:grid-cols-2 gap-12 items-center">
        <div>
          <p className="text-sm text-[var(--accent)] font-medium mb-3">国内个人投资者 · AI 投研</p>
          <h1 className="text-4xl sm:text-5xl font-bold leading-tight tracking-tight">
            像机构一样
            <br />
            <span className="text-[var(--accent)]">推演每一只股票</span>
          </h1>
          <p className="mt-5 text-lg text-[var(--muted)] max-w-xl leading-relaxed">
            AX_Analysis 将多 Agent 引擎产品化：向导式发起、Live 分析室、结构化决策报告。
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link
              href="/workspace/analyses/new"
              className="rounded-xl bg-[var(--accent)] px-6 py-3 font-medium text-white hover:opacity-90 active:scale-[0.98]"
            >
              免费体验分析
            </Link>
            <Link
              href="/login"
              className="rounded-xl border border-[var(--border)] px-6 py-3 font-medium hover:border-[var(--accent)] active:scale-[0.98]"
            >
              登录 / 注册
            </Link>
          </div>
        </div>
        <div className="card p-6 space-y-4 bg-gradient-to-br from-[var(--surface)] to-[var(--surface-2)]">
          <div className="text-sm text-[var(--muted)]">分析室预览</div>
          <div className="grid grid-cols-[120px_1fr] gap-4 min-h-[280px]">
            <div className="space-y-2 text-xs">
              {["技术面 ✓", "市场情绪 ◐", "资讯 ○", "基本面 ○", "多空辩论 ○"].map((s) => (
                <div key={s} className="text-[var(--muted)]">
                  {s}
                </div>
              ))}
            </div>
            <div className="rounded-lg bg-[var(--bg)] p-4 text-sm text-[var(--muted)] leading-relaxed">
              「MACD 出现失败金叉，200 日均线支撑正在经受第 3 次测试…」
              <br />
              <br />
              <span className="text-[var(--accent)]">Live 流式输出中</span>
            </div>
          </div>
        </div>
      </section>

      <section id="features" className="border-t border-[var(--border)] bg-[var(--surface)]/40 py-16">
        <div className="mx-auto max-w-6xl px-4">
          <h2 className="text-2xl font-semibold tracking-tight mb-8">为什么选择 AX</h2>
          <div className="grid md:grid-cols-3 gap-6">
            {features.map((f) => (
              <div key={f.title} className="border-t border-[var(--border)] pt-5">
                <h3 className="font-medium mb-2">{f.title}</h3>
                <p className="text-sm text-[var(--muted)] leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <MarketingPresets />

      <section className="border-t border-[var(--border)] py-16 text-center">
        <h2 className="text-2xl font-semibold tracking-tight">准备好开始了吗？</h2>
        <Link
          href="/workspace/analyses/new"
          className="inline-block mt-6 rounded-xl bg-[var(--accent)] px-8 py-3 font-medium text-white hover:opacity-90 active:scale-[0.98]"
        >
          发起第一次分析
        </Link>
      </section>
    </>
  );
}
