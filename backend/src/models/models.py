"""SQLAlchemy ORM models for LINE AI Secretary.

All entities from the requirements document are defined here.
Uses UUID primary keys and PostgreSQL-specific types.
"""

import enum
import uuid
from datetime import datetime, time

from sqlalchemy import (
    ARRAY,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.models.database import Base


# ─── Enum Definitions ───────────────────────────────────────────


class UserRole(str, enum.Enum):
    guest = "guest"
    user = "user"
    admin = "admin"


class UserStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    disabled = "disabled"


class OAuthProvider(str, enum.Enum):
    line = "line"
    gmail = "gmail"
    gcalendar = "gcalendar"


class ContentType(str, enum.Enum):
    text = "text"
    image = "image"
    url = "url"


class EmailFilterType(str, enum.Enum):
    sender = "sender"
    domain = "domain"
    subject_pattern = "subject_pattern"


class EmailFilterAction(str, enum.Enum):
    important = "important"
    exclude = "exclude"


class EventType(str, enum.Enum):
    business = "business"
    private = "private"


class ConfirmationStatus(str, enum.Enum):
    confirmed = "confirmed"
    tentative = "tentative"


class EditAction(str, enum.Enum):
    create = "create"
    update = "update"
    delete = "delete"


# ─── Models ─────────────────────────────────────────────────────


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    line_user_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    line_display_name: Mapped[str | None] = mapped_column(String(128))
    line_picture_url: Mapped[str | None] = mapped_column(Text)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", native_enum=True),
        nullable=False,
        default=UserRole.guest,
    )
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, name="user_status", native_enum=True),
        nullable=False,
        default=UserStatus.pending,
    )
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    oauth_tokens: Mapped[list["OAuthToken"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    memos: Mapped[list["Memo"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    memo_categories: Mapped[list["MemoCategory"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    email_filters: Mapped[list["EmailFilter"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    unreplied_items: Mapped[list["UnrepliedItem"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    event_color_rules: Mapped[list["EventColorRule"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    notification_setting: Mapped["NotificationSetting | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    edit_histories: Mapped[list["EditHistory"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    approver: Mapped["User | None"] = relationship(remote_side=[id], foreign_keys=[approved_by])

    def __repr__(self) -> str:
        return f"<User {self.line_display_name} ({self.role.value}/{self.status.value})>"


class OAuthToken(Base):
    __tablename__ = "oauth_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    provider: Mapped[OAuthProvider] = mapped_column(
        Enum(OAuthProvider, name="oauth_provider", native_enum=True), nullable=False
    )
    access_token_encrypted: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    refresh_token_encrypted: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    scopes: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="oauth_tokens")

    __table_args__ = (UniqueConstraint("user_id", "provider", name="uq_oauth_user_provider"),)

    def __repr__(self) -> str:
        return f"<OAuthToken user={self.user_id} provider={self.provider.value}>"


class MemoCategory(Base):
    __tablename__ = "memo_categories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    user: Mapped["User"] = relationship(back_populates="memo_categories")
    memos: Mapped[list["Memo"]] = relationship(back_populates="category")

    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_memo_category_user_name"),)

    def __repr__(self) -> str:
        return f"<MemoCategory {self.name}>"


class Memo(Base):
    __tablename__ = "memos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[ContentType] = mapped_column(
        Enum(ContentType, name="content_type", native_enum=True), nullable=False
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("memo_categories.id"), index=True
    )
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(Text), server_default="{}")
    image_url: Mapped[str | None] = mapped_column(Text)
    image_ocr_text: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(Text)
    url_title: Mapped[str | None] = mapped_column(Text)
    url_summary: Mapped[str | None] = mapped_column(Text)
    url_thumbnail: Mapped[str | None] = mapped_column(Text)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="memos")
    category: Mapped["MemoCategory | None"] = relationship(back_populates="memos")

    def __repr__(self) -> str:
        return f"<Memo {self.id} type={self.content_type.value}>"


class EmailFilter(Base):
    __tablename__ = "email_filters"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    filter_type: Mapped[EmailFilterType] = mapped_column(
        Enum(EmailFilterType, name="email_filter_type", native_enum=True), nullable=False
    )
    filter_value: Mapped[str] = mapped_column(String(256), nullable=False)
    action: Mapped[EmailFilterAction] = mapped_column(
        Enum(EmailFilterAction, name="email_filter_action", native_enum=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    user: Mapped["User"] = relationship(back_populates="email_filters")

    __table_args__ = (UniqueConstraint("user_id", "filter_type", "filter_value", name="uq_email_filter"),)

    def __repr__(self) -> str:
        return f"<EmailFilter {self.filter_type.value}={self.filter_value}>"


class UnrepliedItem(Base):
    __tablename__ = "unreplied_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    contact_name: Mapped[str] = mapped_column(String(128), nullable=False)
    content_memo: Mapped[str | None] = mapped_column(Text)
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    user: Mapped["User"] = relationship(back_populates="unreplied_items")

    def __repr__(self) -> str:
        return f"<UnrepliedItem {self.contact_name} completed={self.is_completed}>"


class EventColorRule(Base):
    __tablename__ = "event_color_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    event_type: Mapped[EventType] = mapped_column(
        Enum(EventType, name="event_type_enum", native_enum=True), nullable=False
    )
    confirmation_status: Mapped[ConfirmationStatus] = mapped_column(
        Enum(ConfirmationStatus, name="confirmation_status_enum", native_enum=True), nullable=False
    )
    color_id: Mapped[str] = mapped_column(String(16), nullable=False)
    color_label: Mapped[str | None] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    user: Mapped["User"] = relationship(back_populates="event_color_rules")

    __table_args__ = (UniqueConstraint("user_id", "event_type", "confirmation_status", name="uq_event_color_rule"),)

    def __repr__(self) -> str:
        return f"<EventColorRule {self.event_type.value}/{self.confirmation_status.value}>"


class NotificationSetting(Base):
    __tablename__ = "notification_settings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    morning_summary_time: Mapped[time] = mapped_column(Time, default=time(8, 0))
    morning_summary_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    reminder_intervals: Mapped[list[int] | None] = mapped_column(ARRAY(Integer), server_default="{30,15,5}")
    unreplied_threshold_days: Mapped[int] = mapped_column(Integer, default=3)
    unreplied_reminder_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="notification_setting")

    def __repr__(self) -> str:
        return f"<NotificationSetting user={self.user_id}>"


class EditHistory(Base):
    __tablename__ = "edit_histories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    action: Mapped[EditAction] = mapped_column(Enum(EditAction, name="edit_action", native_enum=True), nullable=False)
    before_data: Mapped[dict | None] = mapped_column(JSONB)
    after_data: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    user: Mapped["User"] = relationship(back_populates="edit_histories")

    def __repr__(self) -> str:
        return f"<EditHistory {self.entity_type}/{self.action.value}>"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    resource: Mapped[str | None] = mapped_column(String(128))
    resource_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    ip_address: Mapped[str | None] = mapped_column(INET)
    user_agent: Mapped[str | None] = mapped_column(Text)
    metadata: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    user: Mapped["User | None"] = relationship(back_populates="audit_logs")

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} resource={self.resource}>"
