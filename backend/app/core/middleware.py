"""Middleware: exception handlers, request timing, security."""

from __future__ import annotations

import logging
import time
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import PocketError

logger = logging.getLogger("pocket")

# Map error codes to HTTP status codes
_STATUS_MAP: dict[str, int] = {
    "NOT_FOUND": 404,
    "VALIDATION_ERROR": 422,
    "CONFLICT": 409,
    "CIRCULAR_DEPENDENCY": 422,
    "PROMPT_VALIDATION_ERROR": 422,
    "AI_SERVICE_ERROR": 502,
    "TOKEN_LIMIT_EXCEEDED": 422,
    "INTERNAL_ERROR": 500,
}


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers on the FastAPI app."""

    @app.exception_handler(PocketError)
    async def pocket_error_handler(_request: Request, exc: PocketError) -> JSONResponse:
        status_code = _STATUS_MAP.get(exc.error_code, 500)
        content: dict[str, Any] = {
            "detail": exc.message,
            "error_code": exc.error_code,
        }
        errors = getattr(exc, "errors", None)
        if errors:
            content["errors"] = errors
        checks = getattr(exc, "checks", None)
        if checks:
            content["checks"] = checks
        return JSONResponse(status_code=status_code, content=content)

    @app.exception_handler(Exception)
    async def unhandled_error_handler(_request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error: %s", exc)
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "error_code": "INTERNAL_ERROR",
            },
        )

    @app.middleware("http")
    async def timing_middleware(request: Request, call_next: Any) -> Any:
        start = time.monotonic()
        response = await call_next(request)
        duration_ms = int((time.monotonic() - start) * 1000)
        response.headers["X-Response-Time-Ms"] = str(duration_ms)
        if duration_ms > 200 and not request.url.path.startswith("/api/v1/ai"):
            logger.warning(
                "Slow response: %s %s took %dms",
                request.method,
                request.url.path,
                duration_ms,
            )
        return response
