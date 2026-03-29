"""Schedule management API endpoints.

Provides Google Calendar CRUD operations and color rule management
via REST API, authenticated with LINE Login token.
"""

from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.models.database import get_db
from src.services.calendar_service import (
    create_event,
    delete_event,
    find_available_slots,
    get_schedule,
    update_event,
)
from src.services.color_defaults import ensure_default_color_rules
from src.models.models import ConfirmationStatus, EventColorRule, EventType
from src.utils.errors import ExternalServiceError, NotFoundError
from src.utils.resolve_user import resolve_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/schedule", tags=["Schedule"])


# ─── Request/Response schemas ──────────────────────────────────


class EventCreate(BaseModel):
    summary: str = Field(..., min_length=1, max_length=256)
    start: str = Field(..., description="ISO format datetime or date")
    end: str = Field(..., description="ISO format datetime or date")
    description: str | None = None
    location: str | None = None
    event_type: str = Field(default="business", pattern="^(business|private)$")
    confirmation_status: str = Field(default="confirmed", pattern="^(confirmed|tentative)$")


class EventUpdate(BaseModel):
    summary: str | None = Field(default=None, max_length=256)
    start: str | None = None
    end: str | None = None
    description: str | None = None
    location: str | None = None
    event_type: str | None = Field(default=None, pattern="^(business|private)$")
    confirmation_status: str | None = Field(default=None, pattern="^(confirmed|tentative)$")


class ColorRuleUpdate(BaseModel):
    event_type: str = Field(..., pattern="^(business|private)$")
    confirmation_status: str = Field(..., pattern="^(confirmed|tentative)$")
    color_id: str = Field(..., min_length=1, max_length=16)
    color_label: str | None = Field(default=None, max_length=32)


class ColorRuleBatchUpdate(BaseModel):
    rules: list[ColorRuleUpdate]


# ─── Endpoints ─────────────────────────────────────────────────


@router.get("")
async def list_schedule(
    date_from: str = Query(..., description="Start date YYYY-MM-DD"),
    date_to: str = Query(..., description="End date YYYY-MM-DD"),
    user_id: str = Query(..., description="User UUID or LINE user ID"),
    db: Session = Depends(get_db),
):
    """Get calendar events within a date range."""
    _validate_date_range(date_from, date_to)

    try:
        resolved_id = resolve_user_id(user_id, db)
    except ValueError:
        return {"events": [], "count": 0, "message": "ユーザーが見つかりません。"}

    try:
        events = get_schedule(resolved_id, db, date_from, date_to)
        return {"events": events, "count": len(events)}
    except Exception as e:
        logger.warning("Schedule fetch failed (returning empty): %s", str(e))
        return {"events": [], "count": 0, "message": "Google Calendar未連携です。設定ページから連携してください。"}


@router.get("/available")
async def list_available_slots(
    date: str = Query(..., description="Date YYYY-MM-DD"),
    duration: int = Query(default=60, ge=15, le=480, description="Duration in minutes"),
    user_id: str = Query(..., description="User UUID or LINE user ID"),
    db: Session = Depends(get_db),
):
    """Find available time slots on a given date."""
    _validate_date(date)

    try:
        resolved_id = resolve_user_id(user_id, db)
    except ValueError:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        slots = find_available_slots(resolved_id, db, date, duration)
        return {"available_slots": slots, "count": len(slots)}
    except Exception as e:
        logger.warning("Available slots fetch failed: %s", str(e))
        return {"available_slots": [], "count": 0, "message": "Google Calendar未連携です。設定ページから連携してください。"}


@router.post("/events")
async def create_schedule_event(
    body: EventCreate,
    user_id: str = Query(..., description="User UUID or LINE user ID"),
    db: Session = Depends(get_db),
):
    """Create a new calendar event."""
    try:
        resolved_id = resolve_user_id(user_id, db)
    except ValueError:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        event = create_event(resolved_id, db, body.model_dump())
        return {"event": event, "message": "予定を作成しました"}
    except NotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Google Calendar未連携です。OAuth認証を完了してください。",
        )
    except ExternalServiceError as e:
        raise HTTPException(status_code=502, detail=str(e.message))


@router.put("/events/{event_id}")
async def update_schedule_event(
    event_id: str,
    body: EventUpdate,
    user_id: str = Query(..., description="User UUID or LINE user ID"),
    db: Session = Depends(get_db),
):
    """Update an existing calendar event."""
    try:
        resolved_id = resolve_user_id(user_id, db)
    except ValueError:
        raise HTTPException(status_code=404, detail="User not found")

    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=422, detail="更新フィールドを指定してください")

    try:
        event = update_event(resolved_id, db, event_id, updates)
        return {"event": event, "message": "予定を更新しました"}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e.message))
    except ExternalServiceError as e:
        raise HTTPException(status_code=502, detail=str(e.message))


@router.delete("/events/{event_id}")
async def delete_schedule_event(
    event_id: str,
    user_id: str = Query(..., description="User UUID or LINE user ID"),
    db: Session = Depends(get_db),
):
    """Delete a calendar event."""
    try:
        resolved_id = resolve_user_id(user_id, db)
    except ValueError:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        delete_event(resolved_id, db, event_id)
        return {"message": "予定を削除しました"}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e.message))
    except ExternalServiceError as e:
        raise HTTPException(status_code=502, detail=str(e.message))


@router.get("/color-rules")
async def list_color_rules(
    user_id: str = Query(..., description="User UUID or LINE user ID"),
    db: Session = Depends(get_db),
):
    """Get event color rules for user (creates defaults if none exist)."""
    try:
        resolved_id = resolve_user_id(user_id, db)
    except ValueError:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        rules = ensure_default_color_rules(resolved_id, db)
        return {
            "rules": [
                {
                    "id": str(r.id),
                    "event_type": r.event_type.value,
                    "confirmation_status": r.confirmation_status.value,
                    "color_id": r.color_id,
                    "color_label": r.color_label,
                }
                for r in rules
            ]
        }
    except Exception as e:
        logger.warning("Color rules fetch failed: %s", str(e))
        return {"rules": []}


@router.put("/color-rules")
async def update_color_rules(
    body: ColorRuleBatchUpdate,
    user_id: str = Query(..., description="User UUID or LINE user ID"),
    db: Session = Depends(get_db),
):
    """Batch update event color rules."""
    try:
        resolved_id = resolve_user_id(user_id, db)
    except ValueError:
        raise HTTPException(status_code=404, detail="User not found")

    updated = []
    for rule_data in body.rules:
        event_type = EventType(rule_data.event_type)
        confirmation = ConfirmationStatus(rule_data.confirmation_status)

        rule = (
            db.query(EventColorRule)
            .filter(
                EventColorRule.user_id == resolved_id,
                EventColorRule.event_type == event_type,
                EventColorRule.confirmation_status == confirmation,
            )
            .first()
        )

        if rule:
            rule.color_id = rule_data.color_id
            rule.color_label = rule_data.color_label
        else:
            rule = EventColorRule(
                user_id=resolved_id,
                event_type=event_type,
                confirmation_status=confirmation,
                color_id=rule_data.color_id,
                color_label=rule_data.color_label,
            )
            db.add(rule)

        updated.append(
            {
                "event_type": rule_data.event_type,
                "confirmation_status": rule_data.confirmation_status,
                "color_id": rule_data.color_id,
                "color_label": rule_data.color_label,
            }
        )

    db.commit()
    return {"rules": updated, "message": "カラールールを更新しました"}


# ─── Helpers ───────────────────────────────────────────────────


def _validate_date(date_str: str) -> None:
    """Validate a date string in YYYY-MM-DD format."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail=f"日付形式が不正です: {date_str} (YYYY-MM-DD形式で指定してください)",
        )


def _validate_date_range(date_from: str, date_to: str) -> None:
    """Validate date range parameters."""
    _validate_date(date_from)
    _validate_date(date_to)
    if date_from > date_to:
        raise HTTPException(
            status_code=422,
            detail="date_fromはdate_to以前の日付を指定してください",
        )
