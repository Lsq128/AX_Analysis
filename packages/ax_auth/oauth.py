"""OAuth2 helpers for production authentication."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode

import httpx
import jwt
from fastapi import HTTPException

from ax_auth.jwt_utils import jwt_secret
from ax_auth.settings import (
    github_oauth_config,
    oauth_redirect_uri,
    oidc_oauth_config,
)

OAUTH_STATE_TTL_MINUTES = 10

PROVIDER_LABELS = {
    "github": "GitHub",
    "oidc": "OIDC",
}


def create_oauth_state(provider: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "oauth-state",
        "typ": "oauth_state",
        "provider": provider,
        "iat": now,
        "exp": now + timedelta(minutes=OAUTH_STATE_TTL_MINUTES),
    }
    return jwt.encode(payload, jwt_secret(), algorithm="HS256")


def verify_oauth_state(state: str, provider: str) -> None:
    try:
        payload = jwt.decode(state, jwt_secret(), algorithms=["HS256"])
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=400, detail="Invalid OAuth state") from exc
    if payload.get("typ") != "oauth_state" or payload.get("provider") != provider:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")


def build_authorize_url(provider: str, *, state: str) -> str:
    redirect_uri = oauth_redirect_uri(provider)
    if provider == "github":
        cfg = github_oauth_config()
        if not cfg:
            raise HTTPException(status_code=503, detail="GitHub OAuth is not configured")
        params = urlencode(
            {
                "client_id": cfg["client_id"],
                "redirect_uri": redirect_uri,
                "scope": "read:user user:email",
                "state": state,
            }
        )
        return f"https://github.com/login/oauth/authorize?{params}"

    if provider == "oidc":
        cfg = oidc_oauth_config()
        if not cfg:
            raise HTTPException(status_code=503, detail="OIDC OAuth is not configured")
        params = urlencode(
            {
                "client_id": cfg["client_id"],
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "scope": cfg["scope"],
                "state": state,
            }
        )
        return f"{cfg['authorize_url']}?{params}"

    raise HTTPException(status_code=404, detail=f"Unknown OAuth provider: {provider}")


def _exchange_github_code(code: str) -> dict[str, Any]:
    cfg = github_oauth_config()
    if not cfg:
        raise HTTPException(status_code=503, detail="GitHub OAuth is not configured")
    redirect_uri = oauth_redirect_uri("github")
    with httpx.Client(timeout=20.0) as client:
        token_resp = client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            json={
                "client_id": cfg["client_id"],
                "client_secret": cfg["client_secret"],
                "code": code,
                "redirect_uri": redirect_uri,
            },
        )
        token_resp.raise_for_status()
        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="GitHub token exchange failed")

        user_resp = client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            },
        )
        user_resp.raise_for_status()
        profile = user_resp.json()

    user_id = profile.get("id")
    if user_id is None:
        raise HTTPException(status_code=400, detail="GitHub profile missing id")

    login = profile.get("login") or str(user_id)
    display_name = profile.get("name") or login
    return {
        "external_id": f"github:{user_id}",
        "display_name": display_name,
        "email": profile.get("email"),
        "avatar_url": profile.get("avatar_url"),
        "provider": "github",
        "provider_subject": str(user_id),
        "provider_login": login,
    }


def _exchange_oidc_code(code: str) -> dict[str, Any]:
    cfg = oidc_oauth_config()
    if not cfg:
        raise HTTPException(status_code=503, detail="OIDC OAuth is not configured")
    redirect_uri = oauth_redirect_uri("oidc")
    with httpx.Client(timeout=20.0) as client:
        token_resp = client.post(
            cfg["token_url"],
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": cfg["client_id"],
                "client_secret": cfg["client_secret"],
            },
            headers={"Accept": "application/json"},
        )
        token_resp.raise_for_status()
        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="OIDC token exchange failed")

        user_resp = client.get(
            cfg["userinfo_url"],
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
        )
        user_resp.raise_for_status()
        profile = user_resp.json()

    subject = profile.get("sub")
    if not subject:
        raise HTTPException(status_code=400, detail="OIDC profile missing sub")

    display_name = (
        profile.get("name")
        or profile.get("preferred_username")
        or profile.get("email")
        or str(subject)
    )
    return {
        "external_id": f"oidc:{subject}",
        "display_name": display_name,
        "email": profile.get("email"),
        "avatar_url": profile.get("picture"),
        "provider": "oidc",
        "provider_subject": str(subject),
        "provider_login": profile.get("preferred_username"),
    }


def exchange_oauth_code(provider: str, code: str) -> dict[str, Any]:
    if provider == "github":
        return _exchange_github_code(code)
    if provider == "oidc":
        return _exchange_oidc_code(code)
    raise HTTPException(status_code=404, detail=f"Unknown OAuth provider: {provider}")
