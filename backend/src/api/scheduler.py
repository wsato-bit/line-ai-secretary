"""Scheduler API endpoints - triggered by Cloud Scheduler."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Header, HTTPException

from src.config import config
from src.services.jobs.morning_summary import run_morning_summaries
from src.services.jobs.event_reminder import run_event_reminders
from src.services.jobs.unreplied_reminder import run_unreplied_reminders

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/jobs", tags=["Scheduler"])


def _verify_job_auth(authorization: str | None) -> None:
    """Verify Cloud Scheduler / internal job authentication.

    Accepts either:
    - Bearer token matching JOB_AUTH_SECRET
    - Google Cloud Tasks service account (via OIDC token validation)

    Args:
        authorization: Authorization header value.

    Raises:
        HTTPException: If authentication fails.
    """
    if not config.JOB_AUTH_SECRET:
        logger.warning("JOB_AUTH_SECRET not configured, skipping job auth check")
        return

    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    expected = f"Bearer {config.JOB_AUTH_SECRET}"
    if authorization != expected:
        raise HTTPException(status_code=403, detail="Invalid job authorization")


@router.post("/morning-summary")
async def trigger_morning_summary(
    authorization: str | None = Header(None),
):
    """Triggered by Cloud Scheduler during morning hours (every 5 min, 06:00-09:59).

    Sends morning summary to users whose configured time matches the current window.
    """
    _verify_job_auth(authorization)

    logger.info("Morning summary job triggered")
    result = await run_morning_summaries()
    return {"status": "ok", **result}


@router.post("/event-reminders")
async def trigger_event_reminders(
    authorization: str | None = Header(None),
):
    """Triggered by Cloud Scheduler every 5 minutes.

    Checks all users' upcoming events against their reminder intervals.
    """
    _verify_job_auth(authorization)

    logger.info("Event reminder job triggered")
    result = await run_event_reminders()
    return {"status": "ok", **result}


@router.post("/unreplied-reminders")
async def trigger_unreplied_reminders(
    authorization: str | None = Header(None),
):
    """Triggered by Cloud Scheduler daily (e.g. 09:00 JST).

    Checks all users with enabled unreplied reminder for overdue items.
    """
    _verify_job_auth(authorization)

    logger.info("Unreplied reminder job triggered")
    result = await run_unreplied_reminders()
    return {"status": "ok", **result}
