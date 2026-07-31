export function extractRating(text: string): string {
  if (!text) return "";
  const m =
    text.match(/\*\*Rating\*\*:\s*([A-Za-z\u4e00-\u9fff]+)/i) ||
    text.match(/Rating:\s*([A-Za-z\u4e00-\u9fff]+)/i) ||
    text.match(/评级[：:]\s*([A-Za-z\u4e00-\u9fff]+)/);
  const raw = (m?.[1] || "").replace(/[★☆⭐✨🌟]/g, "").trim();
  return raw;
}

export const RATING_LABELS_ZH: Record<string, string> = {
  Buy: "买入",
  Overweight: "增持",
  Hold: "持有",
  Underweight: "减持",
  Sell: "卖出",
};

export function ratingLabel(rating: string): string {
  if (!rating) return "";
  const normalized = rating.charAt(0).toUpperCase() + rating.slice(1).toLowerCase();
  return RATING_LABELS_ZH[normalized] || RATING_LABELS_ZH[rating] || rating;
}

export function ratingColor(rating: string): string {
  const r = rating.toLowerCase();
  if (r.includes("buy") || r.includes("买入")) return "var(--success)";
  if (r.includes("overweight") || r.includes("增持")) return "#34d399";
  if (r.includes("underweight") || r.includes("减持")) return "var(--warning)";
  if (r.includes("sell") || r.includes("卖出")) return "var(--danger)";
  return "var(--muted)";
}

export function ratingBadgeClass(rating: string): string {
  const r = rating.toLowerCase();
  if (r.includes("buy") || r.includes("买入")) return "border-[var(--success)]/40 bg-[var(--success)]/10 text-[var(--success)]";
  if (r.includes("overweight") || r.includes("增持")) return "border-[var(--success)]/30 bg-[var(--success)]/5 text-[var(--success)]";
  if (r.includes("underweight") || r.includes("减持")) return "border-[var(--warning)]/40 bg-[var(--warning)]/10 text-[var(--warning)]";
  if (r.includes("sell") || r.includes("卖出")) return "border-[var(--danger)]/40 bg-[var(--danger)]/10 text-[var(--danger)]";
  return "border-[var(--border)] bg-[var(--surface-2)] text-[var(--muted)]";
}
