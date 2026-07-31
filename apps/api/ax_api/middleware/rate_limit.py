"""Simple request rate limiting for API."""

from __future__ import annotations

import os
import time
from collections import defaultdict, deque

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send


def _rpm() -> int:
    return int(os.getenv("AX_API_RATE_LIMIT_RPM", "120"))


class RateLimitMiddleware:
    """Per-IP sliding window limiter; stricter on analysis creation.

    Pure ASGI (not BaseHTTPMiddleware) so StreamingResponse / SSE is not buffered.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path") or ""
        if not path.startswith("/api/v1"):
            await self.app(scope, receive, send)
            return

        # Never rate-limit or wrap SSE streams.
        if path.endswith("/events"):
            await self.app(scope, receive, send)
            return

        client = "unknown"
        if scope.get("client"):
            client = scope["client"][0]
        method = scope.get("method") or "GET"
        key = f"{client}:{self._bucket(method, path)}"
        limit = self._limit(method, path)
        now = time.monotonic()
        window = 60.0
        q = self._hits[key]
        while q and now - q[0] > window:
            q.popleft()
        if len(q) >= limit:
            response = JSONResponse(
                status_code=429,
                content={"detail": "请求过于频繁，请稍后再试。"},
            )
            await response(scope, receive, send)
            return
        q.append(now)
        await self.app(scope, receive, send)

    @staticmethod
    def _bucket(method: str, path: str) -> str:
        if method == "POST" and path.rstrip("/") == "/api/v1/analyses":
            return "analyses_create"
        return "default"

    @staticmethod
    def _limit(method: str, path: str) -> int:
        if method == "POST" and path.rstrip("/") == "/api/v1/analyses":
            return max(5, _rpm() // 6)
        return _rpm()
