"""Pydantic validation schemas for Analytics Dashboard and Model Transparency."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RiskCategoryStat(BaseModel):
    """Aggregate statistic for a single risk tier."""
    category: str = Field(..., description="LOW_RISK, NEEDS_CAUTION, or HIGH_RISK_INDICATORS")
    label: str = Field(..., description="Display label: Low Risk, Needs Caution, High Risk Indicators")
    count: int = Field(default=0, ge=0)
    percentage: float = Field(default=0.0, ge=0.0, le=100.0)
    color: str = Field(..., description="Hex color code for visualization")


class ScoreRangeStat(BaseModel):
    """Distribution of risk scores across standardized intervals."""
    range_label: str = Field(..., description="e.g. '0–20 (Minimal Risk)'")
    min_score: float
    max_score: float
    count: int = Field(default=0, ge=0)
    percentage: float = Field(default=0.0, ge=0.0, le=100.0)


class ChannelRiskStat(BaseModel):
    """Risk breakdown by communication channel."""
    channel: str = Field(..., description="Channel name: EMAIL, TELEGRAM, WHATSAPP, LINKEDIN, OFFICIAL_PORTAL, OTHER")
    count: int = Field(default=0, ge=0)
    percentage: float = Field(default=0.0, ge=0.0, le=100.0)
    average_risk_score: float = Field(default=0.0, ge=0.0, le=100.0)


class WarningIndicatorStat(BaseModel):
    """Frequency of specific warning categories detected across stored records."""
    category: str = Field(..., description="Warning category e.g. UPFRONT_FEE, DOMAIN_SPOOFING")
    title: str = Field(..., description="Representative title")
    severity: str = Field(..., description="CRITICAL, HIGH, MEDIUM, LOW")
    count: int = Field(default=0, ge=0)
    percentage: float = Field(default=0.0, ge=0.0, le=100.0)


class RecentAnalysisSummaryItem(BaseModel):
    """Sanitized, PII-free summary of recent analysis for dashboard activity tables."""
    id: str
    job_title: str
    company_name: str
    contact_channel: str
    final_risk_score: float
    risk_level: str
    requires_payment: bool
    payment_amount_claimed: Optional[float] = None
    created_at: Optional[str] = None


class AnalyticsSummaryResponse(BaseModel):
    """Complete aggregated metrics for the Analytics Dashboard."""
    total_analyses: int = Field(default=0, ge=0)
    average_risk_score: float = Field(default=0.0, ge=0.0, le=100.0)
    
    # Risk Tier Counts & Percentages
    high_risk_count: int = Field(default=0, ge=0)
    high_risk_percentage: float = Field(default=0.0, ge=0.0, le=100.0)
    caution_count: int = Field(default=0, ge=0)
    caution_percentage: float = Field(default=0.0, ge=0.0, le=100.0)
    low_risk_count: int = Field(default=0, ge=0)
    low_risk_percentage: float = Field(default=0.0, ge=0.0, le=100.0)
    
    # Financial Demands
    payment_demanded_count: int = Field(default=0, ge=0)
    payment_demanded_percentage: float = Field(default=0.0, ge=0.0, le=100.0)

    # Structured Distributions
    risk_distribution: List[RiskCategoryStat] = Field(default_factory=list)
    score_ranges: List[ScoreRangeStat] = Field(default_factory=list)
    channel_distribution: List[ChannelRiskStat] = Field(default_factory=list)
    top_warning_indicators: List[WarningIndicatorStat] = Field(default_factory=list)

    # Activity Stream
    recent_activity: List[RecentAnalysisSummaryItem] = Field(default_factory=list)


class RuleDefinition(BaseModel):
    """Specification of a deterministic detection rule in the heuristic engine."""
    rule_id: str
    name: str
    category: str
    severity: str
    risk_points: float
    impact_type: str = Field(default="PENALTY", description="PENALTY or MITIGATION")
    description: str
    detection_mechanism: str
    historical_triggers_count: int = Field(default=0, ge=0)
    trigger_percentage: float = Field(default=0.0, ge=0.0, le=100.0)


class MitigatingSignalDefinition(BaseModel):
    """Legitimacy signal that reduces calculated risk."""
    signal_id: str
    name: str
    point_reduction: float
    description: str
    detection_mechanism: str


class ScoreBandDefinition(BaseModel):
    """Classification boundary for risk scoring."""
    tier: str
    label: str
    min_score: float
    max_score: float
    description: str
    color: str


class OfflineBenchmarkMetrics(BaseModel):
    """Held-out offline evaluation benchmark metrics from historical training split."""
    dataset_name: str = Field(default="EMSCAD Dataset (Held-Out Test Split, N=3,023, random_state=42)")
    test_split_size: int = Field(default=3023, ge=0)
    roc_auc: float = Field(default=0.9628, ge=0.0, le=1.0)
    pr_auc: float = Field(default=0.7921, ge=0.0, le=1.0)
    fraud_precision: float = Field(default=70.07, ge=0.0, le=100.0)
    fraud_recall: float = Field(default=74.42, ge=0.0, le=100.0)
    threshold: float = Field(default=0.61, ge=0.0, le=1.0)
    caveat: str = Field(
        default="Historical offline benchmark on held-out test split, not live Indian scam prevalence."
    )


class ModelTransparencyResponse(BaseModel):
    """Full transparency report on the active heuristic engine and evaluation status."""
    engine_type: str = Field(default="Deterministic Heuristic Rules Engine")
    engine_version: str = Field(default="v1.0-rules-engine")
    total_rules_defined: int = Field(default=10)
    ml_model_status: str = Field(default="Untrained / Heuristic Mode Active")
    ml_metrics_available: bool = Field(default=False)
    ml_metrics_explanation: str = Field(
        default="Supervised ML evaluation metrics (Accuracy, Precision, Recall, F1, Confusion Matrix, ROC-AUC) "
                "are unavailable until a benchmarked, split-validated dataset is trained. Fabricating evaluation "
                "metrics without empirical model training violates CareerShield AI engineering principles."
    )
    total_evaluations_analyzed: int = Field(default=0, ge=0)
    score_calculation_formula: str
    score_bands: List[ScoreBandDefinition] = Field(default_factory=list)
    rules: List[RuleDefinition] = Field(default_factory=list)
    mitigating_signals: List[MitigatingSignalDefinition] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    benchmark_metrics: Optional[OfflineBenchmarkMetrics] = Field(default=None)
