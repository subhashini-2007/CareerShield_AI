"""Application configuration and environment settings."""

import logging
import os
import secrets
from pathlib import Path
from typing import List, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger("careershield.config")


class Settings(BaseSettings):
    """Configuration settings for CareerShield AI."""

    model_config = SettingsConfigDict(
        env_file=(
            str(Path(__file__).resolve().parent.parent.parent / ".env"),
            ".env",
        ),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Application Information
    APP_NAME: str = "CareerShield AI"
    APP_VERSION: str = "0.1.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Security
    SECRET_KEY: str = ""

    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Database Configuration (PostgreSQL default; SQLite allowed only if explicitly configured)
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/careershield_db"

    # ML Artifacts Location
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    MODEL_ARTIFACTS_DIR: str = "artifacts/models"

    # Privacy Settings
    ANONYMIZE_IPS: bool = True

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_database_url(cls, v: str) -> str:
        """Normalize database URL and enforce persistent PostgreSQL in production."""
        if isinstance(v, str):
            v_clean = v.strip()
            # Neon and Render often provide 'postgres://', which SQLAlchemy 2.0 rejects
            if v_clean.startswith("postgres://"):
                v_clean = "postgresql://" + v_clean[len("postgres://"):]

            # Strict production safety check:
            # Ephemeral SQLite is strictly forbidden in production to prevent silent data loss on Render
            env = os.getenv("APP_ENV", "development").lower()
            if env == "production":
                if v_clean.startswith("sqlite"):
                    raise ValueError(
                        "Production mode (APP_ENV=production) requires a persistent PostgreSQL database (Neon). "
                        "Ephemeral SQLite is strictly forbidden in production to prevent silent data loss."
                    )
                if "localhost" in v_clean or "127.0.0.1" in v_clean:
                    raise ValueError(
                        "Production mode (APP_ENV=production) requires a valid remote PostgreSQL connection string "
                        "(e.g., Neon PostgreSQL). Default localhost DATABASE_URL cannot be used in production."
                    )
            return v_clean
        return v

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        origins: List[str] = []
        if isinstance(v, str):
            v_stripped = v.strip()
            if v_stripped.startswith("[") and v_stripped.endswith("]"):
                # Handle JSON list string
                import json

                try:
                    parsed = json.loads(v_stripped)
                    if isinstance(parsed, list):
                        origins = [str(item).strip() for item in parsed if item]
                except Exception:
                    origins = [origin.strip() for origin in v_stripped.strip("[]").split(",") if origin.strip()]
            else:
                origins = [origin.strip() for origin in v_stripped.split(",") if origin.strip()]
        elif isinstance(v, list):
            origins = [str(item).strip() for item in v if item]
        else:
            origins = ["http://localhost:3000", "http://127.0.0.1:3000"]

        # Normalize: strip trailing slashes to guarantee exact Origin header matching
        normalized = [o.rstrip("/") for o in origins if o]
        final_origins = normalized if normalized else ["http://localhost:3000", "http://127.0.0.1:3000"]

        # Warn if production is missing a production domain
        env = os.getenv("APP_ENV", "development").lower()
        if env == "production":
            has_production_origin = any(
                not ("localhost" in o or "127.0.0.1" in o) for o in final_origins
            )
            if not has_production_origin:
                logger.warning(
                    "CORS_ORIGINS contains only localhost in production! "
                    "Browser requests from your Vercel deployment will be blocked until you configure "
                    "your live Vercel URL (e.g. https://careershield-ai.vercel.app) in CORS_ORIGINS."
                )

        return final_origins

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        # Check production constraints
        env = os.getenv("APP_ENV", "development").lower()
        if env == "production":
            if not v or len(v.strip()) < 32:
                raise ValueError(
                    "SECRET_KEY must be set in production with at least 32 characters."
                )
            return v
        # In non-production, generate an ephemeral secret if empty
        if not v or len(v.strip()) == 0:
            generated = secrets.token_urlsafe(32)
            logger.warning(
                "SECRET_KEY was not configured. Generated ephemeral random key for development session."
            )
            return generated
        return v

    @property
    def database_engine_name(self) -> str:
        """Extract database dialect without exposing credentials."""
        url = self.DATABASE_URL.lower()
        if url.startswith("postgresql") or url.startswith("postgres"):
            return "postgresql"
        elif url.startswith("sqlite"):
            return "sqlite"
        else:
            return url.split(":")[0] if ":" in url else "unknown"

    @property
    def is_sqlite(self) -> bool:
        return self.database_engine_name == "sqlite"

    @property
    def is_postgresql(self) -> bool:
        return self.database_engine_name == "postgresql"

    @property
    def model_artifacts_path(self) -> Path:
        """Absolute path to the artifacts/models directory."""
        path = self.BASE_DIR / self.MODEL_ARTIFACTS_DIR
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()
