"""Pytest fixtures for LINE AI Secretary backend tests.

Provides: test client, mock DB session, mock LINE service, mock Google APIs.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import Session, sessionmaker

from src.models.database import Base, get_db
from src.models.models import (
    ContentType,
    Memo,
    MemoCategory,
    UnrepliedItem,
    User,
    UserRole,
    UserStatus,
)


# ─── In-memory SQLite for testing ─────────────────────────────

@pytest.fixture(scope="session")
def test_engine():
    """Create an in-memory SQLite engine for the entire test session."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # Create all tables
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture()
def db_session(test_engine):
    """Provide a transactional DB session that rolls back after each test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    TestSession = sessionmaker(bind=connection)
    session = TestSession()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


# ─── FastAPI Test Client ──────────────────────────────────────

@pytest.fixture()
def client(db_session):
    """Create a FastAPI TestClient with overridden DB dependency."""
    # Patch config and database module before importing app
    with patch("src.config.config") as mock_config:
        mock_config.LINE_CHANNEL_SECRET = "test_channel_secret"
        mock_config.LINE_CHANNEL_ACCESS_TOKEN = "test_access_token"
        mock_config.LINE_LOGIN_CHANNEL_ID = "test_login_channel_id"
        mock_config.LINE_LOGIN_CHANNEL_SECRET = "test_login_channel_secret"
        mock_config.ANTHROPIC_API_KEY = "test_anthropic_key"
        mock_config.FRONTEND_URL = "http://localhost:3847"
        mock_config.DATABASE_URL = "sqlite:///:memory:"
        mock_config.HOST = "0.0.0.0"
        mock_config.PORT = 8293

        from src.main import app

        def _override_get_db():
            try:
                yield db_session
            finally:
                pass

        app.dependency_overrides[get_db] = _override_get_db

        with TestClient(app) as test_client:
            yield test_client

        app.dependency_overrides.clear()


# ─── Test Data Factories ──────────────────────────────────────

@pytest.fixture()
def test_user(db_session: Session) -> User:
    """Create a test user in the database."""
    user = User(
        id=uuid.uuid4(),
        line_user_id="U_test_user_001",
        line_display_name="Test User",
        role=UserRole.user,
        status=UserStatus.approved,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def admin_user(db_session: Session) -> User:
    """Create an admin user in the database."""
    user = User(
        id=uuid.uuid4(),
        line_user_id="U_admin_001",
        line_display_name="Admin User",
        role=UserRole.admin,
        status=UserStatus.approved,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def pending_user(db_session: Session) -> User:
    """Create a pending-approval user in the database."""
    user = User(
        id=uuid.uuid4(),
        line_user_id="U_pending_001",
        line_display_name="Pending User",
        role=UserRole.guest,
        status=UserStatus.pending,
        applied_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def test_memo_category(db_session: Session, test_user: User) -> MemoCategory:
    """Create a default memo category for the test user."""
    category = MemoCategory(
        id=uuid.uuid4(),
        user_id=test_user.id,
        name="未分類",
        sort_order=0,
        is_default=True,
    )
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    return category


@pytest.fixture()
def test_memo(db_session: Session, test_user: User, test_memo_category: MemoCategory) -> Memo:
    """Create a test memo."""
    memo = Memo(
        id=uuid.uuid4(),
        user_id=test_user.id,
        content="Test memo content",
        content_type=ContentType.text,
        category_id=test_memo_category.id,
        tags=["test", "sample"],
        is_deleted=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(memo)
    db_session.commit()
    db_session.refresh(memo)
    return memo


@pytest.fixture()
def test_unreplied_item(db_session: Session, test_user: User) -> UnrepliedItem:
    """Create a test unreplied item."""
    item = UnrepliedItem(
        id=uuid.uuid4(),
        user_id=test_user.id,
        contact_name="Tanaka",
        content_memo="Meeting follow-up",
        registered_at=datetime.now(timezone.utc),
        is_completed=False,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)
    return item


# ─── Mock External Services ───────────────────────────────────

@pytest.fixture()
def mock_line_service():
    """Mock LINE messaging service."""
    with patch("src.services.line_service.line_service") as mock:
        mock.reply_text = AsyncMock(return_value=None)
        mock.push_text = AsyncMock(return_value=None)
        mock.push_flex = AsyncMock(return_value=None)
        yield mock


@pytest.fixture()
def mock_gcs():
    """Mock Google Cloud Storage service."""
    with patch("src.services.storage_service.upload_image") as mock_upload, \
         patch("src.services.storage_service.delete_image") as mock_delete:
        mock_upload.return_value = "https://storage.googleapis.com/test-bucket/test-image.png"
        mock_delete.return_value = None
        yield {"upload": mock_upload, "delete": mock_delete}


@pytest.fixture()
def mock_vision():
    """Mock Google Cloud Vision OCR service."""
    with patch("src.services.ocr_service.extract_text") as mock:
        mock.return_value = "OCR extracted text from image"
        yield mock


@pytest.fixture()
def mock_anthropic():
    """Mock Anthropic Claude API client."""
    with patch("anthropic.Anthropic") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        yield mock_client


@pytest.fixture()
def mock_httpx():
    """Mock httpx async client for URL fetching."""
    with patch("httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
        yield mock_client
