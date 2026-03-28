"""Email filter CRUD service.

Manages user-defined email filters for classifying and
excluding emails from summaries.
"""

import logging
import re
import uuid

from sqlalchemy.orm import Session

from src.models.models import EmailFilter, EmailFilterAction, EmailFilterType
from src.utils.errors import ConflictError, NotFoundError

logger = logging.getLogger(__name__)


def get_filters(user_id: str, db: Session) -> list[dict]:
    """Get all email filters for a user.

    Args:
        user_id: User UUID string.
        db: SQLAlchemy session.

    Returns:
        List of filter dicts.
    """
    filters = (
        db.query(EmailFilter)
        .filter(EmailFilter.user_id == user_id)
        .order_by(EmailFilter.created_at.desc())
        .all()
    )
    return [_filter_to_dict(f) for f in filters]


def set_email_filter(
    user_id: str,
    db: Session,
    filter_type: str,
    filter_value: str,
    action: str,
) -> dict:
    """Create or update an email filter.

    Args:
        user_id: User UUID string.
        db: SQLAlchemy session.
        filter_type: "sender", "domain", or "subject_pattern".
        filter_value: The filter value (email, domain, or regex pattern).
        action: "important" or "exclude".

    Returns:
        Created/updated filter dict.

    Raises:
        ConflictError: If an identical filter already exists.
    """
    ft = EmailFilterType(filter_type)
    fa = EmailFilterAction(action)

    existing = (
        db.query(EmailFilter)
        .filter(
            EmailFilter.user_id == user_id,
            EmailFilter.filter_type == ft,
            EmailFilter.filter_value == filter_value,
        )
        .first()
    )

    if existing:
        if existing.action == fa:
            raise ConflictError("同一のフィルターが既に存在します")
        # Update action if filter exists with different action
        existing.action = fa
        db.commit()
        db.refresh(existing)
        logger.info("Updated email filter %s for user %s", existing.id, user_id)
        return _filter_to_dict(existing)

    new_filter = EmailFilter(
        id=uuid.uuid4(),
        user_id=user_id,
        filter_type=ft,
        filter_value=filter_value,
        action=fa,
    )
    db.add(new_filter)
    db.commit()
    db.refresh(new_filter)

    logger.info("Created email filter %s for user %s", new_filter.id, user_id)
    return _filter_to_dict(new_filter)


def delete_filter(user_id: str, db: Session, filter_id: str) -> bool:
    """Delete an email filter.

    Args:
        user_id: User UUID string.
        db: SQLAlchemy session.
        filter_id: EmailFilter UUID string.

    Returns:
        True if deleted successfully.

    Raises:
        NotFoundError: If filter not found.
    """
    email_filter = (
        db.query(EmailFilter)
        .filter(
            EmailFilter.id == filter_id,
            EmailFilter.user_id == user_id,
        )
        .first()
    )

    if not email_filter:
        raise NotFoundError(resource="EmailFilter", resource_id=filter_id)

    db.delete(email_filter)
    db.commit()

    logger.info("Deleted email filter %s for user %s", filter_id, user_id)
    return True


def apply_filters(user_id: str, db: Session, emails: list[dict]) -> list[dict]:
    """Apply user-defined filters to categorize emails.

    Filters override auto-classification. Applied in order:
    1. Exclude filters remove emails from results
    2. Important filters mark emails as important

    Args:
        user_id: User UUID string.
        db: SQLAlchemy session.
        emails: List of email dicts with 'from', 'subject', 'category' fields.

    Returns:
        Filtered and re-categorized email list.
    """
    filters = (
        db.query(EmailFilter)
        .filter(EmailFilter.user_id == user_id)
        .all()
    )

    if not filters:
        return emails

    exclude_matchers = []
    important_matchers = []

    for f in filters:
        matcher = _build_matcher(f.filter_type, f.filter_value)
        if f.action == EmailFilterAction.exclude:
            exclude_matchers.append(matcher)
        elif f.action == EmailFilterAction.important:
            important_matchers.append(matcher)

    result = []
    for email in emails:
        # Check exclude filters
        if _matches_any(email, exclude_matchers):
            email["category"] = "excluded"
            continue

        # Check important filters
        if _matches_any(email, important_matchers):
            email["category"] = "important"

        result.append(email)

    return result


# ─── Private helpers ───────────────────────────────────────────


def _filter_to_dict(f: EmailFilter) -> dict:
    """Convert EmailFilter model to dict."""
    return {
        "id": str(f.id),
        "filter_type": f.filter_type.value,
        "filter_value": f.filter_value,
        "action": f.action.value,
        "created_at": f.created_at.isoformat() if f.created_at else None,
    }


def _build_matcher(filter_type: EmailFilterType, filter_value: str):
    """Build a matcher function for a filter type/value.

    Returns:
        A callable(email_dict) -> bool.
    """
    if filter_type == EmailFilterType.sender:
        lower_val = filter_value.lower()
        return lambda email: lower_val in email.get("from", "").lower()

    if filter_type == EmailFilterType.domain:
        lower_val = f"@{filter_value.lower().lstrip('@')}"
        return lambda email: lower_val in email.get("from", "").lower()

    if filter_type == EmailFilterType.subject_pattern:
        try:
            pattern = re.compile(filter_value, re.IGNORECASE)
            return lambda email: bool(pattern.search(email.get("subject", "")))
        except re.error:
            logger.warning("Invalid regex pattern in filter: %s", filter_value)
            return lambda email: filter_value.lower() in email.get("subject", "").lower()

    return lambda email: False


def _matches_any(email: dict, matchers: list) -> bool:
    """Check if an email matches any of the given matchers."""
    return any(matcher(email) for matcher in matchers)
