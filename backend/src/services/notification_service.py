"""Notification settings management service."""

import logging
import uuid
from datetime import time

from sqlalchemy.orm import Session

from src.models.models import NotificationSetting

logger = logging.getLogger(__name__)

# Default values
DEFAULT_MORNING_SUMMARY_TIME = time(7, 0)
DEFAULT_REMINDER_INTERVALS = [30, 10]
DEFAULT_UNREPLIED_THRESHOLD_DAYS = 3


def get_notification_settings(
    user_id: uuid.UUID,
    db: Session,
) -> NotificationSetting:
    """Get notification settings for a user, creating defaults if not exist.

    Args:
        user_id: Owner user ID.
        db: Database session.

    Returns:
        NotificationSetting object.
    """
    setting = (
        db.query(NotificationSetting)
        .filter(NotificationSetting.user_id == user_id)
        .first()
    )

    if setting is None:
        setting = NotificationSetting(
            user_id=user_id,
            morning_summary_time=DEFAULT_MORNING_SUMMARY_TIME,
            morning_summary_enabled=True,
            reminder_intervals=DEFAULT_REMINDER_INTERVALS,
            unreplied_threshold_days=DEFAULT_UNREPLIED_THRESHOLD_DAYS,
            unreplied_reminder_enabled=True,
        )
        db.add(setting)
        db.commit()
        db.refresh(setting)
        logger.info("Created default notification settings for user %s", user_id)

    return setting


def update_notification_settings(
    user_id: uuid.UUID,
    updates: dict,
    db: Session,
) -> NotificationSetting:
    """Update notification settings for a user.

    Args:
        user_id: Owner user ID.
        updates: Dict of fields to update. Supported keys:
            - morning_summary_time (str "HH:MM")
            - morning_summary_enabled (bool)
            - reminder_intervals (list[int])
            - unreplied_threshold_days (int)
            - unreplied_reminder_enabled (bool)
        db: Database session.

    Returns:
        Updated NotificationSetting object.
    """
    setting = get_notification_settings(user_id, db)

    if "morning_summary_time" in updates:
        raw = updates["morning_summary_time"]
        if isinstance(raw, str):
            parts = raw.split(":")
            setting.morning_summary_time = time(int(parts[0]), int(parts[1]))
        elif isinstance(raw, time):
            setting.morning_summary_time = raw

    if "morning_summary_enabled" in updates:
        setting.morning_summary_enabled = bool(updates["morning_summary_enabled"])

    if "reminder_intervals" in updates:
        intervals = updates["reminder_intervals"]
        if isinstance(intervals, list) and all(isinstance(i, int) for i in intervals):
            setting.reminder_intervals = sorted(intervals, reverse=True)

    if "unreplied_threshold_days" in updates:
        val = int(updates["unreplied_threshold_days"])
        if val >= 1:
            setting.unreplied_threshold_days = val

    if "unreplied_reminder_enabled" in updates:
        setting.unreplied_reminder_enabled = bool(updates["unreplied_reminder_enabled"])

    db.commit()
    db.refresh(setting)
    logger.info("Updated notification settings for user %s", user_id)
    return setting
