"""LINE webhook endpoint tests.

Tests signature verification, event routing, and message handling.
"""

import hashlib
import hmac
import base64
import json
from unittest.mock import AsyncMock, patch, MagicMock

import pytest


# ─── Helper ───────────────────────────────────────────────────

def _make_signature(body: str, secret: str) -> str:
    """Generate a valid LINE webhook signature."""
    hash_value = hmac.new(
        secret.encode("utf-8"),
        body.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return base64.b64encode(hash_value).decode("utf-8")


def _text_message_body(user_id: str = "U_test_user", text: str = "Hello") -> dict:
    """Build a LINE text message webhook body."""
    return {
        "destination": "Udeadbeef",
        "events": [
            {
                "type": "message",
                "message": {
                    "type": "text",
                    "id": "12345",
                    "text": text,
                },
                "source": {
                    "type": "user",
                    "userId": user_id,
                },
                "replyToken": "test_reply_token",
                "mode": "active",
                "timestamp": 1625000000000,
            }
        ],
    }


# ─── Tests ────────────────────────────────────────────────────

class TestWebhookSignature:
    """Signature verification tests."""

    def test_missing_signature_returns_422(self, client):
        """Request without X-Line-Signature header should return 422."""
        response = client.post(
            "/api/line/webhook",
            json={"events": []},
        )
        assert response.status_code == 422

    def test_invalid_signature_returns_403(self, client):
        """Request with invalid signature should return 403."""
        body = json.dumps({"events": []})
        response = client.post(
            "/api/line/webhook",
            content=body,
            headers={
                "X-Line-Signature": "invalid_signature_value",
                "Content-Type": "application/json",
            },
        )
        assert response.status_code == 403

    @patch("src.api.line_webhook.parser")
    def test_valid_signature_returns_200(self, mock_parser, client):
        """Request with valid parsed events should return 200."""
        mock_parser.parse.return_value = []

        body = json.dumps({"events": []})
        signature = "valid_sig"

        response = client.post(
            "/api/line/webhook",
            content=body,
            headers={
                "X-Line-Signature": signature,
                "Content-Type": "application/json",
            },
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestWebhookEventRouting:
    """Event routing to handler functions."""

    @patch("src.api.line_webhook.handle_line_message", new_callable=AsyncMock)
    @patch("src.api.line_webhook.parser")
    def test_text_message_routes_to_agent(
        self, mock_parser, mock_handle, client
    ):
        """Text message event should be routed to handle_line_message."""
        # Create a mock MessageEvent with TextMessageContent
        mock_event = MagicMock()
        mock_event.__class__.__name__ = "MessageEvent"

        from linebot.v3.webhooks import MessageEvent, TextMessageContent
        mock_event.__class__ = MessageEvent

        mock_msg = MagicMock(spec=TextMessageContent)
        mock_msg.text = "Hello AI"
        mock_event.message = mock_msg
        mock_event.source.user_id = "U_test_user"
        mock_event.reply_token = "reply_tok_123"

        mock_parser.parse.return_value = [mock_event]

        body = json.dumps({"events": []})
        response = client.post(
            "/api/line/webhook",
            content=body,
            headers={
                "X-Line-Signature": "sig",
                "Content-Type": "application/json",
            },
        )
        assert response.status_code == 200
        mock_handle.assert_called_once()

    @patch("src.api.line_webhook.parser")
    def test_empty_events_returns_ok(self, mock_parser, client):
        """Webhook with no events should still return 200 ok."""
        mock_parser.parse.return_value = []

        body = json.dumps({"events": []})
        response = client.post(
            "/api/line/webhook",
            content=body,
            headers={
                "X-Line-Signature": "sig",
                "Content-Type": "application/json",
            },
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
