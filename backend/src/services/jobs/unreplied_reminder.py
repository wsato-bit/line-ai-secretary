"""Unreplied reminder job - sends reminders for overdue unreplied items."""

import logging
from datetime import timedelta, timezone

from sqlalchemy.orm import Session

from src.models.database import SessionLocal
from src.models.models import NotificationSetting, User, UserStatus
from src.services import unreplied_service
from src.services.line_service import line_service
from src.services.line_templates import unreplied_list_template

logger = logging.getLogger(__name__)

JST = timezone(timedelta(hours=9))


def check_overdue_unreplied(
    user_id: str,
    threshold_days: int,
    db: Session,
) -> list[dict]:
    """Check for overdue unreplied items exceeding threshold.

    Args:
        user_id: User UUID string.
        threshold_days: Number of days threshold.
        db: Database session.

    Returns:
        List of overdue item dicts.
    """
    import uuid

    return unreplied_service.get_overdue_unreplied(
        user_id=uuid.UUID(user_id),
        threshold_days=threshold_days,
        db=db,
    )


async def send_unreplied_reminder(
    line_user_id: str,
    items: list[dict],
    threshold_days: int,
) -> None:
    """Send a reminder push message for overdue unreplied items.

    Args:
        line_user_id: LINE user ID for push message.
        items: List of overdue unreplied item dicts.
        threshold_days: Threshold days configured by user.
    """
    if not items:
        return

    # Text message
    lines = [f"⚠️ {threshold_days}日以上未返信の項目が{len(items)}件あります"]
    for item in items[:5]:
        days = item["days_elapsed"]
        lines.append(f"  ・{item['contact_name']} ({days}日経過)")
    if len(items) > 5:
        lines.append(f"  ...他 {len(items) - 5}件")
    lines.append("\n「未返信リスト」と送信すると一覧を確認できます。")

    text = "\n".join(lines)

    try:
        await line_service.push_text(line_user_id, text)

        # Also send Flex message for rich display
        flex_items = [
            {
                "type": "message",
                "from": item["contact_name"],
                "subject": item.get("content_memo") or "メモなし",
                "received_at": f"{item['days_elapsed']}日前",
            }
            for item in items[:10]
        ]
        flex = line_service.create_flex_message(
            f"未返信 {len(items)}件",
            unreplied_list_template(flex_items),
        )
        await line_service.push_message(line_user_id, [flex])

        logger.info(
            "Unreplied reminder sent: %d items to %s",
            len(items), line_user_id,
        )
    except Exception:
        logger.error(
            "Failed to send unreplied reminder to %s",
            line_user_id, exc_info=True,
        )
        raise


async def run_unreplied_reminders() -> dict:
    """Check all users with enabled unreplied reminder for overdue items.

    Called by Cloud Scheduler daily.

    Returns:
        Dict with sent_count and error_count.
    """
    db = SessionLocal()
    sent_count = 0
    error_count = 0

    try:
        settings = (
            db.query(NotificationSetting)
            .filter(NotificationSetting.unreplied_reminder_enabled.is_(True))
            .all()
        )

        for setting in settings:
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

            overdue_items = check_overdue_unreplied(
                user_id=str(user.id),
                threshold_days=setting.unreplied_threshold_days,
                db=db,
            )

            if not overdue_items:
                continue

            try:
                await send_unreplied_reminder(
                    user.line_user_id,
                    overdue_items,
                    setting.unreplied_threshold_days,
                )
                sent_count += 1
            except Exception:
                error_count += 1
    finally:
        db.close()

    logger.info(
        "Unreplied reminder job complete: sent=%d, errors=%d",
        sent_count, error_count,
    )
    return {"sent_count": sent_count, "error_count": error_count}
