"""Auth mode and OAuth configuration."""

from __future__ import annotations

import os


def _bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def auth_dev_mode() -> bool:
    return _bool("AX_AUTH_DEV_MODE", default=True)


def allow_header_fallback() -> bool:
    return _bool("AX_AUTH_ALLOW_HEADER", default=True)


def dev_login_enabled() -> bool:
    return auth_dev_mode() and _bool("AX_AUTH_DEV_LOGIN", default=True)


def oauth_providers() -> list[str]:
    raw = os.getenv("AX_OAUTH_PROVIDERS", "")
    return [p.strip().lower() for p in raw.split(",") if p.strip()]


def oauth_enabled() -> bool:
    return bool(oauth_providers())


def web_base_url() -> str:
    return os.getenv("AX_WEB_URL", "http://localhost:3000").rstrip("/")


def oauth_redirect_uri(provider: str) -> str:
    explicit = os.getenv("AX_OAUTH_REDIRECT_URI", "").strip()
    if explicit:
        return explicit
    return f"{web_base_url()}/api/v1/auth/oauth/{provider}/callback"


def github_oauth_config() -> dict[str, str] | None:
    if "github" not in oauth_providers():
        return None
    client_id = os.getenv("OAUTH_GITHUB_CLIENT_ID", "").strip()
    client_secret = os.getenv("OAUTH_GITHUB_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        return None
    return {"client_id": client_id, "client_secret": client_secret}


def oidc_oauth_config() -> dict[str, str] | None:
    if "oidc" not in oauth_providers():
        return None
    client_id = os.getenv("OAUTH_OIDC_CLIENT_ID", "").strip()
    client_secret = os.getenv("OAUTH_OIDC_CLIENT_SECRET", "").strip()
    authorize_url = os.getenv("OAUTH_OIDC_AUTHORIZE_URL", "").strip()
    token_url = os.getenv("OAUTH_OIDC_TOKEN_URL", "").strip()
    userinfo_url = os.getenv("OAUTH_OIDC_USERINFO_URL", "").strip()
    if not all([client_id, client_secret, authorize_url, token_url, userinfo_url]):
        return None
    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "authorize_url": authorize_url,
        "token_url": token_url,
        "userinfo_url": userinfo_url,
        "scope": os.getenv("OAUTH_OIDC_SCOPE", "openid profile email").strip(),
    }


def configured_oauth_providers() -> list[str]:
    out: list[str] = []
    if github_oauth_config():
        out.append("github")
    if oidc_oauth_config():
        out.append("oidc")
    return out
