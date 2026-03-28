"""Admin API endpoints for user management."""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.models.database import get_db
from src.models.models import User
from src.services import user_service
from src.utils.admin_middleware import require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["Admin"])


# ─── Schemas ───────────────────────────────────────────────────


class UserResponse(BaseModel):
    id: str
    line_user_id: str
    line_display_name: str | None = None
    line_picture_url: str | None = None
    role: str
    status: str
    applied_at: str | None = None
    approved_at: str | None = None
    rejection_reason: str | None = None
    last_active_at: str | None = None
    created_at: str


class UserDetailResponse(UserResponse):
    memo_count: int = 0


class RejectRequest(BaseModel):
    reason: str | None = None


class MessageResponse(BaseModel):
    message: str


# ─── Helpers ───────────────────────────────────────────────────


def _user_to_response(user: User) -> UserResponse:
    """Convert User ORM object to response schema."""
    return UserResponse(
        id=str(user.id),
        line_user_id=user.line_user_id,
        line_display_name=user.line_display_name,
        line_picture_url=user.line_picture_url,
        role=user.role.value,
        status=user.status.value,
        applied_at=user.applied_at.isoformat() if user.applied_at else None,
        approved_at=user.approved_at.isoformat() if user.approved_at else None,
        rejection_reason=user.rejection_reason,
        last_active_at=user.last_active_at.isoformat() if user.last_active_at else None,
        created_at=user.created_at.isoformat(),
    )


def _user_detail_to_response(detail: dict) -> UserDetailResponse:
    """Convert user detail dict to response schema."""
    user = detail["user"]
    return UserDetailResponse(
        id=str(user.id),
        line_user_id=user.line_user_id,
        line_display_name=user.line_display_name,
        line_picture_url=user.line_picture_url,
        role=user.role.value,
        status=user.status.value,
        applied_at=user.applied_at.isoformat() if user.applied_at else None,
        approved_at=user.approved_at.isoformat() if user.approved_at else None,
        rejection_reason=user.rejection_reason,
        last_active_at=user.last_active_at.isoformat() if user.last_active_at else None,
        created_at=user.created_at.isoformat(),
        memo_count=detail["memo_count"],
    )


# ─── Endpoints ─────────────────────────────────────────────────


@router.get("/users", response_model=list[UserResponse])
def list_users(
    status: str | None = Query(None, description="Filter by status"),
    search: str | None = Query(None, description="Search by name or LINE ID"),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List all users with optional filters. Admin only."""
    users = user_service.list_users(db, status_filter=status, search=search)
    return [_user_to_response(u) for u in users]


@router.get("/users/{user_id}", response_model=UserDetailResponse)
def get_user_detail(
    user_id: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get user detail with statistics. Admin only."""
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format")

    detail = user_service.get_user_detail(uid, db)
    if not detail:
        raise HTTPException(status_code=404, detail="User not found")

    return _user_detail_to_response(detail)


@router.post("/users/{user_id}/approve", response_model=UserResponse)
async def approve_user(
    user_id: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Approve a pending user. Admin only."""
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format")

    try:
        user = await user_service.approve_user(admin.id, uid, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return _user_to_response(user)


@router.post("/users/{user_id}/reject", response_model=UserResponse)
async def reject_user(
    user_id: str,
    body: RejectRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Reject a pending user. Admin only."""
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format")

    try:
        user = await user_service.reject_user(admin.id, uid, body.reason, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return _user_to_response(user)


@router.post("/users/{user_id}/disable", response_model=UserResponse)
async def disable_user(
    user_id: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Disable an active user. Admin only."""
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format")

    try:
        user = await user_service.disable_user(admin.id, uid, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return _user_to_response(user)


@router.post("/users/{user_id}/enable", response_model=UserResponse)
async def enable_user(
    user_id: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Re-enable a disabled user. Admin only."""
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format")

    try:
        user = await user_service.enable_user(admin.id, uid, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return _user_to_response(user)
