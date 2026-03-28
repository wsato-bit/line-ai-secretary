"""Admin endpoint tests.

Tests require_admin guard, approve/reject user flows.
"""

import uuid
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from sqlalchemy.orm import Session

from src.models.models import User, UserRole, UserStatus


# ─── Helper to mock LINE profile validation ───────────────────

def _mock_line_profile(user: User):
    """Return a context manager that mocks the LINE profile API call."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "userId": user.line_user_id,
        "displayName": user.line_display_name or "Test",
    }

    return patch(
        "src.utils.admin_middleware.httpx.AsyncClient",
        return_value=MagicMock(
            __aenter__=AsyncMock(return_value=MagicMock(
                get=AsyncMock(return_value=mock_response)
            )),
            __aexit__=AsyncMock(return_value=False),
        ),
    )


class TestRequireAdmin:
    """Admin middleware authorization tests."""

    def test_no_auth_header_returns_401(self, client):
        """Request without Authorization header should be rejected."""
        response = client.get("/api/admin/users")
        assert response.status_code == 401

    def test_non_admin_user_returns_403(
        self, client, db_session: Session, test_user: User
    ):
        """Non-admin user should receive 403 Forbidden."""
        with _mock_line_profile(test_user):
            response = client.get(
                "/api/admin/users",
                headers={"Authorization": "Bearer valid_token"},
            )
        assert response.status_code == 403

    def test_admin_user_gets_access(
        self, client, db_session: Session, admin_user: User
    ):
        """Admin user should be able to access admin endpoints."""
        with _mock_line_profile(admin_user):
            response = client.get(
                "/api/admin/users",
                headers={"Authorization": "Bearer admin_token"},
            )
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestApproveUser:
    """User approval tests."""

    def test_approve_pending_user(
        self, client, db_session: Session, admin_user: User, pending_user: User
    ):
        """Admin should be able to approve a pending user."""
        with _mock_line_profile(admin_user), \
             patch("src.services.user_service.approve_user", new_callable=AsyncMock) as mock_approve:
            # Return the updated user
            pending_user.status = UserStatus.approved
            pending_user.role = UserRole.user
            mock_approve.return_value = pending_user

            response = client.post(
                f"/api/admin/users/{pending_user.id}/approve",
                headers={"Authorization": "Bearer admin_token"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "approved"

    def test_approve_invalid_user_id_returns_400(
        self, client, db_session: Session, admin_user: User
    ):
        """Approving with invalid UUID should return 400."""
        with _mock_line_profile(admin_user):
            response = client.post(
                "/api/admin/users/not-a-uuid/approve",
                headers={"Authorization": "Bearer admin_token"},
            )
        assert response.status_code == 400


class TestRejectUser:
    """User rejection tests."""

    def test_reject_pending_user(
        self, client, db_session: Session, admin_user: User, pending_user: User
    ):
        """Admin should be able to reject a pending user with reason."""
        with _mock_line_profile(admin_user), \
             patch("src.services.user_service.reject_user", new_callable=AsyncMock) as mock_reject:
            pending_user.status = UserStatus.rejected
            pending_user.rejection_reason = "Not authorized"
            mock_reject.return_value = pending_user

            response = client.post(
                f"/api/admin/users/{pending_user.id}/reject",
                json={"reason": "Not authorized"},
                headers={"Authorization": "Bearer admin_token"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "rejected"

    def test_reject_without_reason(
        self, client, db_session: Session, admin_user: User, pending_user: User
    ):
        """Rejection without reason should still work (reason is optional)."""
        with _mock_line_profile(admin_user), \
             patch("src.services.user_service.reject_user", new_callable=AsyncMock) as mock_reject:
            pending_user.status = UserStatus.rejected
            mock_reject.return_value = pending_user

            response = client.post(
                f"/api/admin/users/{pending_user.id}/reject",
                json={},
                headers={"Authorization": "Bearer admin_token"},
            )

        assert response.status_code == 200
