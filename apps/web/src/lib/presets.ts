/** Fallback Chinese labels when API preset list is unavailable. */
export const PRESET_LABELS_ZH: Record<string, string> = {
  quick: "快速诊股",
  technical: "技术趋势",
  news_sentiment: "资讯舆情",
  value: "价值深挖",
  full: "全面研判",
  deep: "深度推演",
  crypto: "数字资产快览",
  custom: "自定义",
};

export const ANALYST_LABELS_ZH: Record<string, string> = {
  market: "技术面",
  social: "舆情",
  news: "新闻",
  fundamentals: "基本面",
};

export function presetLabelZh(
  presetId?: string | null,
  fromApi?: string | null,
): string {
  if (fromApi) return fromApi;
  if (!presetId) return "分析";
  return PRESET_LABELS_ZH[presetId] || presetId;
}

export function analystLabelsZh(analysts: string[]): string {
  return analysts.map((a) => ANALYST_LABELS_ZH[a] || a).join(" · ");
}
