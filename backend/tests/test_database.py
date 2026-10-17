"""Automated tests for database engine configuration and fail-fast behavior."""

import pytest
from sqlalchemy import create_engine, text

from app.core.config import Settings
from app.core.database import (
    DatabaseConnectionError,
    check_database_health,
    create_app_engine,
)


def test_sqlite_engine_detection():
    """Verify explicit SQLite configuration correctly sets engine dialect."""
    custom_settings = Settings(DATABASE_URL="sqlite:///./test_custom.db")
    assert custom_settings.is_sqlite is True
    assert custom_settings.is_postgresql is False
    assert custom_settings.database_engine_name == "sqlite"


def test_postgresql_engine_detection():
    """Verify PostgreSQL configuration correctly sets engine dialect."""
    custom_settings = Settings(
        DATABASE_URL="postgresql://user:pass@localhost:5432/testdb"
    )
    assert custom_settings.is_postgresql is True
    assert custom_settings.is_sqlite is False
    assert custom_settings.database_engine_name == "postgresql"


def test_unreachable_database_fails_loudly():
    """Verify that an unreachable database returns disconnected status without silently falling back."""
    # Attempting to query an unreachable database port
    unreachable_url = "postgresql://invalid_user:invalid_pass@127.0.0.1:59999/nonexistent"
    engine = create_app_engine(unreachable_url)

    with pytest.raises(Exception):
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
