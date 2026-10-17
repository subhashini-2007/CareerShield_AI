"""API endpoints for job risk analysis and audit history."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.analysis import (
    JobAnalysisCreate,
    JobAnalysisResponse,
    PaginatedJobAnalysisResponse,
)
from app.services.analyzer_service import (
    get_analysis_by_id,
    list_analyses,
    process_and_save_analysis,
)

router = APIRouter()


@router.post(
    "/analyze",
    response_model=JobAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Analyze Job Opportunity Risk",
    description="Submits a job opportunity to the heuristic safety engine, evaluates risk indicators, persists the assessment, and returns an explainable report.",
)
def analyze_job_opportunity(
    payload: JobAnalysisCreate,
    request: Request,
    db: Session = Depends(get_db),
) -> JobAnalysisResponse:
    """Analyze a job opportunity for potential recruitment risks and upfront fee demands."""
    client_ip = request.client.host if request.client else None
    try:
        response = process_and_save_analysis(payload, db, client_ip)
        return response
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while evaluating the job posting: {str(exc)}",
        )


@router.get(
    "/analyses",
    response_model=PaginatedJobAnalysisResponse,
    summary="List Analysis Audit History",
    description="Retrieve paginated list of previously verified job opportunity analyses with optional filtering by risk level or search term.",
)
def get_analyses_history(
    page: int = Query(default=1, ge=1, description="Page number starting at 1"),
    page_size: int = Query(default=10, ge=1, le=100, description="Items per page"),
    risk_level: Optional[str] = Query(default=None, description="Filter by risk tier: LOW_RISK, NEEDS_CAUTION, HIGH_RISK_INDICATORS"),
    search: Optional[str] = Query(default=None, description="Search term matching company name or job title"),
    db: Session = Depends(get_db),
) -> PaginatedJobAnalysisResponse:
    """Query stored job opportunity analyses from SQLite database."""
    return list_analyses(
        db=db,
        page=page,
        page_size=page_size,
        risk_level=risk_level,
        search=search,
    )


@router.get(
    "/analyses/{analysis_id}",
    response_model=JobAnalysisResponse,
    summary="Get Specific Analysis Report",
    description="Fetch complete assessment record, detected indicators, and recommendations for a specific analysis ID.",
)
def get_analysis_detail(
    analysis_id: str,
    db: Session = Depends(get_db),
) -> JobAnalysisResponse:
    """Retrieve full details of an analysis by its UUID."""
    record = get_analysis_by_id(db, analysis_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis with ID '{analysis_id}' was not found.",
        )
    return record
