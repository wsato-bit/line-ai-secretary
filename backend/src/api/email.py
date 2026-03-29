"""Email management API endpoints.

Provides Gmail read/reply operations and email filter management
via REST API, authenticated with LINE Login token.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.models.database import get_db
from src.services.email_filter_service import (
    apply_filters,
    delete_filter,
    get_filters,
    set_email_filter,
)
from src.services.gmail_service import (
    get_emails,
    send_email_reply,
    summarize_email,
)
from src.utils.errors import (
    ConflictError,
    ExternalServiceError,
    NotFoundError,
)
from src.utils.resolve_user import resolve_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/emails", tags=["Email"])


# ─── Request/Response schemas ──────────────────────────────────


class EmailReplyRequest(BaseModel):
    body: str = Field(..., min_length=1, max_length=10000)


class EmailFilterCreate(BaseModel):
    filter_type: str = Field(..., pattern="^(sender|domain|subject_pattern)$")
    filter_value: str = Field(..., min_length=1, max_length=256)
    action: str = Field(..., pattern="^(important|exclude)$")


# ─── Email endpoints ───────────────────────────────────────────


@router.get("")
async def list_emails(
    user_id: str = Query(..., description="User UUID or LINE user ID"),
    query: str = Query(default="is:unread", description="Gmail search query"),
    category: str | None = Query(
        default=None,
        description="Filter by category: important, reference, excluded",
    ),
    max_results: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Get emails with auto-classification and user filters applied."""
    try:
        resolved_id = resolve_user_id(user_id, db)
    except ValueError:
        return {"emails": [], "count": 0, "message": "ユーザーが見つかりません。"}

    try:
        emails = get_emails(resolved_id, db, query, max_results)
        emails = apply_filters(resolved_id, db, emails)
        if category:
            emails = [e for e in emails if e.get("category") == category]
        return {"emails": emails, "count": len(emails)}
    except Exception as e:
        logger.warning("Email fetch failed (returning empty): %s", str(e))
        return {"emails": [], "count": 0, "message": "Gmail未連携です。設定ページから連携してください。"}


@router.get("/{email_id}/summary")
async def get_email_summary(
    email_id: str,
    user_id: str = Query(..., description="User UUID or LINE user ID"),
    db: Session = Depends(get_db),
):
    """Get AI-generated summary of an email."""
    try:
        resolved_id = resolve_user_id(user_id, db)
    except ValueError:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        summary = summarize_email(resolved_id, db, email_id)
        return {"email_id": email_id, "summary": summary}
    except Exception as e:
        logger.warning("Email summary failed: %s", str(e))
        return {"email_id": email_id, "summary": "Gmail未連携のためサマリーを取得できません。"}


@router.post("/{email_id}/reply")
async def reply_to_email(
    email_id: str,
    body: EmailReplyRequest,
    user_id: str = Query(..., description="User UUID or LINE user ID"),
    db: Session = Depends(get_db),
):
    """Send a reply to an email."""
    try:
        resolved_id = resolve_user_id(user_id, db)
    except ValueError:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        result = send_email_reply(resolved_id, db, email_id, body.body)
        return {"result": result, "message": "返信を送信しました"}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e.message))
    except ExternalServiceError as e:
        raise HTTPException(status_code=502, detail=str(e.message))


# ─── Filter endpoints ──────────────────────────────────────────


@router.get("/filters")
async def list_email_filters(
    user_id: str = Query(..., description="User UUID or LINE user ID"),
    db: Session = Depends(get_db),
):
    """Get all email filters for the user."""
    try:
        resolved_id = resolve_user_id(user_id, db)
    except ValueError:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        filters = get_filters(resolved_id, db)
        return {"filters": filters, "count": len(filters)}
    except Exception as e:
        logger.warning("Email filter fetch failed: %s", str(e))
        return {"filters": [], "count": 0}


@router.post("/filters")
async def create_email_filter(
    body: EmailFilterCreate,
    user_id: str = Query(..., description="User UUID or LINE user ID"),
    db: Session = Depends(get_db),
):
    """Create a new email filter."""
    try:
        resolved_id = resolve_user_id(user_id, db)
    except ValueError:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        result = set_email_filter(resolved_id, db, body.filter_type, body.filter_value, body.action)
        return {"filter": result, "message": "フィルターを作成しました"}
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e.message))


@router.delete("/filters/{filter_id}")
async def remove_email_filter(
    filter_id: str,
    user_id: str = Query(..., description="User UUID or LINE user ID"),
    db: Session = Depends(get_db),
):
    """Delete an email filter."""
    try:
        resolved_id = resolve_user_id(user_id, db)
    except ValueError:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        delete_filter(resolved_id, db, filter_id)
        return {"message": "フィルターを削除しました"}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e.message))
