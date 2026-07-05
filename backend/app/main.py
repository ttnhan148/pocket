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

    # ── Serve Frontend Static Files ──────────────────────────────────
    import os
    from fastapi.responses import FileResponse

    static_dir = os.path.join(os.path.dirname(__file__), "static")

    @app.get("/{rest_of_path:path}")
    async def serve_frontend(rest_of_path: str):
        if (
            rest_of_path.startswith("api/")
            or rest_of_path.startswith("docs")
            or rest_of_path.startswith("redoc")
            or rest_of_path.startswith("openapi.json")
        ):
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Not Found")

        if not os.path.exists(static_dir):
            return {"message": "Pocket Single-Deploy: Static frontend directory not found. Please build frontend first."}

        # Check if requested path is a real file inside static_dir
        file_path = os.path.join(static_dir, rest_of_path)
        if rest_of_path and os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)

        # Fallback to index.html for client-side routing
        index_path = os.path.join(static_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"message": "Pocket Single-Deploy: index.html not found inside static directory."}

    return app


def _register_routers(app: FastAPI) -> None:
    """Register all API routers."""
    from app.features.context.router import router as context_router
    from app.features.dependency.router import router as dependency_router
    from app.features.health.router import router as health_router
    from app.features.tags_categories.router import router as tags_categories_router
    from app.features.workspace.router import router as workspace_router
    from app.features.favorite.router import router as favorite_router
    from app.features.settings.router import router as settings_router
    from app.features.provider.router import router as provider_router
    from app.features.variables.router import router as variables_router
    from app.features.templates.router import router as templates_router
    from app.features.search.router import router as search_router
    from app.features.conversation.router import router as conversation_router
    from app.features.prompt.router import router as prompt_router
    from app.features.auto.router import router as auto_router
    from app.features.analytics.router import router as analytics_router
    from app.features.jobs.router import router as jobs_router
    from app.features.journals.router import router as journals_router

    app.include_router(health_router, prefix="/api/v1", tags=["Health"])
    app.include_router(workspace_router, prefix="/api/v1/workspaces", tags=["Workspaces"])
    app.include_router(context_router, prefix="/api/v1/workspaces/{workspace_id}/contexts", tags=["Contexts"])
    app.include_router(dependency_router, prefix="/api/v1/workspaces/{workspace_id}", tags=["Dependencies"])
    app.include_router(tags_categories_router, prefix="/api/v1/workspaces/{workspace_id}", tags=["Tags & Categories"])
    app.include_router(favorite_router, prefix="/api/v1/workspaces/{workspace_id}/favorites", tags=["Favorites"])
    app.include_router(settings_router, prefix="/api/v1/settings", tags=["Settings"])
    app.include_router(provider_router, prefix="/api/v1/providers", tags=["Providers"])
    app.include_router(variables_router, prefix="/api/v1/variables", tags=["Variables"])
    app.include_router(templates_router, prefix="/api/v1/templates", tags=["Templates"])
    app.include_router(search_router, prefix="/api/v1/search", tags=["Search"])
    app.include_router(conversation_router, prefix="/api/v1/conversations", tags=["Conversations"])
    app.include_router(prompt_router, prefix="/api/v1/prompts", tags=["Prompts"])
    app.include_router(auto_router, prefix="/api/v1/auto", tags=["Auto AI"])
    app.include_router(analytics_router, prefix="/api/v1/analytics", tags=["Analytics"])
    app.include_router(jobs_router, prefix="/api/v1/jobs", tags=["AI Background Jobs"])
    app.include_router(journals_router, prefix="/api/v1/journals", tags=["Conversation Journals"])


# Default app instance for uvicorn
app = create_app()
