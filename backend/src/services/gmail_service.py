"""Gmail service for email management.

Provides email retrieval, auto-classification, summary generation,
reply sending, and LINE display formatting.
"""

import base64
import logging
import re
from email.mime.text import MIMEText

from googleapiclient.discovery import build
from sqlalchemy.orm import Session

from src.models.models import OAuthProvider
from src.services.google_oauth import get_google_credentials
from src.utils.errors import ExternalServiceError, NotFoundError

logger = logging.getLogger(__name__)

GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]

# Known newsletter / bulk sender domains for auto-exclusion
NEWSLETTER_DOMAINS = frozenset({
    "noreply@", "no-reply@", "notifications@", "newsletter@",
    "marketing@", "info@", "updates@", "digest@", "mailer-daemon@",
})

BULK_SENDER_PATTERNS = [
    re.compile(r"list-unsubscribe", re.IGNORECASE),
    re.compile(r"precedence:\s*bulk", re.IGNORECASE),
    re.compile(r"precedence:\s*list", re.IGNORECASE),
]


def _build_gmail_client(user_id: str, db: Session):
    """Build an authenticated Gmail API client.

    Args:
        user_id: User UUID string.
        db: SQLAlchemy session.

    Returns:
        Gmail API service resource.
    """
    credentials = get_google_credentials(
        user_id=user_id,
        db=db,
        scopes=GMAIL_SCOPES,
        provider=OAuthProvider.gmail,
    )
    return build("gmail", "v1", credentials=credentials)


def get_emails(
    user_id: str,
    db: Session,
    query: str = "is:unread",
    max_results: int = 20,
) -> list[dict]:
    """Get email summaries from Gmail.

    Args:
        user_id: User UUID string.
        db: SQLAlchemy session.
        query: Gmail search query string.
        max_results: Maximum number of emails to return.

    Returns:
        List of email summary dicts.
    """
    service = _build_gmail_client(user_id, db)

    try:
        result = (
            service.users()
            .messages()
            .list(userId="me", q=query, maxResults=max_results)
            .execute()
        )
    except Exception as e:
        logger.error("Gmail list messages error: %s", e)
        raise ExternalServiceError(service="Gmail", message=str(e))

    messages = result.get("messages", [])
    if not messages:
        return []

    emails = []
    for msg_ref in messages:
        try:
            msg = (
                service.users()
                .messages()
                .get(userId="me", id=msg_ref["id"], format="metadata",
                     metadataHeaders=["From", "Subject", "Date", "List-Unsubscribe"])
                .execute()
            )
            email_data = _parse_email_metadata(msg)
            email_data["category"] = classify_email(email_data)
            emails.append(email_data)
        except Exception as e:
            logger.warning("Failed to fetch email %s: %s", msg_ref["id"], e)
            continue

    return emails


def get_email_body(user_id: str, db: Session, email_id: str) -> str:
    """Get the full body text of an email.

    Args:
        user_id: User UUID string.
        db: SQLAlchemy session.
        email_id: Gmail message ID.

    Returns:
        Plain text body of the email.
    """
    service = _build_gmail_client(user_id, db)

    try:
        msg = (
            service.users()
            .messages()
            .get(userId="me", id=email_id, format="full")
            .execute()
        )
    except Exception as e:
        logger.error("Gmail get message error: %s", e)
        raise NotFoundError(resource="Email", resource_id=email_id)

    return _extract_body_text(msg.get("payload", {}))


def classify_email(email_data: dict) -> str:
    """Auto-classify an email as important, reference, or excluded.

    Args:
        email_data: Parsed email metadata dict.

    Returns:
        Category string: "important", "reference", or "excluded".
    """
    from_addr = email_data.get("from", "").lower()
    headers_raw = email_data.get("headers_raw", "")

    # Check for auto-exclude patterns
    if _should_exclude(from_addr, headers_raw):
        return "excluded"

    # Check label IDs for importance signals
    label_ids = email_data.get("label_ids", [])
    if "IMPORTANT" in label_ids or "STARRED" in label_ids:
        return "important"

    # Default to reference
    return "reference"


def summarize_email(email_body: str) -> str:
    """Generate AI summary of an email body.

    This is a placeholder that returns a truncated preview.
    Full implementation will call Claude for summarization.

    Args:
        email_body: Full email body text.

    Returns:
        Summary string.
    """
    # TODO: Integrate Claude API for intelligent summarization
    if not email_body:
        return "本文なし"
    clean = email_body.strip().replace("\n", " ")
    if len(clean) > 200:
        return clean[:197] + "..."
    return clean


def send_email_reply(
    user_id: str,
    db: Session,
    email_id: str,
    body: str,
) -> dict:
    """Send a reply to an email.

    Args:
        user_id: User UUID string.
        db: SQLAlchemy session.
        email_id: Gmail message ID to reply to.
        body: Reply body text.

    Returns:
        Dict with sent message info.
    """
    service = _build_gmail_client(user_id, db)

    # Get original message for reply headers
    try:
        original = (
            service.users()
            .messages()
            .get(userId="me", id=email_id, format="metadata",
                 metadataHeaders=["From", "Subject", "Message-ID"])
            .execute()
        )
    except Exception as e:
        logger.error("Gmail get message for reply error: %s", e)
        raise NotFoundError(resource="Email", resource_id=email_id)

    headers = _extract_headers(original)
    to_addr = headers.get("From", "")
    subject = headers.get("Subject", "")
    if not subject.lower().startswith("re:"):
        subject = f"Re: {subject}"
    message_id = headers.get("Message-ID", "")
    thread_id = original.get("threadId", "")

    # Build MIME message
    mime_msg = MIMEText(body, "plain", "utf-8")
    mime_msg["to"] = to_addr
    mime_msg["subject"] = subject
    if message_id:
        mime_msg["In-Reply-To"] = message_id
        mime_msg["References"] = message_id

    raw = base64.urlsafe_b64encode(mime_msg.as_bytes()).decode("ascii")

    try:
        sent = (
            service.users()
            .messages()
            .send(
                userId="me",
                body={"raw": raw, "threadId": thread_id},
            )
            .execute()
        )
    except Exception as e:
        logger.error("Gmail send reply error: %s", e)
        raise ExternalServiceError(service="Gmail", message=str(e))

    logger.info("Sent reply to email %s for user %s", email_id, user_id)
    return {
        "message_id": sent.get("id", ""),
        "thread_id": sent.get("threadId", ""),
        "status": "sent",
    }


def format_emails_for_line(emails: list[dict]) -> list[dict]:
    """Format emails for LINE Flex Message display.

    Args:
        emails: List of email summary dicts.

    Returns:
        List of dicts ready for line_templates.email_summary_template().
    """
    priority_map = {"important": "high", "reference": "normal", "excluded": "low"}
    return [
        {
            "from": email.get("from", ""),
            "subject": email.get("subject", "件名なし"),
            "summary": email.get("snippet", ""),
            "priority": priority_map.get(email.get("category", ""), "normal"),
        }
        for email in emails
        if email.get("category") != "excluded"
    ]


# ─── Private helpers ───────────────────────────────────────────


def _parse_email_metadata(msg: dict) -> dict:
    """Parse Gmail message metadata into a clean dict."""
    headers = _extract_headers(msg)
    headers_raw = " ".join(f"{k}:{v}" for k, v in headers.items())

    return {
        "id": msg.get("id", ""),
        "thread_id": msg.get("threadId", ""),
        "from": headers.get("From", ""),
        "subject": headers.get("Subject", "件名なし"),
        "date": headers.get("Date", ""),
        "snippet": msg.get("snippet", ""),
        "label_ids": msg.get("labelIds", []),
        "has_list_unsubscribe": bool(headers.get("List-Unsubscribe")),
        "headers_raw": headers_raw,
    }


def _extract_headers(msg: dict) -> dict:
    """Extract headers from Gmail message payload."""
    headers = {}
    payload = msg.get("payload", {})
    for header in payload.get("headers", []):
        headers[header["name"]] = header["value"]
    return headers


def _extract_body_text(payload: dict) -> str:
    """Extract plain text body from Gmail message payload."""
    if payload.get("mimeType") == "text/plain":
        data = payload.get("body", {}).get("data", "")
        if data:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

    # Check parts recursively
    for part in payload.get("parts", []):
        text = _extract_body_text(part)
        if text:
            return text

    return ""


def _should_exclude(from_addr: str, headers_raw: str) -> bool:
    """Check if an email should be auto-excluded.

    Args:
        from_addr: Sender email address (lowercase).
        headers_raw: Raw header string for pattern matching.

    Returns:
        True if the email should be excluded.
    """
    # Check known newsletter sender patterns
    for pattern in NEWSLETTER_DOMAINS:
        if pattern in from_addr:
            return True

    # Check bulk mail headers
    for pattern in BULK_SENDER_PATTERNS:
        if pattern.search(headers_raw):
            return True

    return False
