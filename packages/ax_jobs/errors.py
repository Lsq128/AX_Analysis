"""User-facing job failure classification."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class JobErrorInfo:
    code: str
    message: str
    retryable: bool


_RULES: list[tuple[re.Pattern[str], JobErrorInfo]] = [
    (
        re.compile(r"insufficient quota|402|配额", re.I),
        JobErrorInfo("quota_exceeded", "配额不足，请升级套餐或等待下个周期。", False),
    ),
    (
        re.compile(r"429|rate.?limit|too many requests|throttl", re.I),
        JobErrorInfo("rate_limited", "模型 API 限流，请稍后重试。", True),
    ),
    (
        re.compile(r"timeout|timed out|deadline", re.I),
        JobErrorInfo("timeout", "分析超时，可能是网络或模型响应慢。", True),
    ),
    (
        re.compile(r"api.?key|authentication|unauthorized|401|403", re.I),
        JobErrorInfo("auth_error", "模型 API 密钥无效或未配置，请联系管理员。", False),
    ),
    (
        re.compile(r"invalid ticker|ticker symbol", re.I),
        JobErrorInfo("invalid_ticker", "标的代码无效，请检查后重新发起。", False),
    ),
    (
        re.compile(r"connection|network|dns|refused", re.I),
        JobErrorInfo("network_error", "网络连接失败，请稍后重试。", True),
    ),
    (
        re.compile(r"no data|unavailable|not found", re.I),
        JobErrorInfo("data_unavailable", "部分数据源暂时不可用，可稍后重试或换标的。", True),
    ),
]

_DEFAULT = JobErrorInfo("internal_error", "分析过程中出现错误，可尝试重试。", True)


def classify_job_error(error: str | None) -> JobErrorInfo:
    if not error or not error.strip():
        return JobErrorInfo("unknown", "未知错误。", True)
    text = error.strip()
    for pattern, info in _RULES:
        if pattern.search(text):
            return info
    return _DEFAULT
