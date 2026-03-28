"""Memo management service."""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import or_
from sqlalchemy.orm import Session

from src.models.models import ContentType, Memo, MemoCategory
from src.services.storage_service import upload_image, delete_image
from src.services.ocr_service import extract_text
from src.services.url_service import fetch_url_metadata

logger = logging.getLogger(__name__)


async def save_memo(
    user_id: uuid.UUID,
    content: str,
    content_type: str,
    db: Session,
    file_data: bytes | None = None,
    filename: str | None = None,
) -> Memo:
    """Save a new memo.

    Handles three content types:
    - text: save directly, category/tags will be classified by AI (placeholder).
    - image: upload to GCS, run OCR, save with ocr_text.
    - url: fetch metadata, save with url_title/url_summary/url_thumbnail.

    Args:
        user_id: Owner user ID.
        content: Text content, or URL string for url type.
        content_type: One of "text", "image", "url".
        db: Database session.
        file_data: Raw image bytes (required for image type).
        filename: Original filename (required for image type).

    Returns:
        Created Memo object.
    """
    ct = ContentType(content_type)

    # Ensure user has default categories
    _ensure_default_categories(user_id, db)

    # Get default category (未分類)
    default_category = (
        db.query(MemoCategory).filter(MemoCategory.user_id == user_id, MemoCategory.is_default.is_(True)).first()
    )

    memo = Memo(
        user_id=user_id,
        content=content,
        content_type=ct,
        category_id=default_category.id if default_category else None,
        tags=[],
    )

    if ct == ContentType.image:
        if file_data and filename:
            image_url = upload_image(str(user_id), file_data, filename)
            memo.image_url = image_url
            memo.content = content or filename

            # Run OCR on uploaded image
            ocr_text = extract_text(image_url)
            memo.image_ocr_text = ocr_text
        else:
            logger.warning("Image memo created without file data")

    elif ct == ContentType.url:
        url = content.strip()
        memo.url = url
        metadata = await fetch_url_metadata(url)
        memo.url_title = metadata.title
        memo.url_summary = metadata.description
        memo.url_thumbnail = metadata.thumbnail
        memo.content = metadata.title or url

    # TODO: AI auto-classify category + tags (placeholder)
    # classification = await ai_classify_memo(memo.content)
    # memo.category_id = classification.category_id
    # memo.tags = classification.tags

    db.add(memo)
    db.commit()
    db.refresh(memo)

    logger.info("Memo saved: id=%s, type=%s, user=%s", memo.id, content_type, user_id)
    return memo


def search_memo(
    user_id: uuid.UUID,
    db: Session,
    query: str | None = None,
    category_id: uuid.UUID | None = None,
    tags: list[str] | None = None,
) -> list[Memo]:
    """Search memos with full-text search and filters.

    Args:
        user_id: Owner user ID.
        db: Database session.
        query: Search query (searches content, ocr_text, url_title, url_summary).
        category_id: Filter by category.
        tags: Filter by tags (any match).

    Returns:
        List of matching Memo objects, newest first.
    """
    q = db.query(Memo).filter(Memo.user_id == user_id, Memo.is_deleted.is_(False))

    if query:
        search_term = f"%{query}%"
        q = q.filter(
            or_(
                Memo.content.ilike(search_term),
                Memo.image_ocr_text.ilike(search_term),
                Memo.url_title.ilike(search_term),
                Memo.url_summary.ilike(search_term),
            )
        )

    if category_id:
        q = q.filter(Memo.category_id == category_id)

    if tags:
        # Filter memos that have any of the specified tags
        q = q.filter(Memo.tags.overlap(tags))

    return q.order_by(Memo.created_at.desc()).all()


def get_memo(user_id: uuid.UUID, memo_id: uuid.UUID, db: Session) -> Memo | None:
    """Get a single memo by ID.

    Args:
        user_id: Owner user ID.
        memo_id: Memo ID to retrieve.
        db: Database session.

    Returns:
        Memo object or None if not found.
    """
    return (
        db.query(Memo)
        .filter(
            Memo.id == memo_id,
            Memo.user_id == user_id,
            Memo.is_deleted.is_(False),
        )
        .first()
    )


def delete_memo(user_id: uuid.UUID, memo_id: uuid.UUID, db: Session) -> bool:
    """Soft-delete a memo.

    Args:
        user_id: Owner user ID.
        memo_id: Memo ID to delete.
        db: Database session.

    Returns:
        True if memo was found and deleted, False otherwise.
    """
    memo = get_memo(user_id, memo_id, db)
    if not memo:
        return False

    memo.is_deleted = True
    db.commit()

    # Clean up GCS image if present
    if memo.image_url:
        try:
            delete_image(memo.image_url)
        except Exception:
            logger.exception("Failed to delete GCS image for memo %s", memo_id)

    logger.info("Memo soft-deleted: id=%s, user=%s", memo_id, user_id)
    return True


DEFAULT_CATEGORIES = [
    {"name": "未分類", "sort_order": 0, "is_default": True},
    {"name": "ビジネス", "sort_order": 1, "is_default": False},
    {"name": "アイデア", "sort_order": 2, "is_default": False},
    {"name": "買い物", "sort_order": 3, "is_default": False},
    {"name": "その他", "sort_order": 4, "is_default": False},
]


def _ensure_default_categories(user_id: uuid.UUID, db: Session) -> None:
    """Create default categories for a user if they don't exist."""
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
