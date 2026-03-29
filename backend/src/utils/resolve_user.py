"""Resolve LINE user ID to internal UUID."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from src.models.models import User


def resolve_user_id(user_id_or_line_id: str, db: Session) -> str:
    """Accept either UUID or LINE user ID, return the internal UUID string.

    Args:
        user_id_or_line_id: Either a UUID string or LINE user ID (e.g. "U5a91b...")
        db: SQLAlchemy database session

    Returns:
        Internal UUID as a string.

    Raises:
        ValueError: If the user is not found.
    """
    # Try UUID format first
    try:
        uuid.UUID(user_id_or_line_id)
        return user_id_or_line_id
    except ValueError:
        pass

    # Look up by LINE user ID
    user = db.query(User).filter(User.line_user_id == user_id_or_line_id).first()
    if user:
        return str(user.id)

    raise ValueError(f"User not found: {user_id_or_line_id}")
