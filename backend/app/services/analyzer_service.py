"""Analyzer service managing risk assessment, persistence, and querying."""

import hashlib
import math
from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import JobAnalysis
from app.ml.inference_service import combine_evaluations, get_ml_service
from app.ml.rules_engine import evaluate_job_risk
from app.schemas.analysis import (
    CompanyAssessmentSchema,
    EvidenceSnippetSchema,
    JobAnalysisCreate,
    JobAnalysisResponse,
    PaginatedJobAnalysisResponse,
    WarningSignSchema,
)

STANDARD_DISCLAIMER = (
    "Advisory assessment based on detected pattern indicators. Not definitive legal proof of fraud."
)


def _hash_client_ip(client_ip: Optional[str]) -> Optional[str]:
    """Anonymously hash IP address for basic rate-limiting/audit without storing raw PII."""
    if not client_ip or not settings.ANONYMIZE_IPS:
        return None
    salt = settings.SECRET_KEY[:16] if settings.SECRET_KEY else "careershield_salt"
    return hashlib.sha256(f"{client_ip}:{salt}".encode()).hexdigest()[:32]


def _model_to_response(analysis: JobAnalysis) -> JobAnalysisResponse:
    """Transform JobAnalysis database entity into validated JobAnalysisResponse."""
    warning_signs = [
        WarningSignSchema(**w) if isinstance(w, dict) else w
        for w in (analysis.warning_signs or [])
    ]
    evidence_snippets = [
        EvidenceSnippetSchema(**e) if isinstance(e, dict) else e
        for e in (analysis.evidence_snippets or [])
    ]
    company_assessment = (
        CompanyAssessmentSchema(**analysis.company_assessment)
        if isinstance(analysis.company_assessment, dict)
        else CompanyAssessmentSchema(domain_status="missing", is_known_firm=False)
    )

    return JobAnalysisResponse(
        id=analysis.id,
        job_title=analysis.job_title,
        company_name=analysis.company_name,
        recruiter_name=analysis.recruiter_name,
        recruiter_email=analysis.recruiter_email,
        recruiter_phone=analysis.recruiter_phone,
        contact_channel=analysis.contact_channel,
        job_description=analysis.job_description,
        salary_offered=analysis.salary_offered,
        salary_frequency=analysis.salary_frequency,
        location=analysis.location,
        application_url=analysis.application_url,
        requires_payment=analysis.requires_payment,
        payment_amount_claimed=analysis.payment_amount_claimed,
        payment_reason=analysis.payment_reason,
        ml_risk_score=analysis.ml_risk_score,
        heuristic_risk_score=analysis.heuristic_risk_score,
        final_risk_score=analysis.final_risk_score,
        risk_level=analysis.risk_level,
        confidence_score=analysis.confidence_score,
        warning_signs=warning_signs,
        evidence_snippets=evidence_snippets,
        recommendations=analysis.recommendations or [],
        company_assessment=company_assessment,
        model_version=analysis.model_version,
        disclaimer=STANDARD_DISCLAIMER,
        created_at=analysis.created_at.isoformat() if analysis.created_at else None,
    )


def process_and_save_analysis(
    payload: JobAnalysisCreate,
    db: Session,
    client_ip: Optional[str] = None,
) -> JobAnalysisResponse:
    """
    Run risk assessment on input, persist analysis to database, and return formatted response.
    
    1. Evaluates deterministic safety rules (authoritative primary safeguard).
    2. Runs isolated ML baseline model as a supplementary advisory signal.
    3. Combines signals using an asymmetric rule-dominant strategy.
    4. Persists the analysis audit record to the database.
    """
    payload_dict = payload.model_dump()

    # 1. Evaluate risk using heuristic rules engine (authoritative primary mechanism)
    heuristic_eval = evaluate_job_risk(payload_dict)

    # 2. Run isolated ML inference as a supplementary advisory signal
    ml_service = get_ml_service()
    ml_result = ml_service.predict(payload_dict)

    # 3. Combine scores: deterministic rules dominate; ML provides bounded advisory lift
    evaluation = combine_evaluations(heuristic_eval, ml_result)

    # 2. Persist to database
    ip_hash = _hash_client_ip(client_ip)

    analysis_record = JobAnalysis(
        job_title=payload.job_title,
        company_name=payload.company_name,
        recruiter_name=payload.recruiter_name,
        recruiter_email=payload.recruiter_email,
        recruiter_phone=payload.recruiter_phone,
        contact_channel=payload.contact_channel,
        job_description=payload.job_description,
        salary_offered=payload.salary_offered,
        salary_frequency=payload.salary_frequency,
        location=payload.location,
        application_url=payload.application_url,
        requires_payment=payload.requires_payment,
        payment_amount_claimed=payload.payment_amount_claimed,
        payment_reason=payload.payment_reason,
        ml_risk_score=evaluation["ml_risk_score"],
        heuristic_risk_score=evaluation["heuristic_risk_score"],
        final_risk_score=evaluation["final_risk_score"],
        risk_level=evaluation["risk_level"],
        confidence_score=evaluation["confidence_score"],
        warning_signs=evaluation["warning_signs"],
        evidence_snippets=evaluation["evidence_snippets"],
        recommendations=evaluation["recommendations"],
        company_assessment=evaluation["company_assessment"],
        model_version=evaluation["model_version"],
        client_ip_hash=ip_hash,
    )

    db.add(analysis_record)
    db.commit()
    db.refresh(analysis_record)

    return _model_to_response(analysis_record)


def list_analyses(
    db: Session,
    page: int = 1,
    page_size: int = 10,
    risk_level: Optional[str] = None,
    search: Optional[str] = None,
) -> PaginatedJobAnalysisResponse:
    """
    Query historical analyses from database with pagination and search filters.
    """
    page = max(1, page)
    page_size = max(1, min(page_size, 100))

    query = db.query(JobAnalysis)

    if risk_level and risk_level.upper() not in {"ALL", ""}:
        query = query.filter(JobAnalysis.risk_level == risk_level.upper())

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                JobAnalysis.company_name.ilike(term),
                JobAnalysis.job_title.ilike(term),
            )
        )

    total = query.count()
    pages = max(1, math.ceil(total / page_size))

    records = (
        query.order_by(JobAnalysis.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = [_model_to_response(record) for record in records]

    return PaginatedJobAnalysisResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


def get_analysis_by_id(db: Session, analysis_id: str) -> Optional[JobAnalysisResponse]:
    """
    Fetch a single analysis record by UUID.
    """
    record = db.query(JobAnalysis).filter(JobAnalysis.id == analysis_id).first()
    if not record:
        return None
    return _model_to_response(record)
