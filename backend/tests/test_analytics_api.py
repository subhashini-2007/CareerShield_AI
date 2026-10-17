"""Automated unit and integration tests for analytics and model transparency endpoints."""

from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import JobAnalysis


def test_analytics_summary_empty_database(client: TestClient):
    """Verify analytics summary returns safe zeroed metrics on an empty database."""
    response = client.get("/api/v1/analytics/summary")
    assert response.status_code == 200
    data = response.json()

    assert data["total_analyses"] == 0
    assert data["average_risk_score"] == 0.0
    assert data["high_risk_count"] == 0
    assert data["high_risk_percentage"] == 0.0
    assert data["caution_count"] == 0
    assert data["caution_percentage"] == 0.0
    assert data["low_risk_count"] == 0
    assert data["low_risk_percentage"] == 0.0
    assert data["payment_demanded_count"] == 0
    assert data["payment_demanded_percentage"] == 0.0
    assert len(data["risk_distribution"]) == 3
    assert len(data["score_ranges"]) == 5
    assert data["channel_distribution"] == []
    assert data["top_warning_indicators"] == []
    assert data["recent_activity"] == []


def test_analytics_summary_populated_database(client: TestClient, db_session: Session):
    """Verify aggregated metrics, percentages, channel breakdown, and warnings on populated DB."""
    # 1. Seed low-risk record
    low_job = JobAnalysis(
        job_title="Associate Software Engineer",
        company_name="Tata Consultancy Services",
        contact_channel="OFFICIAL_PORTAL",
        job_description="Standard technical assessment and panel interview. Provident fund and gratuity.",
        final_risk_score=10.0,
        heuristic_risk_score=10.0,
        ml_risk_score=0.0,
        risk_level="LOW_RISK",
        requires_payment=False,
        warning_signs=[],
        evidence_snippets=[],
        company_assessment={"domain_status": "verified_match"},
        created_at=datetime.now(timezone.utc),
    )

    # 2. Seed needs-caution record
    caution_job = JobAnalysis(
        job_title="Content Writer",
        company_name="Freelance Media Hub",
        contact_channel="EMAIL",
        job_description="Remote writing opportunity with weekly assignments.",
        final_risk_score=45.0,
        heuristic_risk_score=45.0,
        ml_risk_score=0.0,
        risk_level="NEEDS_CAUTION",
        requires_payment=False,
        warning_signs=[
            {
                "id": "w1",
                "category": "DOMAIN_SPOOFING",
                "severity": "MEDIUM",
                "title": "Recruiter Using Personal Webmail Domain",
                "description": "Recruiter uses personal webmail.",
            }
        ],
        evidence_snippets=[],
        company_assessment={"domain_status": "personal_domain"},
        created_at=datetime.now(timezone.utc),
    )

    # 3. Seed high-risk scam record
    high_job = JobAnalysis(
        job_title="Data Entry Assistant",
        company_name="QuickCash Services",
        contact_channel="WHATSAPP",
        job_description="Urgent opening! Pay Rs 2500 security deposit for laptop.",
        final_risk_score=95.0,
        heuristic_risk_score=95.0,
        ml_risk_score=0.0,
        risk_level="HIGH_RISK_INDICATORS",
        requires_payment=True,
        payment_amount_claimed=2500.0,
        payment_reason="Laptop Courier Deposit",
        warning_signs=[
            {
                "id": "w2",
                "category": "UPFRONT_FEE",
                "severity": "CRITICAL",
                "title": "Recruiter Demands Upfront Payment",
                "description": "Requires Rs 2500 upfront deposit.",
            },
            {
                "id": "w3",
                "category": "CHANNEL_RISK",
                "severity": "MEDIUM",
                "title": "Informal Hiring Communication via WhatsApp",
                "description": "Contact channel is WhatsApp.",
            },
        ],
        evidence_snippets=[],
        company_assessment={"domain_status": "missing"},
        created_at=datetime.now(timezone.utc),
    )

    db_session.add_all([low_job, caution_job, high_job])
    db_session.commit()

    # Query analytics summary
    response = client.get("/api/v1/analytics/summary")
    assert response.status_code == 200
    data = response.json()

    assert data["total_analyses"] == 3
    assert data["low_risk_count"] == 1
    assert data["caution_count"] == 1
    assert data["high_risk_count"] == 1
    assert data["low_risk_percentage"] == 33.3
    assert data["caution_percentage"] == 33.3
    assert data["high_risk_percentage"] == 33.3

    assert data["payment_demanded_count"] == 1
    assert data["payment_demanded_percentage"] == 33.3

    # Expected average: (10 + 45 + 95) / 3 = 50.0
    assert data["average_risk_score"] == 50.0

    # Channel distribution
    channels = {c["channel"]: c for c in data["channel_distribution"]}
    assert "WHATSAPP" in channels
    assert channels["WHATSAPP"]["count"] == 1
    assert channels["WHATSAPP"]["average_risk_score"] == 95.0

    # Top warnings
    warning_cats = [w["category"] for w in data["top_warning_indicators"]]
    assert "UPFRONT_FEE" in warning_cats
    assert "CHANNEL_RISK" in warning_cats
    assert "DOMAIN_SPOOFING" in warning_cats

    # Recent activity
    assert len(data["recent_activity"]) == 3
    # Check that privacy is preserved: no recruiter email, phone, or raw descriptions in summary item
    recent_item = data["recent_activity"][0]
    assert "job_title" in recent_item
    assert "company_name" in recent_item
    assert "final_risk_score" in recent_item
    assert "recruiter_email" not in recent_item
    assert "recruiter_phone" not in recent_item
    assert "job_description" not in recent_item


def test_model_transparency_empty_database(client: TestClient):
    """Verify model transparency response on empty database."""
    response = client.get("/api/v1/analytics/model-transparency")
    assert response.status_code == 200
    data = response.json()

    assert "Hybrid" in data["engine_type"] or "Deterministic" in data["engine_type"]
    assert data["engine_version"] in [
        "CareerShield-AI-Baseline-TFIDF-LogReg-v1.0.0",
        "v1.0-rules-engine-only",
        "v1.0-rules-engine",
    ]
    assert data["total_rules_defined"] == 10
    assert "score_calculation_formula" in data
    assert data["total_evaluations_analyzed"] == 0
    assert len(data["rules"]) == 10
    assert len(data["score_bands"]) == 3
    assert len(data["mitigating_signals"]) == 3
    assert len(data["limitations"]) >= 3

    # All rule triggers should be 0
    for rule in data["rules"]:
        assert rule["historical_triggers_count"] == 0
        assert rule["trigger_percentage"] == 0.0


def test_model_transparency_populated_database(client: TestClient, db_session: Session):
    """Verify model transparency accurately counts rule triggers from stored warnings."""
    seeded_job = JobAnalysis(
        job_title="Operations Trainee",
        company_name="Apex Corp",
        contact_channel="TELEGRAM",
        job_description="Urgent work! Like youtube videos for quick income.",
        final_risk_score=85.0,
        heuristic_risk_score=85.0,
        ml_risk_score=0.0,
        risk_level="HIGH_RISK_INDICATORS",
        requires_payment=True,
        payment_amount_claimed=500.0,
        warning_signs=[
            {
                "id": "w1",
                "category": "UPFRONT_FEE",
                "severity": "CRITICAL",
                "title": "Recruiter Demands Upfront Payment",
                "description": "demands 500",
            },
            {
                "id": "w2",
                "category": "CHANNEL_RISK",
                "severity": "HIGH",
                "title": "Recruitment Conducted via Telegram",
                "description": "telegram used",
            },
            {
                "id": "w3",
                "category": "SALARY_ANOMALY",
                "severity": "HIGH",
                "title": "Task-Based High-Return Work Scheme",
                "description": "task scheme",
            },
        ],
        evidence_snippets=[],
        company_assessment={"domain_status": "missing"},
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(seeded_job)
    db_session.commit()

    response = client.get("/api/v1/analytics/model-transparency")
    assert response.status_code == 200
    data = response.json()

    assert data["total_evaluations_analyzed"] == 1

    rule_dict = {r["rule_id"]: r for r in data["rules"]}
    assert rule_dict["R1_UPFRONT_FEE_DIRECT"]["historical_triggers_count"] == 1
    assert rule_dict["R1_UPFRONT_FEE_DIRECT"]["trigger_percentage"] == 100.0

    assert rule_dict["R4_CHANNEL_TELEGRAM"]["historical_triggers_count"] == 1
    assert rule_dict["R4_CHANNEL_TELEGRAM"]["trigger_percentage"] == 100.0

    assert rule_dict["R5_TASK_SCAM_PATTERNS"]["historical_triggers_count"] == 1
    assert rule_dict["R5_TASK_SCAM_PATTERNS"]["trigger_percentage"] == 100.0


def test_analytics_summary_handles_malformed_warning_signs(client: TestClient, db_session: Session):
    """Verify endpoint does not raise 500 when warning_signs is None or has unexpected shapes."""
    malformed_job = JobAnalysis(
        job_title="QA Tester",
        company_name="Test Org",
        contact_channel="EMAIL",
        job_description="Sample job description with at least fifteen characters.",
        final_risk_score=20.0,
        heuristic_risk_score=20.0,
        ml_risk_score=0.0,
        risk_level="LOW_RISK",
        requires_payment=False,
        warning_signs=None,  # Null JSON
        evidence_snippets=None,
        company_assessment=None,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(malformed_job)
    db_session.commit()

    response = client.get("/api/v1/analytics/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_analyses"] == 1
    assert data["average_risk_score"] == 20.0
