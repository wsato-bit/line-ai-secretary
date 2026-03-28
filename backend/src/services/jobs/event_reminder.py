"""Event reminder job - sends reminders before upcoming calendar events."""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from src.models.database import SessionLocal
from src.models.models import NotificationSetting, User, UserStatus
from src.services import calendar_service
from src.services.line_service import line_service

logger = logging.getLogger(__name__)

JST = timezone(timedelta(hours=9))


def check_upcoming_events(
    user_id: str,
    db: Session,
    reminder_intervals: list[int],
) -> list[tuple[dict, int]]:
    """Check for upcoming events that match reminder intervals.

    Args:
        user_id: User UUID string.
        db: Database session.
        reminder_intervals: List of minutes-before-event to trigger reminders
                           (e.g. [30, 10]).

    Returns:
        List of (event_dict, minutes_until) tuples for events needing reminders.
    """
    now_jst = datetime.now(JST)
    today_str = now_jst.strftime("%Y-%m-%d")

    try:
        events = calendar_service.get_schedule(
            user_id=user_id,
            db=db,
            date_from=today_str,
            date_to=today_str,
        )
    except Exception:
        logger.warning(
            "Could not fetch calendar for reminder check, user %s",
            user_id, exc_info=True,
        )
        return []

    reminders = []
    for event in events:
        start_str = event.get("start", "")
        if not start_str or len(start_str) <= 10:
            continue  # Skip all-day events

        try:
            event_start = datetime.fromisoformat(
                start_str.replace("Z", "+00:00")
            )
        except ValueError:
            continue

        diff_minutes = (event_start - now_jst).total_seconds() / 60

        for interval in reminder_intervals:
            # Match within a 5-minute window (job runs every 5 min)
            if interval - 2.5 <= diff_minutes < interval + 2.5:
                reminders.append((event, round(diff_minutes)))
                break  # Only one reminder per event per run

    return reminders


async def send_event_reminder(
    line_user_id: str,
    event: dict,
    minutes_until: int,
) -> None:
    """Send a reminder push message for an upcoming event.

    Args:
        line_user_id: LINE user ID for push message.
        event: Event dict from calendar_service.
        minutes_until: Minutes until event starts.
    """
    title = event.get("summary", "無題の予定")
    start_display = event.get("start_display", "")
    location = event.get("location", "")

    lines = [f"⏰ {minutes_until}分後に予定があります"]
    lines.append(f"📌 {title}")
    if start_display:
        lines.append(f"🕐 {start_display}")
    if location:
        lines.append(f"📍 {location}")

    text = "\n".join(lines)

    try:
        await line_service.push_text(line_user_id, text)
        logger.info(
            "Event reminder sent: %s, %d min before, to %s",
            title, minutes_until, line_user_id,
        )
    except Exception:
        logger.error(
            "Failed to send event reminder to %s",
            line_user_id, exc_info=True,
        )
        raise


async def run_event_reminders() -> dict:
    """Check all users' upcoming events against their reminder intervals.

    Called by Cloud Scheduler every 5 minutes.

    Returns:
        Dict with sent_count and error_count.
    """
    db = SessionLocal()
    sent_count = 0
    error_count = 0

    try:
        settings = (
            db.query(NotificationSetting)
            .filter(NotificationSetting.reminder_intervals.isnot(None))
            .all()
        )

        for setting in settings:
            intervals = setting.reminder_intervals
            if not intervals:
                continue

            user = (
                db.query(User)
                .filter(
                    User.id == setting.user_id,
                    User.status == UserStatus.approved,
                )
                .first()
            )
            if not user:
                continue

            upcoming = check_upcoming_events(
                user_id=str(user.id),
                db=db,
                reminder_intervals=intervals,
            )

            for event, minutes_until in upcoming:
                try:
                    await send_event_reminder(
                        user.line_user_id, event, minutes_until,
                    )
                    sent_count += 1
                except Exception:
                    error_count += 1
    finally:
        db.close()

    logger.info(
        "Event reminder job complete: sent=%d, errors=%d",
        sent_count, error_count,
    )
    return {"sent_count": sent_count, "error_count": error_count}
