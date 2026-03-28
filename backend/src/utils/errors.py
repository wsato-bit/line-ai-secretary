"""Custom exception classes for LINE AI Secretary."""

from __future__ import annotations


class AppError(Exception):
    """Base application error."""

    def __init__(self, message: str, status_code: int = 500, detail: str | None = None):
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(message)


class NotFoundError(AppError):
    """Resource not found."""

    def __init__(self, resource: str, resource_id: str | None = None):
        msg = f"{resource} not found"
        if resource_id:
            msg = f"{resource} with id '{resource_id}' not found"
        super().__init__(message=msg, status_code=404)


class UnauthorizedError(AppError):
    """Authentication required or failed."""

    def __init__(self, message: str = "Authentication required"):
        super().__init__(message=message, status_code=401)


class ForbiddenError(AppError):
    """Insufficient permissions."""

    def __init__(self, message: str = "Permission denied"):
        super().__init__(message=message, status_code=403)


class ValidationError(AppError):
    """Request validation failed."""

    def __init__(self, message: str, detail: str | None = None):
        super().__init__(message=message, status_code=422, detail=detail)


class ConflictError(AppError):
    """Resource conflict (e.g. duplicate)."""

    def __init__(self, message: str = "Resource already exists"):
        super().__init__(message=message, status_code=409)


class RateLimitError(AppError):
    """Too many requests."""

    def __init__(self, message: str = "Too many requests. Please try again later."):
        super().__init__(message=message, status_code=429)


class ExternalServiceError(AppError):
    """Error from an external service (LINE, Google, etc.)."""

    def __init__(self, service: str, message: str | None = None):
        msg = f"External service error: {service}"
        if message:
            msg = f"{msg} - {message}"
        super().__init__(message=msg, status_code=502)
