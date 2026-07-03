"""FastAPI application factory."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings
from app.core.database import init_db
from app.core.logging import setup_logging
from app.core.middleware import register_exception_handlers


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    if settings is None:
        settings = Settings()

    setup_logging(settings)

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        """Application lifecycle: startup and shutdown."""
        await init_db(settings)
        yield

    app = FastAPI(
        title="Pocket API",
        description="Personal Context Engineering Platform",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # ── CORS ─────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Exception handlers ───────────────────────────────────────────
    register_exception_handlers(app)

    # ── Store settings in app state ──────────────────────────────────
    app.state.settings = settings

    # ── Register routers ─────────────────────────────────────────────
    _register_routers(app)

    return app


def _register_routers(app: FastAPI) -> None:
    """Register all API routers."""
    from app.features.context.router import router as context_router  # noqa: PLC0415
    from app.features.health.router import router as health_router  # noqa: PLC0415
    from app.features.workspace.router import router as workspace_router  # noqa: PLC0415

    app.include_router(health_router, prefix="/api/v1", tags=["Health"])
    app.include_router(workspace_router, prefix="/api/v1/workspaces", tags=["Workspaces"])
    app.include_router(context_router, prefix="/api/v1/workspaces/{workspace_id}/contexts", tags=["Contexts"])


# Default app instance for uvicorn
app = create_app()
