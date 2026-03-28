"""FastAPI exception handlers for LINE AI Secretary."""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.utils.errors import AppError

logger = logging.getLogger(__name__)


def _error_response(status_code: int, message: str, detail: Any = None) -> JSONResponse:
    """Build a standard error response."""
    body: dict[str, Any] = {
        "error": True,
        "message": message,
    }
    if detail is not None:
        body["detail"] = detail
    return JSONResponse(status_code=status_code, content=body)


async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    """Handle custom AppError exceptions."""
    logger.warning("AppError: %s (status=%d)", exc.message, exc.status_code)
    return _error_response(exc.status_code, exc.message, exc.detail)


async def http_exception_handler(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle Starlette/FastAPI HTTP exceptions."""
    return _error_response(exc.status_code, str(exc.detail))


async def validation_exception_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic request validation errors."""
    errors = []
    for err in exc.errors():
        loc = " -> ".join(str(x) for x in err.get("loc", []))
        errors.append({"field": loc, "message": err.get("msg", "")})
    return _error_response(422, "Validation error", detail=errors)


async def unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler for unhandled exceptions."""
    logger.exception("Unhandled exception: %s", exc)
    return _error_response(500, "Internal server error")


def register_error_handlers(app: FastAPI) -> None:
    """Register all exception handlers on the FastAPI app."""
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
