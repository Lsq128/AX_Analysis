"""JWT authentication for AX."""

from ax_auth.jwt_utils import create_access_token, decode_access_token, subject_from_token
from ax_auth.oauth import build_authorize_url, create_oauth_state, exchange_oauth_code, verify_oauth_state
from ax_auth.settings import (
    allow_header_fallback,
    auth_dev_mode,
    configured_oauth_providers,
    dev_login_enabled,
    oauth_enabled,
)

__all__ = [
    "allow_header_fallback",
    "auth_dev_mode",
    "build_authorize_url",
    "configured_oauth_providers",
    "create_access_token",
    "create_oauth_state",
    "decode_access_token",
    "dev_login_enabled",
    "exchange_oauth_code",
    "oauth_enabled",
    "subject_from_token",
    "verify_oauth_state",
]
