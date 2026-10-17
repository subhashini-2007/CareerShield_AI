"""Pydantic validation schemas for Job Risk Analysis."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class WarningSignSchema(BaseModel):
    id: str = Field(..., description="Unique warning indicator ID")
    category: str = Field(..., description="Category: UPFRONT_FEE, DOMAIN_SPOOFING, CHANNEL_RISK, SALARY_ANOMALY, ZERO_INTERVIEW, PRESSURE_TACTIC, MISSING_INFO, OTHER")
    severity: str = Field(..., description="Severity level: CRITICAL, HIGH, MEDIUM, LOW")
    title: str = Field(..., description="Brief warning title")
    description: str = Field(..., description="Detailed explanation of the risk indicator")
    matched_text: Optional[str] = Field(None, description="Exact phrase or pattern extracted from input")


class EvidenceSnippetSchema(BaseModel):
    id: str = Field(..., description="Snippet identifier")
    text: str = Field(..., description="Matched text snippet")
    attribution: str = Field(default="heuristic_rule", description="Attribution source: heuristic_rule or ml_feature")
    impact_score: float = Field(..., description="Risk point contribution from this evidence")
    reason: str = Field(..., description="Why this evidence elevates or reduces risk")


class CompanyAssessmentSchema(BaseModel):
    domain_status: str = Field(..., description="verified_match, personal_domain, unverified_domain, or missing")
    is_known_firm: bool = Field(default=False, description="Whether the firm matches known Indian corporate benchmark")
    advisory_note: Optional[str] = Field(None, description="Company-specific recruitment advisory note")
    verified_url: Optional[str] = Field(None, description="Official career portal URL if known")


class JobAnalysisCreate(BaseModel):
    """Schema for submitting a job opportunity for risk analysis."""

    job_title: str = Field(..., min_length=2, max_length=255, description="Advertised job title")
    company_name: str = Field(..., min_length=2, max_length=255, description="Hiring company or organization name")
    recruiter_name: Optional[str] = Field(None, max_length=255, description="Recruiter contact person name")
    recruiter_email: Optional[str] = Field(None, max_length=255, description="Recruiter email address or contact handle")
    recruiter_phone: Optional[str] = Field(None, max_length=50, description="Recruiter phone or WhatsApp number")
    contact_channel: str = Field(
        default="EMAIL",
        description="Primary communication channel: EMAIL, TELEGRAM, WHATSAPP, LINKEDIN, OFFICIAL_PORTAL, OTHER"
    )
    job_description: str = Field(
        ...,
        min_length=15,
        max_length=20000,
        description="Full text of the job posting, offer letter, or recruiter message"
    )
    salary_offered: Optional[str] = Field(None, max_length=100, description="Advertised compensation claim")
    salary_frequency: Optional[str] = Field(default="ANNUAL", description="Frequency: MONTHLY, ANNUAL, PER_TASK, DAILY")
    location: Optional[str] = Field(None, max_length=150, description="Job location or Remote status")
    application_url: Optional[str] = Field(None, max_length=500, description="Job portal or company website URL")
    requires_payment: bool = Field(default=False, description="Whether the recruiter requested any fee or deposit")
    payment_amount_claimed: Optional[float] = Field(None, ge=0, description="Amount demanded in INR if applicable")
    payment_reason: Optional[str] = Field(None, max_length=255, description="Stated reason for payment: registration, training, kit, etc.")

    @field_validator("job_title", "company_name")
    @classmethod
    def strip_and_validate_non_empty(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Field cannot be empty or purely whitespace.")
        return clean

    @field_validator("contact_channel")
    @classmethod
    def validate_contact_channel(cls, v: str) -> str:
        valid_channels = {"EMAIL", "TELEGRAM", "WHATSAPP", "LINKEDIN", "OFFICIAL_PORTAL", "OTHER"}
        upper = v.strip().upper()
        if upper not in valid_channels:
            return "OTHER"
        return upper

    @field_validator("salary_frequency")
    @classmethod
    def validate_salary_frequency(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return "ANNUAL"
        valid_frequencies = {"MONTHLY", "ANNUAL", "PER_TASK", "DAILY"}
        upper = v.strip().upper()
        if upper not in valid_frequencies:
            return "ANNUAL"
        return upper


class JobAnalysisResponse(BaseModel):
    """Complete response schema for a job risk assessment."""

    id: str
    job_title: str
    company_name: str
    recruiter_name: Optional[str] = None
    recruiter_email: Optional[str] = None
    recruiter_phone: Optional[str] = None
    contact_channel: str
    job_description: str
    salary_offered: Optional[str] = None
    salary_frequency: Optional[str] = None
    location: Optional[str] = None
    application_url: Optional[str] = None
    requires_payment: bool
    payment_amount_claimed: Optional[float] = None
    payment_reason: Optional[str] = None

    # Risk Metrics
    ml_risk_score: float = Field(..., description="ML model text risk score (0.0 when untrained)")
    heuristic_risk_score: float = Field(..., description="Rules-based risk score (0-100)")
    final_risk_score: float = Field(..., description="Calibrated final risk score (0-100)")
    risk_level: str = Field(..., description="LOW_RISK, NEEDS_CAUTION, or HIGH_RISK_INDICATORS")
    confidence_score: float = Field(..., description="Confidence metric (0.0 to 1.0)")

    # Explainable Details
    warning_signs: List[WarningSignSchema] = Field(default_factory=list)
    evidence_snippets: List[EvidenceSnippetSchema] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    company_assessment: CompanyAssessmentSchema

    # Provenance
    model_version: str
    disclaimer: str = Field(
        default="Advisory assessment based on detected pattern indicators. Not definitive legal proof of fraud.",
        description="Standard Responsible AI disclaimer"
    )
    created_at: Optional[str] = None


class PaginatedJobAnalysisResponse(BaseModel):
    """Paginated list of historical analyses."""

    items: List[JobAnalysisResponse]
    total: int
    page: int
    page_size: int
    pages: int
