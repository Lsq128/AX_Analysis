import type { AnalysisJob } from "./types";

export function jobErrorMessage(job: AnalysisJob): string {
  return job.error_message || job.error || "分析失败，请稍后重试。";
}

export function jobIsRetryable(job: AnalysisJob): boolean {
  return job.retryable !== false && job.status === "failed";
}
