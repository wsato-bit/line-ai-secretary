"""Default EventColorRule definitions.

Google Calendar color IDs:
  1=Lavender, 2=Sage, 3=Grape, 4=Flamingo, 5=Banana,
  6=Tangerine, 7=Peacock, 8=Graphite, 9=Blueberry, 10=Basil, 11=Tomato

Default mapping:
  business/confirmed  → 9 (Blueberry / blue)
  business/tentative  → 7 (Peacock / cyan)
  private/confirmed   → 10 (Basil / green)
  private/tentative   → 5 (Banana / yellow)
"""

import logging
import uuid

from sqlalchemy.orm import Session

from src.models.models import ConfirmationStatus, EventColorRule, EventType

logger = logging.getLogger(__name__)

DEFAULT_COLOR_RULES = [
    {
        "event_type": EventType.business,
        "confirmation_status": ConfirmationStatus.confirmed,
        "color_id": "9",
        "color_label": "Blueberry",
    },
    {
        "event_type": EventType.business,
        "confirmation_status": ConfirmationStatus.tentative,
        "color_id": "7",
        "color_label": "Peacock",
    },
    {
        "event_type": EventType.private,
        "confirmation_status": ConfirmationStatus.confirmed,
        "color_id": "10",
        "color_label": "Basil",
    },
    {
        "event_type": EventType.private,
        "confirmation_status": ConfirmationStatus.tentative,
        "color_id": "5",
        "color_label": "Banana",
    },
]


def ensure_default_color_rules(user_id: str, db: Session) -> list[EventColorRule]:
    """Create default EventColorRules for a user if none exist.

    Args:
        user_id: User UUID string.
        db: SQLAlchemy session.

    Returns:
        List of EventColorRule records (existing or newly created).
    """
    existing = (
        db.query(EventColorRule)
        .filter(EventColorRule.user_id == user_id)
        .all()
    )

    if existing:
        return existing

    rules = []
    for rule_data in DEFAULT_COLOR_RULES:
        rule = EventColorRule(
            id=uuid.uuid4(),
            user_id=user_id,
            event_type=rule_data["event_type"],
            confirmation_status=rule_data["confirmation_status"],
            color_id=rule_data["color_id"],
            color_label=rule_data["color_label"],
        )
        db.add(rule)
        rules.append(rule)

    db.commit()
    logger.info("Created default color rules for user %s", user_id)
    return rules


def get_color_for_event(
    user_id: str,
    db: Session,
    event_type: EventType = EventType.business,
    confirmation_status: ConfirmationStatus = ConfirmationStatus.confirmed,
) -> str:
    """Get the Google Calendar color ID for an event type/status combination.

    Args:
        user_id: User UUID string.
        db: SQLAlchemy session.
        event_type: Business or private.
        confirmation_status: Confirmed or tentative.

    Returns:
        Google Calendar color ID string (e.g. "9").
    """
    rule = (
        db.query(EventColorRule)
        .filter(
            EventColorRule.user_id == user_id,
            EventColorRule.event_type == event_type,
            EventColorRule.confirmation_status == confirmation_status,
        )
        .first()
    )

    if rule:
        return rule.color_id

    # Fallback to defaults
    for default in DEFAULT_COLOR_RULES:
        if (
            default["event_type"] == event_type
            and default["confirmation_status"] == confirmation_status
        ):
            return default["color_id"]

    return "1"  # Lavender as ultimate fallback
