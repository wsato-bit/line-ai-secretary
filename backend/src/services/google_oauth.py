"""Google OAuth 2.0 token management utility.

Retrieves, decrypts, and refreshes Google OAuth tokens stored
in the OAuthToken model. Used by Calendar and Gmail services.
"""

import logging
from datetime import datetime, timezone

from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2.credentials import Credentials
from sqlalchemy.orm import Session

from src.config import config
from src.models.models import OAuthProvider, OAuthToken
from src.utils.encryption import decrypt_token, encrypt_token
from src.utils.errors import NotFoundError, ExternalServiceError

logger = logging.getLogger(__name__)

# Google OAuth endpoints
GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"


def get_google_credentials(
    user_id: str,
    db: Session,
    scopes: list[str],
    provider: OAuthProvider = OAuthProvider.gcalendar,
) -> Credentials:
    """Retrieve and return valid Google OAuth credentials for a user.

    Loads encrypted tokens from DB, decrypts them, and refreshes
    if expired. Updated tokens are re-encrypted and saved back.

    Args:
        user_id: The User.id (UUID as string).
        db: SQLAlchemy session.
        scopes: Required OAuth scopes.
        provider: OAuthProvider enum (gcalendar or gmail).

    Returns:
        google.oauth2.credentials.Credentials ready to use.

    Raises:
        NotFoundError: If no OAuth token found for user/provider.
        ExternalServiceError: If token refresh fails.
    """
    token_record = (
        db.query(OAuthToken)
        .filter(
            OAuthToken.user_id == user_id,
            OAuthToken.provider == provider,
        )
        .first()
    )

    if not token_record:
        raise NotFoundError(
            resource="OAuthToken",
            resource_id=f"{user_id}/{provider.value}",
        )

    access_token = decrypt_token(token_record.access_token_encrypted)
    refresh_token = decrypt_token(token_record.refresh_token_encrypted)

    credentials = Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri=GOOGLE_TOKEN_URI,
        client_id=config.LINE_LOGIN_CHANNEL_ID,  # reuse or add GOOGLE_CLIENT_ID
        client_secret=config.LINE_LOGIN_CHANNEL_SECRET,  # reuse or add GOOGLE_CLIENT_SECRET
        scopes=scopes,
    )

    # Check expiry and refresh if needed
    if _is_expired(token_record.expires_at):
        credentials = _refresh_credentials(credentials, token_record, db)

    return credentials


def _is_expired(expires_at: datetime) -> bool:
    """Check if token has expired (with 5-minute buffer)."""
    now = datetime.now(timezone.utc)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    buffer_seconds = 300  # 5 minutes
    return (expires_at.timestamp() - now.timestamp()) < buffer_seconds


def _refresh_credentials(
    credentials: Credentials,
    token_record: OAuthToken,
    db: Session,
) -> Credentials:
    """Refresh expired credentials and update DB record.

    Args:
        credentials: Google OAuth credentials with refresh token.
        token_record: OAuthToken DB record to update.
        db: SQLAlchemy session.

    Returns:
        Refreshed Credentials.

    Raises:
        ExternalServiceError: If refresh fails.
    """
    try:
        credentials.refresh(GoogleAuthRequest())
    except Exception as e:
        logger.error("Google OAuth token refresh failed: %s", e)
        raise ExternalServiceError(
            service="Google OAuth",
            message="Token refresh failed. User may need to re-authenticate.",
        )

    # Persist refreshed tokens
    token_record.access_token_encrypted = encrypt_token(credentials.token)
    if credentials.refresh_token:
        token_record.refresh_token_encrypted = encrypt_token(credentials.refresh_token)
    if credentials.expiry:
        token_record.expires_at = credentials.expiry.replace(tzinfo=timezone.utc)

    db.commit()
    logger.info("Refreshed Google OAuth token for user %s", token_record.user_id)

    return credentials
