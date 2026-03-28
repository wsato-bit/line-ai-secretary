"""Monitoring utilities: health checks, structured logging, error reporting."""
from __future__ import annotations

import logging
import json
import sys
import time
from typing import Any

import redis.asyncio as aioredis
from sqlalchemy import text
from fastapi import APIRouter

from src.config import config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["monitoring"])


# ---------------------------------------------------------------------------
# Structured Logging for Cloud Logging
# ---------------------------------------------------------------------------


class CloudLoggingFormatter(logging.Formatter):
    """JSON formatter compatible with Google Cloud Logging."""

    LEVEL_MAP = {
        logging.DEBUG: "DEBUG",
        logging.INFO: "INFO",
        logging.WARNING: "WARNING",
        logging.ERROR: "ERROR",
        logging.CRITICAL: "CRITICAL",
    }

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "severity": self.LEVEL_MAP.get(record.levelno, "DEFAULT"),
            "message": record.getMessage(),
            "logger": record.name,
            "timestamp": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S.%fZ"),
        }
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        return json.dumps(log_entry, ensure_ascii=False)


def setup_cloud_logging() -> None:
    """Configure root logger with structured JSON output for Cloud Run."""
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    # Remove existing handlers
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(CloudLoggingFormatter())
    root.addHandler(handler)

    logger.info("Cloud Logging structured formatter initialized")


# ---------------------------------------------------------------------------
# Health Check Helpers
# ---------------------------------------------------------------------------


async def _check_database() -> dict[str, Any]:
    """Check database connectivity."""
    from src.models.database import async_session_factory

    try:
        start = time.monotonic()
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        latency_ms = round((time.monotonic() - start) * 1000, 1)
        return {"status": "ok", "latency_ms": latency_ms}
    except Exception as e:
        logger.error("Database health check failed: %s", e)
        return {"status": "error", "error": str(e)}


async def _check_redis() -> dict[str, Any]:
    """Check Redis connectivity."""
    if not config.REDIS_URL:
        return {"status": "skip", "reason": "REDIS_URL not configured"}
    try:
        start = time.monotonic()
        client = aioredis.from_url(config.REDIS_URL, decode_responses=True)
        await client.ping()
        await client.aclose()
        latency_ms = round((time.monotonic() - start) * 1000, 1)
        return {"status": "ok", "latency_ms": latency_ms}
    except Exception as e:
        logger.error("Redis health check failed: %s", e)
        return {"status": "error", "error": str(e)}


async def _check_anthropic() -> dict[str, Any]:
    """Check Anthropic API key is configured (does not make an API call)."""
    if config.ANTHROPIC_API_KEY:
        return {"status": "ok"}
    return {"status": "error", "error": "ANTHROPIC_API_KEY not set"}


async def _check_line() -> dict[str, Any]:
    """Check LINE credentials are configured."""
    missing = []
    if not config.LINE_CHANNEL_SECRET:
        missing.append("LINE_CHANNEL_SECRET")
    if not config.LINE_CHANNEL_ACCESS_TOKEN:
        missing.append("LINE_CHANNEL_ACCESS_TOKEN")
    if missing:
        return {"status": "error", "missing": missing}
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Health Check Endpoints
# ---------------------------------------------------------------------------


@router.get("/health")
async def health_check_simple():
    """Lightweight health check for Cloud Run probes."""
    return {"status": "ok"}


@router.get("/health/detailed")
async def health_check_detailed():
    """Detailed health check with dependency status."""
    checks = {
        "database": await _check_database(),
        "redis": await _check_redis(),
        "anthropic": await _check_anthropic(),
        "line": await _check_line(),
    }

    all_ok = all(c.get("status") == "ok" for c in checks.values() if c.get("status") != "skip")
    overall = "ok" if all_ok else "degraded"

    return {
        "status": overall,
        "checks": checks,
    }


# ---------------------------------------------------------------------------
# Error Reporting
# ---------------------------------------------------------------------------


def report_error(error: Exception, context: dict[str, Any] | None = None) -> None:
    """Log an error with structured context for Cloud Error Reporting.

    Cloud Error Reporting automatically picks up properly formatted
    exception logs from Cloud Logging.
    """
    extra_ctx = context or {}
    logger.error(
        "Unhandled error: %s | context=%s",
        error,
        json.dumps(extra_ctx, ensure_ascii=False, default=str),
        exc_info=True,
    )
