"""Memo category management service."""

from __future__ import annotations

import logging
import uuid

from sqlalchemy.orm import Session

from src.models.models import MemoCategory

logger = logging.getLogger(__name__)

DEFAULT_CATEGORIES = [
    {"name": "未分類", "sort_order": 0, "is_default": True},
    {"name": "ビジネス", "sort_order": 1, "is_default": False},
    {"name": "アイデア", "sort_order": 2, "is_default": False},
    {"name": "買い物", "sort_order": 3, "is_default": False},
    {"name": "その他", "sort_order": 4, "is_default": False},
]


def list_categories(user_id: uuid.UUID, db: Session) -> list[MemoCategory]:
    """List all memo categories for a user, ordered by sort_order.

    Creates default categories if none exist.

    Args:
        user_id: Owner user ID.
        db: Database session.

    Returns:
        List of MemoCategory objects.
    """
    ensure_default_categories(user_id, db)
    return db.query(MemoCategory).filter(MemoCategory.user_id == user_id).order_by(MemoCategory.sort_order).all()


def create_category(user_id: uuid.UUID, name: str, db: Session) -> MemoCategory:
    """Create a new memo category.

    Args:
        user_id: Owner user ID.
        name: Category name.
        db: Database session.

    Returns:
        Created MemoCategory object.

    Raises:
        ValueError: If a category with the same name already exists.
    """
    existing = db.query(MemoCategory).filter(MemoCategory.user_id == user_id, MemoCategory.name == name).first()
    if existing:
        raise ValueError(f"Category '{name}' already exists")

    # Get max sort_order
    max_order = (
        db.query(MemoCategory.sort_order)
        .filter(MemoCategory.user_id == user_id)
        .order_by(MemoCategory.sort_order.desc())
        .first()
    )
    next_order = (max_order[0] + 1) if max_order else 0

    category = MemoCategory(
        user_id=user_id,
        name=name,
        sort_order=next_order,
        is_default=False,
    )
    db.add(category)
    db.commit()
    db.refresh(category)

    logger.info("Category created: %s for user %s", name, user_id)
    return category


def update_category(
    user_id: uuid.UUID,
    category_id: uuid.UUID,
    name: str,
    db: Session,
) -> MemoCategory | None:
    """Update a memo category name.

    Args:
        user_id: Owner user ID.
        category_id: Category ID to update.
        name: New category name.
        db: Database session.

    Returns:
        Updated MemoCategory or None if not found.

    Raises:
        ValueError: If a category with the new name already exists.
    """
    category = db.query(MemoCategory).filter(MemoCategory.id == category_id, MemoCategory.user_id == user_id).first()
    if not category:
        return None

    # Check duplicate name
    duplicate = (
        db.query(MemoCategory)
        .filter(
            MemoCategory.user_id == user_id,
            MemoCategory.name == name,
            MemoCategory.id != category_id,
        )
        .first()
    )
    if duplicate:
        raise ValueError(f"Category '{name}' already exists")

    category.name = name
    db.commit()
    db.refresh(category)

    logger.info("Category updated: %s -> %s", category_id, name)
    return category


def delete_category(
    user_id: uuid.UUID,
    category_id: uuid.UUID,
    db: Session,
) -> bool:
    """Delete a memo category.

    Default categories cannot be deleted.

    Args:
        user_id: Owner user ID.
        category_id: Category ID to delete.
        db: Database session.

    Returns:
        True if deleted, False if not found or is default.
    """
    category = db.query(MemoCategory).filter(MemoCategory.id == category_id, MemoCategory.user_id == user_id).first()
    if not category:
        return False

    if category.is_default:
        logger.warning("Cannot delete default category: %s", category_id)
        return False

    db.delete(category)
    db.commit()

    logger.info("Category deleted: %s", category_id)
    return True


def reorder_categories(
    user_id: uuid.UUID,
    category_ids: list[uuid.UUID],
    db: Session,
) -> list[MemoCategory]:
    """Reorder categories by setting sort_order based on the given ID list.

    Args:
        user_id: Owner user ID.
        category_ids: Ordered list of category IDs.
        db: Database session.

    Returns:
        Updated list of MemoCategory objects in new order.
    """
    categories = db.query(MemoCategory).filter(MemoCategory.user_id == user_id).all()
    category_map = {cat.id: cat for cat in categories}

    for order, cat_id in enumerate(category_ids):
        if cat_id in category_map:
            category_map[cat_id].sort_order = order

    db.commit()

    logger.info("Categories reordered for user %s", user_id)
    return db.query(MemoCategory).filter(MemoCategory.user_id == user_id).order_by(MemoCategory.sort_order).all()


def ensure_default_categories(user_id: uuid.UUID, db: Session) -> None:
    """Create default categories for a user if they don't exist.

    Args:
        user_id: Owner user ID.
        db: Database session.
    """
    existing = db.query(MemoCategory).filter(MemoCategory.user_id == user_id).count()
    if existing > 0:
        return

    for cat_data in DEFAULT_CATEGORIES:
        category = MemoCategory(
            user_id=user_id,
            name=cat_data["name"],
            sort_order=cat_data["sort_order"],
            is_default=cat_data["is_default"],
        )
        db.add(category)

    db.commit()
    logger.info("Default memo categories created for user %s", user_id)
