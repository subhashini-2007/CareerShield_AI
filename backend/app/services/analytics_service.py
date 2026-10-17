"""Analytics service calculating database-backed statistics and model transparency."""

import math
from typing import Any, Dict, List, Optional
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.db.models import JobAnalysis
from app.ml.inference_service import get_ml_service
from app.schemas.analytics import (
    AnalyticsSummaryResponse,
    ChannelRiskStat,
    MitigatingSignalDefinition,
    ModelTransparencyResponse,
    OfflineBenchmarkMetrics,
    RecentAnalysisSummaryItem,
    RiskCategoryStat,
    RuleDefinition,
    ScoreBandDefinition,
    ScoreRangeStat,
    WarningIndicatorStat,
)

# Canonical rule catalog matching backend/app/ml/rules_engine.py
CANONICAL_RULES = [
    {
        "rule_id": "R1_UPFRONT_FEE_DIRECT",
        "name": "Direct Upfront Payment or Deposit Demand",
        "category": "UPFRONT_FEE",
        "severity": "CRITICAL",
        "risk_points": 55.0,
        "impact_type": "PENALTY",
        "description": "Recruiter explicitly requests money for application, training, registration, or kit deposit.",
        "detection_mechanism": "Direct payment flag 'requires_payment == True' or non-zero payment amount claimed.",
        "match_category": "UPFRONT_FEE",
        "match_substring": "Demands Upfront Payment",
    },
    {
        "rule_id": "R2_UPFRONT_FEE_KEYWORD",
        "name": "Job Description Mentions Upfront Fee or Deposit",
        "category": "UPFRONT_FEE",
        "severity": "CRITICAL",
        "risk_points": 50.0,
        "impact_type": "PENALTY",
        "description": "Job text contains fee-related keywords such as registration charges, refundable laptop deposits, or verification kit fees.",
        "detection_mechanism": "Regex pattern scan against FEE_PATTERNS in job description text.",
        "match_category": "UPFRONT_FEE",
        "match_substring": "Mentions Upfront Payment",
    },
    {
        "rule_id": "R3_DOMAIN_SPOOFING_FREE_MAIL",
        "name": "Free Webmail Spoofing Top Indian Tech Employer",
        "category": "DOMAIN_SPOOFING",
        "severity": "CRITICAL",
        "risk_points": 40.0,
        "impact_type": "PENALTY",
        "description": "Recruiter uses personal free webmail (@gmail, @yahoo) while claiming to hire on behalf of top tech MNCs (TCS, Infosys, Wipro, etc.).",
        "detection_mechanism": "Email domain matched against FREE_EMAIL_DOMAINS and KNOWN_TECH_EMPLOYERS corporate registry.",
        "match_category": "DOMAIN_SPOOFING",
        "match_substring": "Free Email Used to Impersonate",
    },
    {
        "rule_id": "R4_CHANNEL_TELEGRAM",
        "name": "Recruitment Conducted via Telegram",
        "category": "CHANNEL_RISK",
        "severity": "HIGH",
        "risk_points": 30.0,
        "impact_type": "PENALTY",
        "description": "Recruitment communication initiated or managed over Telegram channels or bots, common vectors for untraceable task schemes.",
        "detection_mechanism": "Contact channel set to 'TELEGRAM' or recruiter handle referencing t.me / Telegram bot.",
        "match_category": "CHANNEL_RISK",
        "match_substring": "Telegram",
    },
    {
        "rule_id": "R5_TASK_SCAM_PATTERNS",
        "name": "Task-Based High-Return Scheme or Daily Payout",
        "category": "SALARY_ANOMALY",
        "severity": "HIGH",
        "risk_points": 30.0,
        "impact_type": "PENALTY",
        "description": "Advertising exorbitant daily payouts for simple social media liking, subscribing, or data entry typing tasks.",
        "detection_mechanism": "Regex pattern scan against TASK_SCAM_PATTERNS (e.g., 'like youtube videos', 'daily payout of Rs').",
        "match_category": "SALARY_ANOMALY",
        "match_substring": "Task-Based",
    },
    {
        "rule_id": "R6_DOMAIN_SPOOFING_UNVERIFIED",
        "name": "Unverified Domain for Known Corporate Employer",
        "category": "DOMAIN_SPOOFING",
        "severity": "HIGH",
        "risk_points": 25.0,
        "impact_type": "PENALTY",
        "description": "Recruiter email domain does not match the official authorized career domains of the claimed recognized employer.",
        "detection_mechanism": "Email domain comparison against KNOWN_TECH_EMPLOYERS authorized domain whitelist.",
        "match_category": "DOMAIN_SPOOFING",
        "match_substring": "Unverified Email Domain",
    },
    {
        "rule_id": "R7_CHANNEL_WHATSAPP",
        "name": "Informal Hiring Communication via WhatsApp",
        "category": "CHANNEL_RISK",
        "severity": "MEDIUM",
        "risk_points": 20.0,
        "impact_type": "PENALTY",
        "description": "Job offer or interview discussions conducted solely over WhatsApp without verified corporate application links or official ATS.",
        "detection_mechanism": "Contact channel set to 'WHATSAPP'.",
        "match_category": "CHANNEL_RISK",
        "match_substring": "WhatsApp",
    },
    {
        "rule_id": "R8_PRESSURE_URGENCY",
        "name": "Artificial Urgency or Zero-Interview Guaranteed Selection",
        "category": "PRESSURE_TACTIC",
        "severity": "MEDIUM",
        "risk_points": 20.0,
        "impact_type": "PENALTY",
        "description": "Uses artificial urgency ('limited seats left', 'immediate offer today') or guarantees selection without interview to force quick decisions.",
        "detection_mechanism": "Regex pattern scan against PRESSURE_PATTERNS (e.g. 'direct selection', 'no interview').",
        "match_category": "PRESSURE_TACTIC",
        "match_substring": "Artificial Urgency",
    },
    {
        "rule_id": "R9_DOMAIN_PERSONAL_GENERAL",
        "name": "Recruiter Using Personal Webmail Domain",
        "category": "DOMAIN_SPOOFING",
        "severity": "MEDIUM",
        "risk_points": 15.0,
        "impact_type": "PENALTY",
        "description": "Recruiter uses personal webmail (@gmail, @yahoo) for general corporate hiring where organizational email is expected.",
        "detection_mechanism": "Recruiter email domain matched against FREE_EMAIL_DOMAINS without known employer match.",
        "match_category": "DOMAIN_SPOOFING",
        "match_substring": "Personal Webmail Domain",
    },
    {
        "rule_id": "R10_MISSING_CONTACT_INFO",
        "name": "Missing Verifiable Website and Email Contact",
        "category": "MISSING_INFO",
        "severity": "LOW",
        "risk_points": 15.0,
        "impact_type": "PENALTY",
        "description": "Job opportunity lacks both an official career website link and a recruiter email address for independent due diligence.",
        "detection_mechanism": "Absence of valid HTTP(S) application URL and absence of valid recruiter email address.",
        "match_category": "MISSING_INFO",
        "match_substring": "Missing",
    },
]

MITIGATING_SIGNALS = [
    MitigatingSignalDefinition(
        signal_id="M1_OFFICIAL_DOMAIN",
        name="Verified Official Corporate Domain",
        point_reduction=15.0,
        description="Recruiter email domain verified to match official corporate registry (e.g. @tcs.com, @infosys.com).",
        detection_mechanism="Exact match or subdomain match against KNOWN_TECH_EMPLOYERS authorized domain registry.",
    ),
    MitigatingSignalDefinition(
        signal_id="M2_STRUCTURED_INTERVIEWS",
        name="Structured Technical Interview Process",
        point_reduction=8.0,
        description="Job posting describes standard multi-stage evaluation (coding round, panel interview, background verification).",
        detection_mechanism="Regex pattern match against LEGITIMACY_PATTERNS.",
    ),
    MitigatingSignalDefinition(
        signal_id="M3_STATUTORY_BENEFITS",
        name="Recognized Statutory Employee Benefits",
        point_reduction=8.0,
        description="Compensation terms explicitly reference Provident Fund (PF), Gratuity, and medical/health insurance.",
        detection_mechanism="Regex pattern match against statutory benefits keywords.",
    ),
]

SCORE_BANDS = [
    ScoreBandDefinition(
        tier="LOW_RISK",
        label="Low Risk",
        min_score=0.0,
        max_score=34.0,
        description="Standard corporate hiring patterns detected; official communication channels verified.",
        color="#10B981",
    ),
    ScoreBandDefinition(
        tier="NEEDS_CAUTION",
        label="Needs Caution",
        min_score=34.1,
        max_score=64.9,
        description="Unverified recruiter details, personal webmail, or informal channels warrant candidate due diligence.",
        color="#F59E0B",
    ),
    ScoreBandDefinition(
        tier="HIGH_RISK_INDICATORS",
        label="High Risk Indicators",
        min_score=65.0,
        max_score=100.0,
        description="Critical risk flags detected: upfront fee requests, top-firm domain spoofing, or task scam guarantees.",
        color="#EF4444",
    ),
]

LIMITATIONS = [
    "Deterministic keyword and regex detection is limited to known vocabulary patterns; novel evasion slang or emerging scam variations may evade static rules.",
    "Legitimate early-stage startups, individual consultants, or academic labs operating via personal webmail (@gmail.com) may be flagged with 'Needs Caution' due to lack of corporate domain ownership.",
    "The system does not perform real-time external WHOIS or live DNS lookups in offline environments; domain authenticity is verified against our curated corporate benchmark registry.",
    "Absence of risk flags does not constitute a legal guarantee of legitimacy. Job seekers must conduct independent due diligence via official portals before signing contracts or sharing identity documents.",
]


def get_analytics_summary(db: Session) -> AnalyticsSummaryResponse:
    """
    Compute comprehensive, database-backed recruitment risk statistics.
    Returns safe default figures when database contains zero records.
    """
    total_analyses = db.query(JobAnalysis).count()

    # Default empty response structure
    if total_analyses == 0:
        return AnalyticsSummaryResponse(
            total_analyses=0,
            average_risk_score=0.0,
            high_risk_count=0,
            high_risk_percentage=0.0,
            caution_count=0,
            caution_percentage=0.0,
            low_risk_count=0,
            low_risk_percentage=0.0,
            payment_demanded_count=0,
            payment_demanded_percentage=0.0,
            risk_distribution=[
                RiskCategoryStat(category="LOW_RISK", label="Low Risk", count=0, percentage=0.0, color="#10B981"),
                RiskCategoryStat(category="NEEDS_CAUTION", label="Needs Caution", count=0, percentage=0.0, color="#F59E0B"),
                RiskCategoryStat(category="HIGH_RISK_INDICATORS", label="High Risk Indicators", count=0, percentage=0.0, color="#EF4444"),
            ],
            score_ranges=[
                ScoreRangeStat(range_label="0–20 (Minimal)", min_score=0.0, max_score=20.0, count=0, percentage=0.0),
                ScoreRangeStat(range_label="21–40 (Low)", min_score=20.1, max_score=40.0, count=0, percentage=0.0),
                ScoreRangeStat(range_label="41–60 (Moderate)", min_score=40.1, max_score=60.0, count=0, percentage=0.0),
                ScoreRangeStat(range_label="61–80 (Elevated)", min_score=60.1, max_score=80.0, count=0, percentage=0.0),
                ScoreRangeStat(range_label="81–100 (Critical)", min_score=80.1, max_score=100.0, count=0, percentage=0.0),
            ],
            channel_distribution=[],
            top_warning_indicators=[],
            recent_activity=[],
        )

    # 1. Average score
    avg_score = db.query(func.avg(JobAnalysis.final_risk_score)).scalar() or 0.0
    average_risk_score = round(float(avg_score), 1)

    # 2. Risk level counts
    low_count = db.query(JobAnalysis).filter(JobAnalysis.risk_level == "LOW_RISK").count()
    caution_count = db.query(JobAnalysis).filter(JobAnalysis.risk_level == "NEEDS_CAUTION").count()
    high_count = db.query(JobAnalysis).filter(JobAnalysis.risk_level == "HIGH_RISK_INDICATORS").count()

    low_pct = round((low_count / total_analyses) * 100.0, 1)
    caution_pct = round((caution_count / total_analyses) * 100.0, 1)
    high_pct = round((high_count / total_analyses) * 100.0, 1)

    risk_distribution = [
        RiskCategoryStat(category="LOW_RISK", label="Low Risk", count=low_count, percentage=low_pct, color="#10B981"),
        RiskCategoryStat(category="NEEDS_CAUTION", label="Needs Caution", count=caution_count, percentage=caution_pct, color="#F59E0B"),
        RiskCategoryStat(category="HIGH_RISK_INDICATORS", label="High Risk Indicators", count=high_count, percentage=high_pct, color="#EF4444"),
    ]

    # 3. Payment demand statistics
    payment_count = db.query(JobAnalysis).filter(
        or_(
            JobAnalysis.requires_payment == True,
            JobAnalysis.payment_amount_claimed > 0,
        )
    ).count()
    payment_pct = round((payment_count / total_analyses) * 100.0, 1)

    # 4. Score range distribution
    all_scores = [r[0] for r in db.query(JobAnalysis.final_risk_score).all() if r[0] is not None]
    range_defs = [
        ("0–20 (Minimal)", 0.0, 20.0),
        ("21–40 (Low)", 20.1, 40.0),
        ("41–60 (Moderate)", 40.1, 60.0),
        ("61–80 (Elevated)", 60.1, 80.0),
        ("81–100 (Critical)", 80.1, 100.0),
    ]

    score_ranges: List[ScoreRangeStat] = []
    for label, min_s, max_s in range_defs:
        in_range = sum(1 for s in all_scores if min_s <= s <= max_s)
        pct = round((in_range / total_analyses) * 100.0, 1)
        score_ranges.append(ScoreRangeStat(
            range_label=label,
            min_score=min_s,
            max_score=max_s,
            count=in_range,
            percentage=pct,
        ))

    # 5. Channel risk distribution
    channel_query = (
        db.query(
            JobAnalysis.contact_channel,
            func.count(JobAnalysis.id).label("c_count"),
            func.avg(JobAnalysis.final_risk_score).label("c_avg"),
        )
        .group_by(JobAnalysis.contact_channel)
        .all()
    )

    channel_distribution: List[ChannelRiskStat] = []
    for ch, c_cnt, c_avg in channel_query:
        channel_name = (ch or "OTHER").upper()
        avg_val = round(float(c_avg or 0.0), 1)
        channel_distribution.append(ChannelRiskStat(
            channel=channel_name,
            count=c_cnt,
            percentage=round((c_cnt / total_analyses) * 100.0, 1),
            average_risk_score=avg_val,
        ))
    channel_distribution.sort(key=lambda x: x.count, reverse=True)

    # 6. Aggregated warning indicators from stored records
    warning_records = db.query(JobAnalysis.warning_signs).all()
    category_counts: Dict[str, int] = {}
    category_titles: Dict[str, str] = {}
    category_severities: Dict[str, str] = {}

    for (w_list,) in warning_records:
        if isinstance(w_list, list):
            # Track unique categories per analysis to calculate % of analyses affected
            seen_categories = set()
            for w in w_list:
                if isinstance(w, dict):
                    cat = w.get("category", "OTHER")
                    title = w.get("title", cat.replace("_", " ").title())
                    severity = w.get("severity", "MEDIUM")
                    
                    category_counts[cat] = category_counts.get(cat, 0) + 1
                    if cat not in category_titles:
                        category_titles[cat] = title
                        category_severities[cat] = severity

    top_warning_indicators: List[WarningIndicatorStat] = []
    for cat, count in sorted(category_counts.items(), key=lambda item: item[1], reverse=True):
        top_warning_indicators.append(WarningIndicatorStat(
            category=cat,
            title=category_titles.get(cat, cat.replace("_", " ").title()),
            severity=category_severities.get(cat, "MEDIUM"),
            count=count,
            percentage=round((count / total_analyses) * 100.0, 1),
        ))

    # 7. Recent activity (PII sanitized)
    recent_query = (
        db.query(JobAnalysis)
        .order_by(JobAnalysis.created_at.desc())
        .limit(10)
        .all()
    )

    recent_activity: List[RecentAnalysisSummaryItem] = []
    for r in recent_query:
        recent_activity.append(RecentAnalysisSummaryItem(
            id=r.id,
            job_title=r.job_title,
            company_name=r.company_name,
            contact_channel=r.contact_channel,
            final_risk_score=r.final_risk_score,
            risk_level=r.risk_level,
            requires_payment=r.requires_payment,
            payment_amount_claimed=r.payment_amount_claimed,
            created_at=r.created_at.isoformat() if r.created_at else None,
        ))

    return AnalyticsSummaryResponse(
        total_analyses=total_analyses,
        average_risk_score=average_risk_score,
        high_risk_count=high_count,
        high_risk_percentage=high_pct,
        caution_count=caution_count,
        caution_percentage=caution_pct,
        low_risk_count=low_count,
        low_risk_percentage=low_pct,
        payment_demanded_count=payment_count,
        payment_demanded_percentage=payment_pct,
        risk_distribution=risk_distribution,
        score_ranges=score_ranges,
        channel_distribution=channel_distribution,
        top_warning_indicators=top_warning_indicators,
        recent_activity=recent_activity,
    )


def get_model_transparency(db: Session) -> ModelTransparencyResponse:
    """
    Generate model transparency report documenting deterministic rules and live trigger counts.
    """
    total_analyses = db.query(JobAnalysis).count()

    # Tally rule triggers across stored database warnings
    rule_counts: Dict[str, int] = {r["rule_id"]: 0 for r in CANONICAL_RULES}

    if total_analyses > 0:
        warning_records = db.query(JobAnalysis.warning_signs).all()
        for (w_list,) in warning_records:
            if isinstance(w_list, list):
                for w in w_list:
                    if isinstance(w, dict):
                        cat = w.get("category")
                        title = w.get("title", "")
                        for r in CANONICAL_RULES:
                            # Match rule by category and characteristic title substring
                            if r["match_category"] == cat and r["match_substring"] in title:
                                rule_counts[r["rule_id"]] += 1
                                break

    rules_definitions: List[RuleDefinition] = []
    for r in CANONICAL_RULES:
        count = rule_counts.get(r["rule_id"], 0)
        pct = round((count / total_analyses) * 100.0, 1) if total_analyses > 0 else 0.0
        rules_definitions.append(RuleDefinition(
            rule_id=r["rule_id"],
            name=r["name"],
            category=r["category"],
            severity=r["severity"],
            risk_points=r["risk_points"],
            impact_type=r["impact_type"],
            description=r["description"],
            detection_mechanism=r["detection_mechanism"],
            historical_triggers_count=count,
            trigger_percentage=pct,
        ))

    info = get_ml_service().get_transparency_info()
    benchmark_metrics = None
    if info.get("benchmark_metrics"):
        benchmark_metrics = OfflineBenchmarkMetrics(**info["benchmark_metrics"])

    return ModelTransparencyResponse(
        engine_type=info["engine_type"],
        engine_version=info["engine_version"],
        total_rules_defined=len(CANONICAL_RULES),
        ml_model_status=info["ml_model_status"],
        ml_metrics_available=info["ml_metrics_available"],
        ml_metrics_explanation=info["ml_metrics_explanation"],
        total_evaluations_analyzed=total_analyses,
        score_calculation_formula=info["score_calculation_formula"],
        score_bands=SCORE_BANDS,
        rules=rules_definitions,
        mitigating_signals=MITIGATING_SIGNALS,
        limitations=LIMITATIONS,
        benchmark_metrics=benchmark_metrics,
    )
