"""SQLAlchemy ORM models for CareerShield AI.

Designed to be fully compatible with both PostgreSQL and SQLite.
Uses standard JSON, portable String(36) UUID representations, and timezone-aware DateTimes.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship
from sqlalchemy.types import JSON

from app.core.database import Base


def generate_uuid() -> str:
    """Generate a 36-character canonical UUID string."""
    return str(uuid.uuid4())


class JobAnalysis(Base):
    """Stores full analysis audit trail, scores, evidence, and recommendations."""

    __tablename__ = "job_analyses"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    job_title = Column(String(255), nullable=False)
    company_name = Column(String(255), nullable=False, index=True)
    recruiter_name = Column(String(255), nullable=True)
    recruiter_email = Column(String(255), nullable=True)
    recruiter_phone = Column(String(50), nullable=True)
    contact_channel = Column(String(50), default="EMAIL", nullable=False)
    job_description = Column(Text, nullable=False)
    salary_offered = Column(String(100), nullable=True)
    salary_frequency = Column(String(20), default="ANNUAL", nullable=True)
    location = Column(String(150), nullable=True)
    application_url = Column(String(500), nullable=True)

    # Specific Risk Factors
    requires_payment = Column(Boolean, default=False, nullable=False)
    payment_amount_claimed = Column(Float, nullable=True)
    payment_reason = Column(String(255), nullable=True)

    # Distinct Risk Scoring Breakdown
    ml_risk_score = Column(Float, default=0.0, nullable=False)
    heuristic_risk_score = Column(Float, default=0.0, nullable=False)
    final_risk_score = Column(Float, default=0.0, nullable=False)
    risk_level = Column(String(30), default="LOW_RISK", nullable=False)  # LOW_RISK, NEEDS_CAUTION, HIGH_RISK_INDICATORS
    confidence_score = Column(Float, default=0.0, nullable=False)

    # Explainable AI & Structured Details
    warning_signs = Column(JSON, default=list, nullable=False)
    evidence_snippets = Column(JSON, default=list, nullable=False)
    recommendations = Column(JSON, default=list, nullable=False)
    company_assessment = Column(JSON, default=dict, nullable=False)

    # Provenance & Audit
    model_version = Column(String(50), default="v1.0-rules-only", nullable=False)
    client_ip_hash = Column(String(64), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    # Relationships
    feedbacks = relationship(
        "AnalysisFeedback",
        back_populates="analysis",
        cascade="all, delete-orphan",
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to safe dictionary."""
        return {
            "id": self.id,
            "job_title": self.job_title,
            "company_name": self.company_name,
            "recruiter_name": self.recruiter_name,
            "recruiter_email": self.recruiter_email,
            "recruiter_phone": self.recruiter_phone,
            "contact_channel": self.contact_channel,
            "job_description": self.job_description,
            "salary_offered": self.salary_offered,
            "salary_frequency": self.salary_frequency,
            "location": self.location,
            "application_url": self.application_url,
            "requires_payment": self.requires_payment,
            "payment_amount_claimed": self.payment_amount_claimed,
            "payment_reason": self.payment_reason,
            "ml_risk_score": self.ml_risk_score,
            "heuristic_risk_score": self.heuristic_risk_score,
            "final_risk_score": self.final_risk_score,
            "risk_level": self.risk_level,
            "confidence_score": self.confidence_score,
            "warning_signs": self.warning_signs or [],
            "evidence_snippets": self.evidence_snippets or [],
            "recommendations": self.recommendations or [],
            "company_assessment": self.company_assessment or {},
            "model_version": self.model_version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AnalysisFeedback(Base):
    """User corrections and validation feedback on risk analysis results."""

    __tablename__ = "analysis_feedbacks"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    analysis_id = Column(
        String(36),
        ForeignKey("job_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_verdict = Column(String(50), nullable=False)  # ACCURATE, TOO_STRICT, MISSED_SCAM, INCONCLUSIVE
    actual_outcome = Column(String(50), nullable=True)  # CONFIRMED_LEGITIMATE, CONFIRMED_SCAM, UNRESOLVED
    comments = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    analysis = relationship("JobAnalysis", back_populates="feedbacks")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "analysis_id": self.analysis_id,
            "user_verdict": self.user_verdict,
            "actual_outcome": self.actual_outcome,
            "comments": self.comments,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class CompanyBenchmark(Base):
    """Ground-truth benchmark of verified employers and known legitimate domains."""

    __tablename__ = "known_company_benchmarks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    canonical_name = Column(String(255), unique=True, nullable=False, index=True)
    official_career_url = Column(String(255), nullable=False)
    legitimate_domains = Column(JSON, nullable=False)  # e.g., ["tcs.com", "careers.tcs.com"]
    never_charges_fees_policy = Column(Boolean, default=True, nullable=False)
    official_hr_email_pattern = Column(String(255), nullable=True)
    frequently_spoofed = Column(Boolean, default=True, nullable=False)
    advisory_note = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "canonical_name": self.canonical_name,
            "official_career_url": self.official_career_url,
            "legitimate_domains": self.legitimate_domains or [],
            "never_charges_fees_policy": self.never_charges_fees_policy,
            "official_hr_email_pattern": self.official_hr_email_pattern,
            "frequently_spoofed": self.frequently_spoofed,
            "advisory_note": self.advisory_note,
        }


class ModelEvalMetric(Base):
    """Persistent log of real evaluated machine learning model runs."""

    __tablename__ = "model_eval_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_version = Column(String(50), unique=True, nullable=False, index=True)
    algorithm_name = Column(String(100), nullable=False)
    dataset_records_count = Column(Integer, nullable=False)
    test_accuracy = Column(Float, nullable=False)
    precision_macro = Column(Float, nullable=False)
    recall_macro = Column(Float, nullable=False)
    f1_macro = Column(Float, nullable=False)
    roc_auc = Column(Float, nullable=False)
    confusion_matrix = Column(JSON, nullable=False)  # {"tn": ..., "fp": ..., "fn": ..., "tp": ...}
    feature_importance_top20 = Column(JSON, nullable=False)
    trained_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "model_version": self.model_version,
            "algorithm_name": self.algorithm_name,
            "dataset_records_count": self.dataset_records_count,
            "test_accuracy": self.test_accuracy,
            "precision_macro": self.precision_macro,
            "recall_macro": self.recall_macro,
            "f1_macro": self.f1_macro,
            "roc_auc": self.roc_auc,
            "confusion_matrix": self.confusion_matrix,
            "feature_importance_top20": self.feature_importance_top20,
            "trained_at": self.trained_at.isoformat() if self.trained_at else None,
        }
