"""Alembic migration environment configuration.

Reads DATABASE_URL from the application config module so that
the connection string is managed in one place.
"""

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# Add project root to sys.path so that 'src' imports work
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import config as app_config  # noqa: E402
from src.models.database import Base  # noqa: E402
from src.models.models import (  # noqa: E402, F401  (import to register models)
    AuditLog,
    EditHistory,
    EmailFilter,
    EventColorRule,
    Memo,
    MemoCategory,
    NotificationSetting,
    OAuthToken,
    UnrepliedItem,
    User,
)

# Alembic Config object
alembic_config = context.config

# Set up loggers from alembic.ini
if alembic_config.config_file_name is not None:
    fileConfig(alembic_config.config_file_name)

# Override sqlalchemy.url with the real DATABASE_URL from app config
alembic_config.set_main_option("sqlalchemy.url", app_config.DATABASE_URL)

# Target metadata for autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Generates SQL script without connecting to the database.
    """
    url = alembic_config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Creates an Engine and associates a connection with the context.
    """
    connectable = engine_from_config(
        alembic_config.get_section(alembic_config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
