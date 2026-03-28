"""Memo service unit tests.

Tests save, search, delete operations with mocked external services.
"""

import uuid
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from sqlalchemy.orm import Session

from src.models.models import ContentType, Memo, MemoCategory, User
from src.services import memo_service


class TestSaveTextMemo:
    """Text memo save tests."""

    @pytest.mark.asyncio
    async def test_save_text_memo(self, db_session: Session, test_user: User, test_memo_category):
        """Saving a text memo should persist content and return Memo object."""
        memo = await memo_service.save_memo(
            user_id=test_user.id,
            content="Important meeting notes",
            content_type="text",
            db=db_session,
        )

        assert memo is not None
        assert memo.content == "Important meeting notes"
        assert memo.content_type == ContentType.text
        assert memo.user_id == test_user.id
        assert memo.is_deleted is False

    @pytest.mark.asyncio
    async def test_save_text_memo_has_default_category(
        self, db_session: Session, test_user: User, test_memo_category
    ):
        """Text memo should be assigned the default category."""
        memo = await memo_service.save_memo(
            user_id=test_user.id,
            content="Categorized memo",
            content_type="text",
            db=db_session,
        )
        assert memo.category_id == test_memo_category.id


class TestSaveImageMemo:
    """Image memo save tests with mocked GCS and Vision."""

    @pytest.mark.asyncio
    async def test_save_image_memo(
        self, db_session: Session, test_user: User, test_memo_category, mock_gcs, mock_vision
    ):
        """Saving an image memo should upload to GCS and run OCR."""
        memo = await memo_service.save_memo(
            user_id=test_user.id,
            content="Receipt photo",
            content_type="image",
            db=db_session,
            file_data=b"fake_image_data",
            filename="receipt.png",
        )

        assert memo is not None
        assert memo.content_type == ContentType.image
        assert memo.image_url is not None
        assert "storage.googleapis.com" in memo.image_url
        assert memo.image_ocr_text == "OCR extracted text from image"

        mock_gcs["upload"].assert_called_once()
        mock_vision.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_image_memo_without_file(
        self, db_session: Session, test_user: User, test_memo_category
    ):
        """Image memo without file data should still save but without image URL."""
        memo = await memo_service.save_memo(
            user_id=test_user.id,
            content="No file image",
            content_type="image",
            db=db_session,
        )
        assert memo is not None
        assert memo.image_url is None


class TestSaveUrlMemo:
    """URL memo save tests with mocked httpx."""

    @pytest.mark.asyncio
    async def test_save_url_memo(self, db_session: Session, test_user: User, test_memo_category):
        """Saving a URL memo should fetch metadata and store it."""
        mock_metadata = MagicMock()
        mock_metadata.title = "Example Page Title"
        mock_metadata.description = "A description of the page"
        mock_metadata.thumbnail = "https://example.com/thumb.jpg"

        with patch(
            "src.services.memo_service.fetch_url_metadata",
            new_callable=AsyncMock,
            return_value=mock_metadata,
        ):
            memo = await memo_service.save_memo(
                user_id=test_user.id,
                content="https://example.com",
                content_type="url",
                db=db_session,
            )

        assert memo is not None
        assert memo.content_type == ContentType.url
        assert memo.url == "https://example.com"
        assert memo.url_title == "Example Page Title"
        assert memo.url_summary == "A description of the page"
        assert memo.url_thumbnail == "https://example.com/thumb.jpg"


class TestSearchMemo:
    """Memo search tests."""

    def test_search_returns_user_memos(
        self, db_session: Session, test_user: User, test_memo: Memo
    ):
        """Search should return memos belonging to the user."""
        results = memo_service.search_memo(user_id=test_user.id, db=db_session)
        assert len(results) >= 1
        assert any(m.id == test_memo.id for m in results)

    def test_search_excludes_deleted_memos(
        self, db_session: Session, test_user: User, test_memo: Memo
    ):
        """Search should not return soft-deleted memos."""
        test_memo.is_deleted = True
        db_session.commit()

        results = memo_service.search_memo(user_id=test_user.id, db=db_session)
        assert not any(m.id == test_memo.id for m in results)

    def test_search_by_query(
        self, db_session: Session, test_user: User, test_memo: Memo
    ):
        """Search with keyword should filter by content."""
        results = memo_service.search_memo(
            user_id=test_user.id,
            db=db_session,
            query="Test memo",
        )
        assert len(results) >= 1

    def test_search_by_query_no_match(
        self, db_session: Session, test_user: User, test_memo: Memo
    ):
        """Search with non-matching keyword should return empty."""
        results = memo_service.search_memo(
            user_id=test_user.id,
            db=db_session,
            query="nonexistent_keyword_xyz",
        )
        assert len(results) == 0

    def test_search_other_user_returns_empty(
        self, db_session: Session, admin_user: User, test_memo: Memo
    ):
        """Search should not return memos from other users."""
        results = memo_service.search_memo(user_id=admin_user.id, db=db_session)
        assert not any(m.id == test_memo.id for m in results)


class TestDeleteMemo:
    """Memo soft-delete tests."""

    def test_delete_memo_soft_deletes(
        self, db_session: Session, test_user: User, test_memo: Memo
    ):
        """delete_memo should set is_deleted=True."""
        result = memo_service.delete_memo(test_user.id, test_memo.id, db_session)
        assert result is True

        db_session.refresh(test_memo)
        assert test_memo.is_deleted is True

    def test_delete_nonexistent_memo_returns_false(
        self, db_session: Session, test_user: User
    ):
        """Deleting a non-existent memo should return False."""
        fake_id = uuid.uuid4()
        result = memo_service.delete_memo(test_user.id, fake_id, db_session)
        assert result is False

    def test_delete_other_users_memo_returns_false(
        self, db_session: Session, admin_user: User, test_memo: Memo
    ):
        """Deleting another user's memo should return False."""
        result = memo_service.delete_memo(admin_user.id, test_memo.id, db_session)
        assert result is False
