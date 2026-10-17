"""System health and diagnostic inspection endpoint."""

from datetime import datetime, timezone
import logging

from fastapi import APIRouter

from app.core.config import settings
from app.core.database import check_database_health
from app.ml.inference_service import get_ml_service
from app.schemas.health import (
    AppInfo,
    DatabaseHealth,
    HealthResponse,
    ModelHealth,
)

logger = logging.getLogger("careershield.health")
router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="System Health & Diagnostics",
    description="Check application status, active database engine connectivity, and ML model loaded status. Does not expose credentials.",
)
def get_system_health() -> HealthResponse:
    """Retrieve system diagnostics without exposing sensitive settings."""
    db_health = check_database_health()

    # Determine ML model status safely using the inference service
    try:
        ml_service = get_ml_service()
        is_model_present = ml_service.is_available
        model_version = ml_service.version if is_model_present else "not-loaded"
        model_status = "trained" if is_model_present else "not_trained"
    except Exception as exc:
        logger.warning("Error checking ML model health: %s", str(exc))
        is_model_present = False
        model_version = "not-loaded"
        model_status = "not_trained"

    overall_status = "ok" if db_health["connected"] else "degraded"

    return HealthResponse(
        status=overall_status,
        timestamp=datetime.now(timezone.utc),
        app=AppInfo(
            name=settings.APP_NAME,
            version=settings.APP_VERSION,
            environment=settings.APP_ENV,
        ),
        database=DatabaseHealth(
            connected=db_health["connected"],
            engine=db_health["engine"],
            latency_ms=db_health["latency_ms"],
            error=db_health["error"],
        ),
        model=ModelHealth(
            loaded=is_model_present,
            version=model_version,
            status=model_status,
        ),
    )
