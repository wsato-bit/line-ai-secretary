"""LINE unreplied item management API endpoints."""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.models.database import get_db
from src.services import unreplied_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/unreplied", tags=["Unreplied"])


# ─── Schemas ───────────────────────────────────────────────────


class UnrepliedItemResponse(BaseModel):
    id: str
    contact_name: str
    content_memo: str | None = None
    registered_at: str
    completed_at: str | None = None
    is_completed: bool
    days_elapsed: int


class CreateUnrepliedRequest(BaseModel):
    contact_name: str
    content_memo: str | None = None


# ─── Helpers ───────────────────────────────────────────────────


def _get_user_id_from_header(user_id: str = Query(..., alias="user_id")) -> uuid.UUID:
    """Extract user_id from query parameter.

    TODO: Replace with proper auth dependency that extracts user from JWT/session.
    """
    try:
        return uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format")


# ─── Endpoints ─────────────────────────────────────────────────


@router.get("", response_model=list[UnrepliedItemResponse])
def list_unreplied_items(
    user_id: uuid.UUID = Depends(_get_user_id_from_header),
    include_completed: bool = Query(False),
    db: Session = Depends(get_db),
):
    """List unreplied items with days_elapsed calculation."""
    items = unreplied_service.list_unreplied(
        user_id=user_id,
        db=db,
        include_completed=include_completed,
    )
    return items


@router.post("", response_model=UnrepliedItemResponse, status_code=201)
def create_unreplied_item(
    body: CreateUnrepliedRequest,
    user_id: uuid.UUID = Depends(_get_user_id_from_header),
    db: Session = Depends(get_db),
):
    """Register a new unreplied item."""
    item = unreplied_service.register_unreplied(
        user_id=user_id,
        contact_name=body.contact_name,
        content_memo=body.content_memo,
        db=db,
    )
    return {
        "id": str(item.id),
        "contact_name": item.contact_name,
        "content_memo": item.content_memo,
        "registered_at": item.registered_at.isoformat(),
        "completed_at": None,
        "is_completed": item.is_completed,
        "days_elapsed": 0,
    }


@router.put("/{item_id}/complete", response_model=UnrepliedItemResponse)
def complete_unreplied_item(
    item_id: str,
    user_id: uuid.UUID = Depends(_get_user_id_from_header),
    db: Session = Depends(get_db),
):
    """Mark an unreplied item as completed."""
    try:
        item_uuid = uuid.UUID(item_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid item_id format")

    item = unreplied_service.complete_unreplied(user_id, item_uuid, db)
    if not item:
        raise HTTPException(status_code=404, detail="Unreplied item not found")

    return {
        "id": str(item.id),
        "contact_name": item.contact_name,
        "content_memo": item.content_memo,
        "registered_at": item.registered_at.isoformat(),
        "completed_at": item.completed_at.isoformat() if item.completed_at else None,
        "is_completed": item.is_completed,
        "days_elapsed": 0,
    }
