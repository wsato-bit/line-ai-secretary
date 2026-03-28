"""Pydantic schemas for API request/response.

Single source of truth for type definitions.
"""

import uuid
from datetime import datetime, time

from pydantic import BaseModel, ConfigDict, Field


# ─── Base Schemas ────────────────────────────────────────────────


class BaseResponse(BaseModel):
    """Standard base for all response schemas."""

    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: bool = True
    message: str
    detail: str | list | None = None


class PaginationParams(BaseModel):
    """Common pagination parameters."""

    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)


class PaginatedResponse(BaseResponse):
    """Paginated list response wrapper."""

    total: int
    page: int
    per_page: int
    pages: int


# ─── User Schemas ────────────────────────────────────────────────


class UserResponse(BaseResponse):
    id: uuid.UUID
    line_user_id: str
    line_display_name: str | None = None
    line_picture_url: str | None = None
    role: str
    status: str
    applied_at: datetime | None = None
    approved_at: datetime | None = None
    last_active_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class UserApprovalRequest(BaseModel):
    """Admin approval/rejection of a user."""

    approved: bool
    rejection_reason: str | None = None


class UserListResponse(PaginatedResponse):
    items: list[UserResponse]


# ─── OAuth Schemas ───────────────────────────────────────────────


class OAuthCallbackRequest(BaseModel):
    """OAuth callback data."""

    code: str
    state: str | None = None


class OAuthTokenResponse(BaseResponse):
    id: uuid.UUID
    provider: str
    expires_at: datetime
    scopes: list[str] | None = None
    created_at: datetime


# ─── Memo Schemas ────────────────────────────────────────────────


class MemoCreateRequest(BaseModel):
    """Create a new memo."""

    content: str = Field(max_length=10000)
    content_type: str = Field(default="text")
    category_id: uuid.UUID | None = None
    tags: list[str] = Field(default_factory=list, max_length=20)
    image_url: str | None = None
    url: str | None = None


class MemoUpdateRequest(BaseModel):
    """Update an existing memo."""

    content: str | None = Field(default=None, max_length=10000)
    category_id: uuid.UUID | None = None
    tags: list[str] | None = Field(default=None, max_length=20)


class MemoResponse(BaseResponse):
    id: uuid.UUID
    user_id: uuid.UUID
    content: str
    content_type: str
    category_id: uuid.UUID | None = None
    tags: list[str] | None = None
    image_url: str | None = None
    image_ocr_text: str | None = None
    url: str | None = None
    url_title: str | None = None
    url_summary: str | None = None
    url_thumbnail: str | None = None
    created_at: datetime
    updated_at: datetime


class MemoListResponse(PaginatedResponse):
    items: list[MemoResponse]


# ─── MemoCategory Schemas ────────────────────────────────────────


class MemoCategoryCreateRequest(BaseModel):
    name: str = Field(max_length=64)
    sort_order: int = 0


class MemoCategoryUpdateRequest(BaseModel):
    name: str | None = Field(default=None, max_length=64)
    sort_order: int | None = None


class MemoCategoryResponse(BaseResponse):
    id: uuid.UUID
    name: str
    sort_order: int
    is_default: bool
    created_at: datetime


# ─── EmailFilter Schemas ─────────────────────────────────────────


class EmailFilterCreateRequest(BaseModel):
    filter_type: str  # sender / domain / subject_pattern
    filter_value: str = Field(max_length=256)
    action: str  # important / exclude


class EmailFilterResponse(BaseResponse):
    id: uuid.UUID
    filter_type: str
    filter_value: str
    action: str
    created_at: datetime


# ─── UnrepliedItem Schemas ───────────────────────────────────────


class UnrepliedItemCreateRequest(BaseModel):
    contact_name: str = Field(max_length=128)
    content_memo: str | None = None


class UnrepliedItemResponse(BaseResponse):
    id: uuid.UUID
    contact_name: str
    content_memo: str | None = None
    registered_at: datetime
    completed_at: datetime | None = None
    is_completed: bool
    days_elapsed: int | None = None
    created_at: datetime


class UnrepliedItemListResponse(PaginatedResponse):
    items: list[UnrepliedItemResponse]


# ─── EventColorRule Schemas ──────────────────────────────────────


class EventColorRuleCreateRequest(BaseModel):
    event_type: str  # business / private
    confirmation_status: str  # confirmed / tentative
    color_id: str = Field(max_length=16)
    color_label: str | None = Field(default=None, max_length=32)


class EventColorRuleResponse(BaseResponse):
    id: uuid.UUID
    event_type: str
    confirmation_status: str
    color_id: str
    color_label: str | None = None
    created_at: datetime


# ─── NotificationSetting Schemas ─────────────────────────────────


class NotificationSettingUpdateRequest(BaseModel):
    morning_summary_time: time | None = None
    morning_summary_enabled: bool | None = None
    reminder_intervals: list[int] | None = Field(default=None)
    unreplied_threshold_days: int | None = Field(default=None, ge=1, le=30)
    unreplied_reminder_enabled: bool | None = None


class NotificationSettingResponse(BaseResponse):
    id: uuid.UUID
    morning_summary_time: time
    morning_summary_enabled: bool
    reminder_intervals: list[int] | None = None
    unreplied_threshold_days: int
    unreplied_reminder_enabled: bool
    created_at: datetime
    updated_at: datetime


# ─── EditHistory Schemas ─────────────────────────────────────────


class EditHistoryResponse(BaseResponse):
    id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID
    action: str
    before_data: dict | None = None
    after_data: dict | None = None
    created_at: datetime


# ─── AuditLog Schemas ────────────────────────────────────────────


class AuditLogResponse(BaseResponse):
    id: uuid.UUID
    user_id: uuid.UUID | None = None
    action: str
    resource: str | None = None
    resource_id: uuid.UUID | None = None
    ip_address: str | None = None
    metadata: dict | None = None
    created_at: datetime


class AuditLogListResponse(PaginatedResponse):
    items: list[AuditLogResponse]


# ─── LINE Webhook Schemas ────────────────────────────────────────


class LineWebhookEvent(BaseModel):
    """Simplified LINE webhook event."""

    type: str
    reply_token: str | None = None
    source: dict | None = None
    message: dict | None = None
    timestamp: int | None = None


class LineWebhookRequest(BaseModel):
    """LINE webhook request body."""

    destination: str | None = None
    events: list[LineWebhookEvent] = Field(default_factory=list)


# ─── Health / Misc ───────────────────────────────────────────────


class HealthResponse(BaseModel):
    status: str = "ok"
