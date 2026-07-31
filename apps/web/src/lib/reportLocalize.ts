/**
 * Display-layer localization for report markdown.
 * Keeps engine tokens (BUY/HOLD/SELL, FINAL TRANSACTION PROPOSAL greppable form)
 * while presenting structural headings in Chinese with English gloss.
 */

const REPLACEMENTS: Array<[RegExp, string]> = [
  [/^# Trading Analysis Report:\s*/m, "# 投研分析报告 (Trading Analysis Report)："],
  [/^Generated:\s*/m, "生成时间 (Generated)："],

  [/^## I\.\s*Analyst Team Reports\s*$/m, "## 一、分析师团队报告 (Analyst Team Reports)"],
  [/^## II\.\s*Research Team Decision\s*$/m, "## 二、研究团队决议 (Research Team Decision)"],
  [/^## III\.\s*Trading Team Plan\s*$/m, "## 三、交易团队计划 (Trading Team Plan)"],
  [/^## IV\.\s*Risk Management Team Decision\s*$/m, "## 四、风控团队决议 (Risk Management Team Decision)"],
  [/^## V\.\s*Portfolio Manager Decision\s*$/m, "## 五、组合经理决策 (Portfolio Manager Decision)"],

  [/^### Market Analyst\s*$/m, "### 技术面分析师 (Market Analyst)"],
  [/^### Sentiment Analyst\s*$/m, "### 舆情分析师 (Sentiment Analyst)"],
  [/^### News Analyst\s*$/m, "### 资讯分析师 (News Analyst)"],
  [/^### Fundamentals Analyst\s*$/m, "### 基本面分析师 (Fundamentals Analyst)"],
  [/^### Bull Researcher(?: Analysis)?\s*$/m, "### 多头研究员 (Bull Researcher)"],
  [/^### Bear Researcher(?: Analysis)?\s*$/m, "### 空头研究员 (Bear Researcher)"],
  [/^### Research Manager(?: Decision)?\s*$/m, "### 研究经理 (Research Manager)"],
  [/^### Trader\s*$/m, "### 交易员 (Trader)"],
  [/^### Aggressive Analyst(?: Analysis)?\s*$/m, "### 激进分析师 (Aggressive Analyst)"],
  [/^### Conservative Analyst(?: Analysis)?\s*$/m, "### 保守分析师 (Conservative Analyst)"],
  [/^### Neutral Analyst(?: Analysis)?\s*$/m, "### 中性分析师 (Neutral Analyst)"],
  [/^### Portfolio Manager(?: Decision)?\s*$/m, "### 组合经理 (Portfolio Manager)"],

  // Dialogue prefixes inside debate transcripts
  [/^Market Analyst:\s*/gm, "技术面分析师 (Market Analyst)："],
  [/^Sentiment Analyst:\s*/gm, "舆情分析师 (Sentiment Analyst)："],
  [/^News Analyst:\s*/gm, "资讯分析师 (News Analyst)："],
  [/^Fundamentals Analyst:\s*/gm, "基本面分析师 (Fundamentals Analyst)："],
  [/^Bull Researcher:\s*/gm, "多头研究员 (Bull Researcher)："],
  [/^Bear Researcher:\s*/gm, "空头研究员 (Bear Researcher)："],
  [/^Research Manager:\s*/gm, "研究经理 (Research Manager)："],
  [/^Trader:\s*/gm, "交易员 (Trader)："],
  [/^Aggressive Analyst:\s*/gm, "激进分析师 (Aggressive Analyst)："],
  [/^Conservative Analyst:\s*/gm, "保守分析师 (Conservative Analyst)："],
  [/^Neutral Analyst:\s*/gm, "中性分析师 (Neutral Analyst)："],
  [/^Portfolio Manager:\s*/gm, "组合经理 (Portfolio Manager)："],

  // Structural labels — keep BUY/HOLD/SELL English (industry convention + parsers)
  [/^FINAL TRANSACTION PROPOSAL:\s*/gm, "最终交易建议 (FINAL TRANSACTION PROPOSAL)："],
  [/\*\*Action\*\*\s*:/g, "**动作 (Action)**："],
  [/\*\*Reasoning\*\*\s*:/g, "**理由 (Reasoning)**："],
  [/\*\*Entry Price\*\*\s*:/g, "**参考入场 (Entry Price)**："],
  [/\*\*Stop Loss\*\*\s*:/g, "**止损 (Stop Loss)**："],
  [/\*\*Position Sizing\*\*\s*:/g, "**仓位 (Position Sizing)**："],
  [/\*\*Rating\*\*\s*:/gi, "**评级 (Rating)**："],
  [/\*\*Executive Summary\*\*\s*:/gi, "**执行摘要 (Executive Summary)**："],
  [/\*\*Investment Thesis\*\*\s*:/gi, "**投资论点 (Investment Thesis)**："],
];

export function localizeReportMarkdown(markdown: string): string {
  if (!markdown) return markdown;
  // Patterns only match English structural forms; bilingual text is left unchanged.
  let out = markdown;
  for (const [pattern, replacement] of REPLACEMENTS) {
    out = out.replace(pattern, replacement);
  }
  return out;
}
