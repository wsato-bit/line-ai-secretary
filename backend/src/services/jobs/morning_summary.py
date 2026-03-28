"""Morning summary job - sends daily schedule/email/unreplied overview via LINE."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from src.models.database import SessionLocal
from src.models.models import NotificationSetting, User, UserStatus
from src.services import calendar_service, unreplied_service
from src.services.line_service import line_service
from src.services.line_templates import schedule_summary_template

logger = logging.getLogger(__name__)

JST = timezone(timedelta(hours=9))


def generate_morning_summary(user_id: str, db: Session) -> str | None:
    """Generate a morning summary for a single user.

    Fetches today's schedule, unreplied overdue items, and formats them.

    Args:
        user_id: User UUID string (internal ID).
        db: Database session.

    Returns:
        Formatted summary text, or None if nothing to report.
    """
    import uuid

    user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
    if not user:
        logger.warning("User not found for morning summary: %s", user_id)
        return None

    now_jst = datetime.now(JST)
    today_str = now_jst.strftime("%Y-%m-%d")

    # Fetch today's schedule
    events = []
    try:
        events = calendar_service.get_schedule(
            user_id=user_id,
            db=db,
            date_from=today_str,
            date_to=today_str,
        )
    except Exception:
        logger.warning("Could not fetch calendar for user %s", user_id, exc_info=True)

    # Fetch overdue unreplied items
    setting = db.query(NotificationSetting).filter(NotificationSetting.user_id == user.id).first()
    threshold = setting.unreplied_threshold_days if setting else 3
    overdue_items = unreplied_service.get_overdue_unreplied(
        user_id=user.id,
        threshold_days=threshold,
        db=db,
    )

    if not events and not overdue_items:
        return None

    # Build summary text
    lines = [f"おはようございます。{now_jst.strftime('%m月%d日')}のサマリーです。"]

    if events:
        lines.append(f"\n📅 本日の予定: {len(events)}件")
        for ev in events[:5]:
            start = ev.get("start_display", "")
            end = ev.get("end_display", "")
            title = ev.get("summary", "無題")
            lines.append(f"  {start}-{end} {title}")
        if len(events) > 5:
            lines.append(f"  ...他 {len(events) - 5}件")
    else:
        lines.append("\n📅 本日の予定はありません。")

    if overdue_items:
        lines.append(f"\n⚠️ 未返信({threshold}日超): {len(overdue_items)}件")
        for item in overdue_items[:3]:
            lines.append(f"  {item['contact_name']} ({item['days_elapsed']}日経過)")
        if len(overdue_items) > 3:
            lines.append(f"  ...他 {len(overdue_items) - 3}件")

    return "\n".join(lines)


async def send_morning_summary(user: User, db: Session) -> bool:
    """Generate and send morning summary to a single user via LINE Push.

    Args:
        user: User ORM object.
        db: Database session.

    Returns:
        True if sent, False if skipped or failed.
    """
    summary_text = generate_morning_summary(str(user.id), db)
    if not summary_text:
        logger.debug("No morning summary content for user %s", user.id)
        return False

    try:
        # Send text summary
        await line_service.push_text(user.line_user_id, summary_text)

        # Also send Flex schedule card if there are events
        now_jst = datetime.now(JST)
        today_str = now_jst.strftime("%Y-%m-%d")
        try:
            events = calendar_service.get_schedule(
                user_id=str(user.id),
                db=db,
                date_from=today_str,
                date_to=today_str,
            )
            if events:
                line_events = calendar_service.format_events_for_line(events)
                flex = line_service.create_flex_message(
                    "本日の予定",
                    schedule_summary_template(line_events),
                )
                await line_service.push_message(user.line_user_id, [flex])
        except Exception:
            logger.debug("Skipped Flex schedule card for user %s", user.id, exc_info=True)

        logger.info("Morning summary sent to user %s", user.id)
        return True
    except Exception:
        logger.error("Failed to send morning summary to user %s", user.id, exc_info=True)
        return False


async def run_morning_summaries() -> dict:
    """Iterate all users whose morning summary time matches now (within 5min window).

    Called by Cloud Scheduler every 5 minutes during morning hours.

    Returns:
        Dict with sent_count and error_count.
    """
    db = SessionLocal()
    sent_count = 0
    error_count = 0

    try:
        now_jst = datetime.now(JST)

        # Find users with morning summary enabled
        settings = db.query(NotificationSetting).filter(NotificationSetting.morning_summary_enabled.is_(True)).all()

        for setting in settings:
            # Check if current time is within 5-minute window of configured time
            configured = setting.morning_summary_time
            configured_dt = datetime.combine(now_jst.date(), configured, tzinfo=JST)
            diff_minutes = (now_jst - configured_dt).total_seconds() / 60

            if not (0 <= diff_minutes < 5):
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

            try:
                sent = await send_morning_summary(user, db)
                if sent:
                    sent_count += 1
            except Exception:
                logger.error(
                    "Error sending morning summary for user %s",
                    setting.user_id,
                    exc_info=True,
                )
                error_count += 1
    finally:
        db.close()

    logger.info(
        "Morning summary job complete: sent=%d, errors=%d",
        sent_count,
        error_count,
    )
    return {"sent_count": sent_count, "error_count": error_count}
