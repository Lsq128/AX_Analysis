/** Extract structured highlights from report markdown sections. */

export type ReportSummary = {
  executiveSummary: string;
  researchRating: string;
  researchView: string;
  traderAction: string;
  traderEntry: string;
  traderStop: string;
  traderPosition: string;
};

export function buildReportSummary(
  decisionMd: string,
  traderMd: string,
  managerMd: string,
): ReportSummary {
  const source = decisionMd || managerMd;
  return {
    executiveSummary: pickField(source, ["executive summary", "执行摘要", "summary"]) || firstParagraph(source),
    researchRating: pickField(managerMd || source, ["rating", "评级"]),
    researchView: pickField(managerMd || source, ["investment thesis", "理由", "rationale"]) || firstParagraph(managerMd),
    traderAction: pickField(traderMd, ["action", "动作", "recommendation"]),
    traderEntry: pickField(traderMd, ["entry", "入场", "target price", "参考入场"]),
    traderStop: pickField(traderMd, ["stop", "止损"]),
    traderPosition: pickField(traderMd, ["position", "仓位", "size"]),
  };
}

function pickField(text: string, labels: string[]): string {
  if (!text) return "";
  for (const label of labels) {
    const re = new RegExp(`(?:\\*\\*)?${escapeRe(label)}(?:\\*\\*)?\\s*[:：-]\\s*(.+)$`, "im");
    const m = text.match(re);
    if (m?.[1]) return m[1].trim().replace(/\*\*/g, "");
  }
  return "";
}

function firstParagraph(text: string): string {
  if (!text) return "";
  const line = text
    .split("\n")
    .map((l) => l.trim())
    .find((l) => l && !l.startsWith("#"));
  return line?.replace(/\*\*/g, "") || "";
}

function escapeRe(value: string) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
