"""Admin authentication and authorization middleware."""

import logging

import httpx
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from src.models.database import get_db
from src.models.models import User, UserRole

logger = logging.getLogger(__name__)

LINE_PROFILE_URL = "https://api.line.me/v2/profile"


async def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """Resolve current user from Authorization Bearer token.

    Validates the LINE access token, looks up the user in DB,
    and returns the User ORM object.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    access_token = auth_header.removeprefix("Bearer ").strip()
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Validate token via LINE Profile API
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                LINE_PROFILE_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if resp.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid or expired token")
            profile = resp.json()
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to validate LINE token")
        raise HTTPException(status_code=401, detail="Token validation failed")

    line_user_id = profile.get("userId")
    if not line_user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.line_user_id == line_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


async def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency that ensures the current user has admin role.

    Returns the admin User if authorized, raises 403 otherwise.
    """
    if current_user.role != UserRole.admin:
        logger.warning(
            "Non-admin access attempt: user_id=%s, role=%s",
            current_user.id,
            current_user.role.value,
        )
        raise HTTPException(
            status_code=403,
            detail="Admin access required",
        )
    return current_user
