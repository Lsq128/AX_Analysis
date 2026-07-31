"""AX Analysis FastAPI application."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ax_api.middleware.rate_limit import RateLimitMiddleware
from ax_api.routes import admin, analyses, auth, billing, llm, memory, presets, report_library, reports, tickers, users
from ax_db.session import init_db
from ax_engine.env import load_ax_env


@asynccontextmanager
async def lifespan(_app: FastAPI):
    load_ax_env()
    init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="AX Analysis API",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        # Next dev (3000) calls API (8000) directly for SSE; avoid allow_origins="*"
        # together with credentials (browsers reject that combination).
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RateLimitMiddleware)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(llm.router, prefix="/api/v1")
    app.include_router(billing.router, prefix="/api/v1")
    app.include_router(admin.router, prefix="/api/v1")
    app.include_router(memory.router, prefix="/api/v1")
    app.include_router(report_library.router, prefix="/api/v1")
    app.include_router(tickers.router, prefix="/api/v1")
    app.include_router(analyses.router, prefix="/api/v1")
    app.include_router(reports.router, prefix="/api/v1")
    app.include_router(presets.router, prefix="/api/v1")
    app.include_router(users.router, prefix="/api/v1")
    return app


app = create_app()


def main() -> None:
    import uvicorn

    uvicorn.run("ax_api.main:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    main()
