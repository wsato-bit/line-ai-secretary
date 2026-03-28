"""Audit log middleware for LINE AI Secretary.

Logs all API operations to the AuditLog table.
"""

from __future__ import annotations

import logging
import time
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from src.models.database import SessionLocal
from src.models.models import AuditLog

logger = logging.getLogger(__name__)

# Paths to exclude from audit logging
EXCLUDED_PATHS = {"/api/health", "/docs", "/openapi.json", "/redoc", "/favicon.ico"}


class AuditLogMiddleware(BaseHTTPMiddleware):
    """Middleware that records each API request to the audit_logs table."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Skip excluded paths
        if request.url.path in EXCLUDED_PATHS:
            return await call_next(request)

        start_time = time.monotonic()
        response: Response | None = None
        error_msg: str | None = None

        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            error_msg = str(exc)
            raise
        finally:
            duration_ms = round((time.monotonic() - start_time) * 1000)
            status_code = response.status_code if response else 500
            self._record_audit_log(request, status_code, duration_ms, error_msg)

    def _record_audit_log(
        self,
        request: Request,
        status_code: int,
        duration_ms: int,
        error_msg: str | None,
    ) -> None:
        """Write audit log record to the database."""
        try:
            # Extract user_id from request state if set by auth middleware
            user_id: uuid.UUID | None = getattr(request.state, "user_id", None)

            # Build action string from method + path
            action = f"{request.method} {request.url.path}"

            # Extract resource info from path
            path_parts = request.url.path.strip("/").split("/")
            resource = path_parts[1] if len(path_parts) > 1 else None
            resource_id = _try_parse_uuid(path_parts[-1]) if len(path_parts) > 2 else None

            # Client info
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")

            metadata = {
                "status_code": status_code,
                "duration_ms": duration_ms,
                "query_params": dict(request.query_params),
            }
            if error_msg:
                metadata["error"] = error_msg

            db = SessionLocal()
            try:
                log_entry = AuditLog(
                    user_id=user_id,
                    action=action,
                    resource=resource,
                    resource_id=resource_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    metadata=metadata,
                )
                db.add(log_entry)
                db.commit()
            except Exception:
                db.rollback()
                logger.exception("Failed to write audit log")
            finally:
                db.close()
        except Exception:
            logger.exception("Audit middleware error (non-blocking)")


def _try_parse_uuid(value: str) -> uuid.UUID | None:
    """Try to parse a string as UUID, return None on failure."""
    try:
        return uuid.UUID(value)
    except (ValueError, AttributeError):
        return None
