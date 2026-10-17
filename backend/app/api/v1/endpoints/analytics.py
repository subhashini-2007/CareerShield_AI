"""API endpoints for dashboard analytics and model transparency."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.analytics import (
    AnalyticsSummaryResponse,
    ModelTransparencyResponse,
)
from app.services.analytics_service import (
    get_analytics_summary,
    get_model_transparency,
)

router = APIRouter()


@router.get(
    "/summary",
    response_model=AnalyticsSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Analytics Dashboard Summary",
    description=(
        "Returns database-backed recruitment risk statistics, risk category distributions, "
        "score histograms, channel risk breakdown, top warning indicators, and recent activity."
    ),
)
def get_analytics_dashboard_summary(
    db: Session = Depends(get_db),
) -> AnalyticsSummaryResponse:
    """Compute and return aggregated metrics for the analytics dashboard."""
    return get_analytics_summary(db=db)


@router.get(
    "/model-transparency",
    response_model=ModelTransparencyResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Heuristic Model Transparency & Evaluation Status",
    description=(
        "Returns active heuristic rule definitions, risk points, mitigation signals, "
        "operational limitations, score calibration formula, and live database trigger frequencies."
    ),
)
def get_heuristic_model_transparency(
    db: Session = Depends(get_db),
) -> ModelTransparencyResponse:
    """Return transparent rule specifications and live database trigger statistics."""
    return get_model_transparency(db=db)
