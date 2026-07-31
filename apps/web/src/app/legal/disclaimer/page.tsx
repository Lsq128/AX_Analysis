import Link from "next/link";

export default function DisclaimerPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-16 space-y-6">
      <Link href="/" className="text-sm text-[var(--muted)] hover:text-[var(--text)]">
        ← 返回首页
      </Link>
      <h1 className="text-3xl font-semibold">免责声明</h1>
      <div className="prose prose-invert max-w-none text-sm leading-relaxed text-[var(--muted)] space-y-4">
        <p>
          AX_Analysis 提供的所有分析结果、评级、交易建议及报告内容，均由人工智能模型基于公开或授权数据自动生成，
          <strong className="text-[var(--text)]">仅供研究辅助与学习参考，不构成任何投资建议、要约或承诺</strong>。
        </p>
        <p>
          证券市场存在风险，历史表现不代表未来收益。用户应独立判断并自行承担投资决策的全部后果。
          AX 及其运营方不对因使用本产品而产生的任何直接或间接损失承担责任。
        </p>
        <p>
          分析结论基于提交任务时的可见信息，可能存在延迟、遗漏或模型幻觉。请勿将 AI 输出作为唯一决策依据。
        </p>
      </div>
    </div>
  );
}
