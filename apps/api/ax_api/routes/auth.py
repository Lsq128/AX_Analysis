"""Authentication routes."""

from __future__ import annotations

from typing import Annotated
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from ax_api.deps import get_current_user
from ax_auth.jwt_utils import create_access_token
from ax_auth.oauth import (
    PROVIDER_LABELS,
    build_authorize_url,
    create_oauth_state,
    exchange_oauth_code,
    verify_oauth_state,
)
from ax_auth.settings import (
    allow_header_fallback,
    auth_dev_mode,
    configured_oauth_providers,
    dev_login_enabled,
    web_base_url,
)
from ax_db.repository import UserRepository
from ax_db.session import db_enabled, session_scope

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=128)
    display_name: str | None = Field(default=None, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    display_name: str


class OAuthProviderResponse(BaseModel):
    id: str
    label: str


class AuthConfigResponse(BaseModel):
    dev_mode: bool
    dev_login: bool
    header_fallback: bool
    oauth_providers: list[OAuthProviderResponse]


@router.get("/config", response_model=AuthConfigResponse)
def auth_config() -> AuthConfigResponse:
    providers = [
        OAuthProviderResponse(id=pid, label=PROVIDER_LABELS.get(pid, pid.upper()))
        for pid in configured_oauth_providers()
    ]
    return AuthConfigResponse(
        dev_mode=auth_dev_mode(),
        dev_login=dev_login_enabled(),
        header_fallback=allow_header_fallback(),
        oauth_providers=providers,
    )


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest) -> TokenResponse:
    """Issue a JWT for the given user id (dev only)."""
    if not dev_login_enabled():
        raise HTTPException(status_code=403, detail="Dev login is disabled in production mode")
    display_name = body.display_name or body.user_id
    if db_enabled():
        with session_scope() as session:
            UserRepository(session).get_or_create(body.user_id, display_name=display_name)
    token = create_access_token(subject=body.user_id, claims={"name": display_name})
    return TokenResponse(
        access_token=token,
        user_id=body.user_id,
        display_name=display_name,
    )


@router.get("/oauth/{provider}/start")
def oauth_start(provider: str) -> RedirectResponse:
    provider = provider.lower()
    if provider not in configured_oauth_providers():
        raise HTTPException(status_code=404, detail="OAuth provider not configured")
    state = create_oauth_state(provider)
    url = build_authorize_url(provider, state=state)
    return RedirectResponse(url, status_code=302)


@router.get("/oauth/{provider}/callback")
def oauth_callback(
    provider: str,
    code: Annotated[str | None, Query()] = None,
    state: Annotated[str | None, Query()] = None,
    error: Annotated[str | None, Query()] = None,
) -> RedirectResponse:
    provider = provider.lower()
    if error:
        params = urlencode({"error": error})
        return RedirectResponse(f"{web_base_url()}/login/callback?{params}", status_code=302)
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing OAuth code or state")

    verify_oauth_state(state, provider)
    profile = exchange_oauth_code(provider, code)
    external_id = profile["external_id"]
    display_name = profile["display_name"]

    if db_enabled():
        with session_scope() as session:
            UserRepository(session).get_or_create(external_id, display_name=display_name)

    token = create_access_token(
        subject=external_id,
        claims={
            "name": display_name,
            "provider": profile.get("provider"),
            "email": profile.get("email"),
        },
    )
    params = urlencode(
        {
            "access_token": token,
            "user_id": external_id,
            "display_name": display_name,
        }
    )
    return RedirectResponse(f"{web_base_url()}/login/callback?{params}", status_code=302)


@router.get("/session", response_model=TokenResponse)
def session(user: Annotated[dict, Depends(get_current_user)]) -> TokenResponse:
    token = create_access_token(
        subject=user["external_id"],
        claims={"name": user.get("display_name", user["external_id"])},
    )
    return TokenResponse(
        access_token=token,
        user_id=user["external_id"],
        display_name=user.get("display_name") or user["external_id"],
    )
