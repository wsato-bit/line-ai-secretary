"""Authentication endpoint tests.

Tests LINE Login URL generation, callback, and /me endpoint.
"""

from unittest.mock import AsyncMock, patch

import pytest


class TestLineLogin:
    """LINE Login URL generation tests."""

    def test_login_url_generation(self, client):
        """GET /api/auth/line/login should return an authorization URL and state."""
        response = client.get("/api/auth/line/login")
        assert response.status_code == 200

        data = response.json()
        assert "authorization_url" in data
        assert "state" in data
        assert "access.line.me" in data["authorization_url"]
        assert "response_type=code" in data["authorization_url"]

    def test_login_url_contains_client_id(self, client):
        """Authorization URL should include the LINE Login channel ID."""
        response = client.get("/api/auth/line/login")
        data = response.json()
        assert "client_id=" in data["authorization_url"]

    def test_login_generates_unique_states(self, client):
        """Each login request should generate a unique state parameter."""
        r1 = client.get("/api/auth/line/login")
        r2 = client.get("/api/auth/line/login")
        assert r1.json()["state"] != r2.json()["state"]


class TestLineCallback:
    """LINE Login OAuth callback tests."""

    @patch("src.api.auth._get_line_profile", new_callable=AsyncMock)
    @patch("src.api.auth._exchange_code_for_token", new_callable=AsyncMock)
    def test_callback_with_valid_code(
        self, mock_exchange, mock_profile, client
    ):
        """Callback with valid code and state should return user info."""
        # First, generate a state
        login_response = client.get("/api/auth/line/login")
        state = login_response.json()["state"]

        mock_exchange.return_value = {"access_token": "test_access_token"}
        mock_profile.return_value = {
            "userId": "U_new_user_001",
            "displayName": "New User",
            "pictureUrl": "https://example.com/pic.jpg",
        }

        response = client.get(
            "/api/auth/line/callback",
            params={"code": "valid_auth_code", "state": state},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["user_id"] == "U_new_user_001"
        assert data["display_name"] == "New User"
        assert data["access_token"] == "test_access_token"
        assert data["status"] in ("active", "pending_approval", "new")

    def test_callback_with_invalid_state(self, client):
        """Callback with invalid state should return 400."""
        response = client.get(
            "/api/auth/line/callback",
            params={"code": "some_code", "state": "invalid_state"},
        )
        assert response.status_code == 400

    def test_callback_missing_code(self, client):
        """Callback without code parameter should return 422."""
        response = client.get(
            "/api/auth/line/callback",
            params={"state": "some_state"},
        )
        assert response.status_code == 422


class TestMeEndpoint:
    """GET /api/auth/me endpoint tests."""

    def test_me_without_auth_returns_401(self, client):
        """Request without Authorization header should return 401."""
        response = client.get("/api/auth/me")
        assert response.status_code == 401

    def test_me_with_invalid_bearer_returns_401(self, client):
        """Request with invalid bearer token should return 401."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401

    @patch("src.api.auth._get_line_profile", new_callable=AsyncMock)
    def test_me_with_valid_token(self, mock_profile, client):
        """Request with valid token should return user info."""
        mock_profile.return_value = {
            "userId": "U_test_user",
            "displayName": "Test User",
            "pictureUrl": None,
        }

        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer valid_access_token"},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["user_id"] == "U_test_user"
        assert data["display_name"] == "Test User"
        assert data["status"] == "active"


class TestLogout:
    """Logout endpoint tests."""

    def test_logout_returns_ok(self, client):
        """POST /api/auth/logout should return success."""
        response = client.post("/api/auth/logout")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
