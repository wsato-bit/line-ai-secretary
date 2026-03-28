"""LINE unreplied item management service."""

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from src.models.models import UnrepliedItem

logger = logging.getLogger(__name__)


def register_unreplied(
    user_id: uuid.UUID,
    contact_name: str,
    content_memo: str | None,
    db: Session,
) -> UnrepliedItem:
    """Register a new unreplied item.

    Args:
        user_id: Owner user ID.
        contact_name: Name of the contact to reply to.
        content_memo: Optional note about the message content.
        db: Database session.

    Returns:
        Created UnrepliedItem object.
    """
    item = UnrepliedItem(
        user_id=user_id,
        contact_name=contact_name,
        content_memo=content_memo,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    logger.info(
        "Unreplied item registered: id=%s, contact=%s, user=%s",
        item.id, contact_name, user_id,
    )
    return item


def list_unreplied(
    user_id: uuid.UUID,
    db: Session,
    include_completed: bool = False,
) -> list[dict]:
    """List unreplied items with days_elapsed calculation.

    Args:
        user_id: Owner user ID.
        db: Database session.
        include_completed: Whether to include completed items.

    Returns:
        List of dicts with item data and days_elapsed.
    """
    q = db.query(UnrepliedItem).filter(UnrepliedItem.user_id == user_id)

    if not include_completed:
        q = q.filter(UnrepliedItem.is_completed.is_(False))

    items = q.order_by(UnrepliedItem.registered_at.desc()).all()
    now = datetime.now(timezone.utc)

    result = []
    for item in items:
        registered = item.registered_at
        if registered.tzinfo is None:
            registered = registered.replace(tzinfo=timezone.utc)
        days_elapsed = (now - registered).days

        result.append({
            "id": str(item.id),
            "contact_name": item.contact_name,
            "content_memo": item.content_memo,
            "registered_at": item.registered_at.isoformat(),
            "completed_at": item.completed_at.isoformat() if item.completed_at else None,
            "is_completed": item.is_completed,
            "days_elapsed": days_elapsed,
        })

    return result


def complete_unreplied(
    user_id: uuid.UUID,
    item_id: uuid.UUID,
    db: Session,
) -> UnrepliedItem | None:
    """Mark an unreplied item as completed.

    Args:
        user_id: Owner user ID.
        item_id: Item ID to complete.
        db: Database session.

    Returns:
        Updated UnrepliedItem or None if not found.
    """
    item = (
        db.query(UnrepliedItem)
        .filter(
            UnrepliedItem.id == item_id,
            UnrepliedItem.user_id == user_id,
        )
        .first()
    )
    if not item:
        return None

    item.is_completed = True
    item.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(item)

    logger.info("Unreplied item completed: id=%s, user=%s", item_id, user_id)
    return item


def get_overdue_unreplied(
    user_id: uuid.UUID,
    threshold_days: int,
    db: Session,
) -> list[dict]:
    """Get unreplied items that exceed the threshold days.

    Args:
        user_id: Owner user ID.
        threshold_days: Number of days after which an item is considered overdue.
        db: Database session.

    Returns:
        List of overdue item dicts with days_elapsed.
    """
    all_items = list_unreplied(user_id, db, include_completed=False)
    return [item for item in all_items if item["days_elapsed"] >= threshold_days]
