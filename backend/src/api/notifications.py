"""Notification settings API endpoints."""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.models.database import get_db
from src.services import notification_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


# ─── Schemas ───────────────────────────────────────────────────


class NotificationSettingsResponse(BaseModel):
    morning_summary_time: str
    morning_summary_enabled: bool
    reminder_intervals: list[int]
    unreplied_threshold_days: int
    unreplied_reminder_enabled: bool


class UpdateNotificationSettingsRequest(BaseModel):
    morning_summary_time: str | None = None
    morning_summary_enabled: bool | None = None
    reminder_intervals: list[int] | None = None
    unreplied_threshold_days: int | None = None
    unreplied_reminder_enabled: bool | None = None


# ─── Helpers ───────────────────────────────────────────────────


def _get_user_id(user_id: str = Query(..., alias="user_id")) -> uuid.UUID:
    """Extract user_id from query parameter.

    TODO: Replace with proper auth dependency that extracts user from JWT/session.
    """
    try:
        return uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format")


def _setting_to_response(setting) -> dict:
    """Convert NotificationSetting ORM object to response dict."""
    return {
        "morning_summary_time": setting.morning_summary_time.strftime("%H:%M"),
        "morning_summary_enabled": setting.morning_summary_enabled,
        "reminder_intervals": setting.reminder_intervals or [],
        "unreplied_threshold_days": setting.unreplied_threshold_days,
        "unreplied_reminder_enabled": setting.unreplied_reminder_enabled,
    }


# ─── Endpoints ─────────────────────────────────────────────────


@router.get("/settings", response_model=NotificationSettingsResponse)
def get_settings(
    user_id: uuid.UUID = Depends(_get_user_id),
    db: Session = Depends(get_db),
):
    """Get notification settings for a user. Creates defaults if not exist."""
    setting = notification_service.get_notification_settings(user_id, db)
    return _setting_to_response(setting)


@router.put("/settings", response_model=NotificationSettingsResponse)
def update_settings(
    body: UpdateNotificationSettingsRequest,
    user_id: uuid.UUID = Depends(_get_user_id),
    db: Session = Depends(get_db),
):
    """Update notification settings for a user."""
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    setting = notification_service.update_notification_settings(user_id, updates, db)
    return _setting_to_response(setting)
