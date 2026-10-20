"""SQLAlchemy database connection management and health diagnostics."""

import logging
import os
import time
from typing import Any, Dict

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings

logger = logging.getLogger("careershield.database")


class DatabaseConnectionError(RuntimeError):
    """Raised when the explicitly configured database cannot be reached."""
    pass


# Engine instantiation based on explicit DATABASE_URL
def create_app_engine(database_url: str):
    connect_args: Dict[str, Any] = {}
    engine_kwargs: Dict[str, Any] = {}

    if settings.is_sqlite:
        connect_args["check_same_thread"] = False
    else:
        # Check if running in a serverless environment (e.g. Vercel)
        is_serverless = bool(
            os.getenv("VERCEL")
            or os.getenv("AWS_LAMBDA_FUNCTION_NAME")
            or os.getenv("DB_POOL_NULL", "").lower() in ("true", "1")
        )
        if is_serverless:
            # Serverless functions are stateless: avoid holding open pool connections
            engine_kwargs["poolclass"] = NullPool
        else:
            # Managed PostgreSQL (Neon / Render / production)
            # pool_recycle=300 aligns with Neon's 5-minute auto-suspend lifecycle
            engine_kwargs["pool_pre_ping"] = True
            engine_kwargs["pool_size"] = 5
            engine_kwargs["max_overflow"] = 10
            engine_kwargs["pool_recycle"] = 300

    return create_engine(
        database_url,
        connect_args=connect_args,
        **engine_kwargs,
    )


engine = create_app_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def check_database_health() -> Dict[str, Any]:
    """Inspect database connectivity and latency without exposing credentials."""
    start_time = time.time()
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        latency_ms = round((time.time() - start_time) * 1000, 2)
        return {
            "connected": True,
            "engine": settings.database_engine_name,
            "latency_ms": latency_ms,
            "error": None,
        }
    except Exception as exc:
        latency_ms = round((time.time() - start_time) * 1000, 2)
        # Log clean error without exposing full connection string
        logger.error(f"Database health check failed for {settings.database_engine_name}: {exc}")
        return {
            "connected": False,
            "engine": settings.database_engine_name,
            "latency_ms": latency_ms,
            "error": "Database connection refused or unreachable. Check credentials and server status.",
        }


def verify_database_connection() -> None:
    """
    Explicitly test database connection.
    Fails loudly if unreachable; NEVER silently falls back to another engine.
    """
    health = check_database_health()
    if not health["connected"]:
        raise DatabaseConnectionError(
            f"Configured database engine '{settings.database_engine_name}' is unreachable: {health['error']}. "
            f"Ensure PostgreSQL is running or verify your explicit DATABASE_URL."
        )
