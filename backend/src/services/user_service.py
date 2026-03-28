"""User management service for admin operations."""

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from src.models.models import Memo, User, UserRole, UserStatus
from src.services.line_service import line_service

logger = logging.getLogger(__name__)


def list_pending_applications(db: Session) -> list[User]:
    """Return all users with pending status, ordered by applied_at."""
    return (
        db.query(User)
        .filter(User.status == UserStatus.pending)
        .order_by(User.applied_at.asc().nullsfirst())
        .all()
    )


def list_users(
    db: Session,
    status_filter: str | None = None,
    search: str | None = None,
) -> list[User]:
    """Return users with optional status filter and search."""
    query = db.query(User)

    if status_filter:
        try:
            status_enum = UserStatus(status_filter)
            query = query.filter(User.status == status_enum)
        except ValueError:
            pass  # Ignore invalid status filter

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                User.line_display_name.ilike(search_pattern),
                User.line_user_id.ilike(search_pattern),
            )
        )

    return query.order_by(User.created_at.desc()).all()


def get_user_detail(user_id: uuid.UUID, db: Session) -> dict | None:
    """Return user with statistics (memo count, last active, etc.)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None

    memo_count = (
        db.query(func.count(Memo.id))
        .filter(Memo.user_id == user_id, Memo.is_deleted.is_(False))
        .scalar()
    ) or 0

    return {
        "user": user,
        "memo_count": memo_count,
    }


async def approve_user(
    admin_user_id: uuid.UUID,
    target_user_id: uuid.UUID,
    db: Session,
) -> User:
    """Approve a pending user application."""
    user = db.query(User).filter(User.id == target_user_id).first()
    if not user:
        raise ValueError("User not found")

    if user.status != UserStatus.pending:
        raise ValueError(f"Cannot approve user with status: {user.status.value}")

    user.status = UserStatus.approved
    user.role = UserRole.user
    user.approved_at = datetime.now(timezone.utc)
    user.approved_by = admin_user_id
    user.rejection_reason = None
    db.commit()
    db.refresh(user)

    # Send LINE push notification
    await _notify_user_status_change(user, "approved")

    logger.info("User %s approved by admin %s", target_user_id, admin_user_id)
    return user


async def reject_user(
    admin_user_id: uuid.UUID,
    target_user_id: uuid.UUID,
    reason: str | None,
    db: Session,
) -> User:
    """Reject a pending user application."""
    user = db.query(User).filter(User.id == target_user_id).first()
    if not user:
        raise ValueError("User not found")

    if user.status != UserStatus.pending:
        raise ValueError(f"Cannot reject user with status: {user.status.value}")

    user.status = UserStatus.rejected
    user.rejection_reason = reason
    db.commit()
    db.refresh(user)

    # Send LINE push notification
    await _notify_user_status_change(user, "rejected", reason)

    logger.info("User %s rejected by admin %s", target_user_id, admin_user_id)
    return user


async def disable_user(
    admin_user_id: uuid.UUID,
    target_user_id: uuid.UUID,
    db: Session,
) -> User:
    """Disable an approved/active user."""
    user = db.query(User).filter(User.id == target_user_id).first()
    if not user:
        raise ValueError("User not found")

    if user.status == UserStatus.disabled:
        raise ValueError("User is already disabled")

    user.status = UserStatus.disabled
    db.commit()
    db.refresh(user)

    # Send LINE push notification
    await _notify_user_status_change(user, "disabled")

    logger.info("User %s disabled by admin %s", target_user_id, admin_user_id)
    return user


async def enable_user(
    admin_user_id: uuid.UUID,
    target_user_id: uuid.UUID,
    db: Session,
) -> User:
    """Re-enable a disabled user."""
    user = db.query(User).filter(User.id == target_user_id).first()
    if not user:
        raise ValueError("User not found")

    if user.status != UserStatus.disabled:
        raise ValueError(f"Cannot enable user with status: {user.status.value}")

    user.status = UserStatus.approved
    user.role = UserRole.user
    db.commit()
    db.refresh(user)

    # Send LINE push notification
    await _notify_user_status_change(user, "enabled")

    logger.info("User %s re-enabled by admin %s", target_user_id, admin_user_id)
    return user


async def _notify_user_status_change(
    user: User,
    action: str,
    reason: str | None = None,
) -> None:
    """Send LINE push notification to user about their status change."""
    messages = {
        "approved": "LINE AI Secretaryへようこそ！\nアカウントが承認されました。サービスをご利用いただけます。",
        "rejected": "LINE AI Secretaryからのお知らせ\nアカウント申請が承認されませんでした。",
        "disabled": "LINE AI Secretaryからのお知らせ\nアカウントが一時停止されました。",
        "enabled": "LINE AI Secretaryからのお知らせ\nアカウントが再有効化されました。サービスをご利用いただけます。",
    }

    text = messages.get(action, "アカウントステータスが変更されました。")
    if action == "rejected" and reason:
        text += f"\n理由: {reason}"

    try:
        await line_service.push_text(user.line_user_id, text)
    except Exception:
        logger.exception("Failed to send status change notification to user %s", user.id)
