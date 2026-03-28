"""Unreplied service unit tests.

Tests register, list, complete, and overdue operations.
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import Session

from src.models.models import UnrepliedItem, User
from src.services import unreplied_service


class TestRegisterUnreplied:
    """Registration tests."""

    def test_register_creates_item(self, db_session: Session, test_user: User):
        """register_unreplied should create and persist an UnrepliedItem."""
        item = unreplied_service.register_unreplied(
            user_id=test_user.id,
            contact_name="Suzuki",
            content_memo="Call back about project",
            db=db_session,
        )

        assert item is not None
        assert item.contact_name == "Suzuki"
        assert item.content_memo == "Call back about project"
        assert item.user_id == test_user.id
        assert item.is_completed is False

    def test_register_without_memo(self, db_session: Session, test_user: User):
        """register_unreplied should work without content_memo."""
        item = unreplied_service.register_unreplied(
            user_id=test_user.id,
            contact_name="Yamada",
            content_memo=None,
            db=db_session,
        )
        assert item.content_memo is None
        assert item.contact_name == "Yamada"


class TestListUnreplied:
    """List/query tests."""

    def test_list_returns_items(
        self, db_session: Session, test_user: User, test_unreplied_item: UnrepliedItem
    ):
        """list_unreplied should return active items for the user."""
        results = unreplied_service.list_unreplied(
            user_id=test_user.id,
            db=db_session,
        )
        assert len(results) >= 1
        assert any(r["id"] == str(test_unreplied_item.id) for r in results)

    def test_list_has_days_elapsed(
        self, db_session: Session, test_user: User, test_unreplied_item: UnrepliedItem
    ):
        """Each item in list should have a days_elapsed field."""
        results = unreplied_service.list_unreplied(
            user_id=test_user.id,
            db=db_session,
        )
        assert len(results) >= 1
        assert "days_elapsed" in results[0]
        assert isinstance(results[0]["days_elapsed"], int)
        assert results[0]["days_elapsed"] >= 0

    def test_list_excludes_completed_by_default(
        self, db_session: Session, test_user: User, test_unreplied_item: UnrepliedItem
    ):
        """list_unreplied should exclude completed items by default."""
        test_unreplied_item.is_completed = True
        test_unreplied_item.completed_at = datetime.now(timezone.utc)
        db_session.commit()

        results = unreplied_service.list_unreplied(
            user_id=test_user.id,
            db=db_session,
        )
        assert not any(r["id"] == str(test_unreplied_item.id) for r in results)

    def test_list_includes_completed_when_requested(
        self, db_session: Session, test_user: User, test_unreplied_item: UnrepliedItem
    ):
        """list_unreplied with include_completed=True should return completed items."""
        test_unreplied_item.is_completed = True
        test_unreplied_item.completed_at = datetime.now(timezone.utc)
        db_session.commit()

        results = unreplied_service.list_unreplied(
            user_id=test_user.id,
            db=db_session,
            include_completed=True,
        )
        assert any(r["id"] == str(test_unreplied_item.id) for r in results)

    def test_list_days_elapsed_for_old_item(self, db_session: Session, test_user: User):
        """Items registered days ago should have correct days_elapsed."""
        old_item = UnrepliedItem(
            id=uuid.uuid4(),
            user_id=test_user.id,
            contact_name="Old Contact",
            registered_at=datetime.now(timezone.utc) - timedelta(days=5),
            is_completed=False,
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(old_item)
        db_session.commit()

        results = unreplied_service.list_unreplied(
            user_id=test_user.id,
            db=db_session,
        )
        old_result = next(r for r in results if r["id"] == str(old_item.id))
        assert old_result["days_elapsed"] >= 5


class TestCompleteUnreplied:
    """Completion tests."""

    def test_complete_marks_done(
        self, db_session: Session, test_user: User, test_unreplied_item: UnrepliedItem
    ):
        """complete_unreplied should mark item as completed."""
        result = unreplied_service.complete_unreplied(
            user_id=test_user.id,
            item_id=test_unreplied_item.id,
            db=db_session,
        )

        assert result is not None
        assert result.is_completed is True
        assert result.completed_at is not None

    def test_complete_nonexistent_returns_none(
        self, db_session: Session, test_user: User
    ):
        """Completing a non-existent item should return None."""
        result = unreplied_service.complete_unreplied(
            user_id=test_user.id,
            item_id=uuid.uuid4(),
            db=db_session,
        )
        assert result is None

    def test_complete_other_users_item_returns_none(
        self, db_session: Session, admin_user: User, test_unreplied_item: UnrepliedItem
    ):
        """Completing another user's item should return None."""
        result = unreplied_service.complete_unreplied(
            user_id=admin_user.id,
            item_id=test_unreplied_item.id,
            db=db_session,
        )
        assert result is None


class TestGetOverdueUnreplied:
    """Overdue detection tests."""

    def test_get_overdue_returns_old_items(self, db_session: Session, test_user: User):
        """get_overdue_unreplied should return items past threshold."""
        old_item = UnrepliedItem(
            id=uuid.uuid4(),
            user_id=test_user.id,
            contact_name="Overdue Contact",
            registered_at=datetime.now(timezone.utc) - timedelta(days=4),
            is_completed=False,
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(old_item)
        db_session.commit()

        overdue = unreplied_service.get_overdue_unreplied(
            user_id=test_user.id,
            threshold_days=3,
            db=db_session,
        )
        assert len(overdue) >= 1
        assert any(o["id"] == str(old_item.id) for o in overdue)

    def test_get_overdue_excludes_recent_items(
        self, db_session: Session, test_user: User, test_unreplied_item: UnrepliedItem
    ):
        """get_overdue_unreplied should not return recently registered items."""
        overdue = unreplied_service.get_overdue_unreplied(
            user_id=test_user.id,
            threshold_days=3,
            db=db_session,
        )
        assert not any(o["id"] == str(test_unreplied_item.id) for o in overdue)
