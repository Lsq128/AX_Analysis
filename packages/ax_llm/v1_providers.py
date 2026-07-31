"""v1 domestic LLM providers for AX SaaS."""

from __future__ import annotations

from dataclasses import dataclass

from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.llm_clients.model_catalog import get_model_options

V1_PROVIDER_IDS = ("deepseek", "qwen-cn", "kimi")


@dataclass(frozen=True)
class ProviderSpec:
    id: str
    label: str
    quota_factor: float
    description: str


PROVIDER_SPECS: dict[str, ProviderSpec] = {
    "deepseek": ProviderSpec(
        id="deepseek",
        label="DeepSeek",
        quota_factor=1.0,
        description="均衡档 · 性价比优先",
    ),
    "qwen-cn": ProviderSpec(
        id="qwen-cn",
        label="通义千问",
        quota_factor=1.2,
        description="均衡档 · 中文理解强",
    ),
    "kimi": ProviderSpec(
        id="kimi",
        label="Kimi",
        quota_factor=1.2,
        description="长上下文 · Moonshot",
    ),
}

# Kimi uses custom-only in upstream catalog; AX v1 defaults.
_KIMI_MODELS = {
    "quick": [
        ("Kimi K2 Turbo", "kimi-k2-turbo-preview"),
        ("Custom model ID", "custom"),
    ],
    "deep": [
        ("Kimi K2", "kimi-k2-0711-preview"),
        ("Custom model ID", "custom"),
    ],
}


def list_v1_providers() -> list[dict]:
    out = []
    for pid in V1_PROVIDER_IDS:
        spec = PROVIDER_SPECS[pid]
        models = get_provider_models(pid)
        out.append(
            {
                "id": spec.id,
                "label": spec.label,
                "quota_factor": spec.quota_factor,
                "description": spec.description,
                "models": models,
                "defaults": default_models(pid),
            }
        )
    return out


def get_provider_models(provider: str) -> dict[str, list[dict[str, str]]]:
    pid = provider.lower()
    if pid not in V1_PROVIDER_IDS:
        raise KeyError(f"Unsupported v1 provider: {provider!r}")
    if pid == "kimi":
        raw = _KIMI_MODELS
    else:
        raw = {
            "quick": get_model_options(pid, "quick"),
            "deep": get_model_options(pid, "deep"),
        }
    return {
        mode: [{"label": label, "id": model_id} for label, model_id in options]
        for mode, options in raw.items()
    }


def default_models(provider: str) -> dict[str, str]:
    pid = provider.lower()
    if pid == "deepseek":
        return {
            "quick": DEFAULT_CONFIG.get("quick_think_llm", "deepseek-v4-flash"),
            "deep": DEFAULT_CONFIG.get("deep_think_llm", "deepseek-v4-pro"),
        }
    models = get_provider_models(pid)
    return {
        "quick": _first_real_model(models["quick"]),
        "deep": _first_real_model(models["deep"]),
    }


def _first_real_model(options: list[dict[str, str]]) -> str:
    for opt in options:
        if opt["id"] != "custom":
            return opt["id"]
    return options[0]["id"] if options else "custom"


def resolve_llm_selection(
    provider: str | None,
    *,
    shallow_thinker: str | None = None,
    deep_thinker: str | None = None,
) -> dict[str, str]:
    """Return normalized llm_provider + model ids for engine selections."""
    pid = (provider or DEFAULT_CONFIG.get("llm_provider") or "deepseek").lower()
    if pid not in V1_PROVIDER_IDS:
        raise ValueError(f"llm_provider must be one of: {', '.join(V1_PROVIDER_IDS)}")

    defaults = default_models(pid)
    quick = (shallow_thinker or defaults["quick"]).strip()
    deep = (deep_thinker or defaults["deep"]).strip()
    if not quick or not deep:
        raise ValueError("shallow_thinker and deep_thinker are required")

    return {
        "llm_provider": pid,
        "shallow_thinker": quick,
        "deep_thinker": deep,
    }


def provider_quota_factor(provider: str | None) -> float:
    pid = (provider or "deepseek").lower()
    spec = PROVIDER_SPECS.get(pid)
    return spec.quota_factor if spec else 1.0
