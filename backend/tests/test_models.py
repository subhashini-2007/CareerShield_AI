"""Automated tests for database models and schema relationships."""

from sqlalchemy.orm import Session

from app.db.models import (
    AnalysisFeedback,
    CompanyBenchmark,
    JobAnalysis,
    ModelEvalMetric,
)


def test_job_analysis_lifecycle(db_session: Session):
    """Test creating, saving, and querying a JobAnalysis record."""
    analysis = JobAnalysis(
        job_title="Associate Software Engineer",
        company_name="Acme Technology Solutions",
        recruiter_email="hr@acmetech.com",
        contact_channel="EMAIL",
        job_description="Seeking a fresher Python developer for backend API engineering.",
        salary_offered="₹4,50,000",
        salary_frequency="ANNUAL",
        requires_payment=False,
        ml_risk_score=15.0,
        heuristic_risk_score=10.0,
        final_risk_score=12.0,
        risk_level="LOW_RISK",
        confidence_score=0.92,
        warning_signs=[],
        evidence_snippets=[],
        recommendations=["Verify company website independently before sharing documents."],
        company_assessment={"domain_status": "unverified", "is_known_firm": False},
    )

    db_session.add(analysis)
    db_session.commit()

    retrieved = db_session.query(JobAnalysis).filter_by(id=analysis.id).first()
    assert retrieved is not None
    assert retrieved.job_title == "Associate Software Engineer"
    assert retrieved.risk_level == "LOW_RISK"
    assert len(retrieved.recommendations) == 1

    data = retrieved.to_dict()
    assert data["id"] == analysis.id
    assert data["ml_risk_score"] == 15.0


def test_feedback_relationship(db_session: Session):
    """Test creating feedback tied to a JobAnalysis record."""
    analysis = JobAnalysis(
        job_title="Data Entry Intern",
        company_name="Express Gigs",
        job_description="Earn 5000 daily typing captchas from home.",
        requires_payment=True,
        payment_amount_claimed=1500.0,
        payment_reason="Registration Fee",
        ml_risk_score=85.0,
        heuristic_risk_score=95.0,
        final_risk_score=91.0,
        risk_level="HIGH_RISK_INDICATORS",
        confidence_score=0.98,
        warning_signs=[{"category": "UPFRONT_FEE", "severity": "CRITICAL"}],
        evidence_snippets=["pay 1500 registration fee"],
        recommendations=["Do not transfer money."],
        company_assessment={},
    )
    db_session.add(analysis)
    db_session.commit()

    feedback = AnalysisFeedback(
        analysis_id=analysis.id,
        user_verdict="ACCURATE",
        actual_outcome="CONFIRMED_SCAM",
        comments="The recruiter asked for Rs 1500 on WhatsApp immediately after application.",
    )
    db_session.add(feedback)
    db_session.commit()

    retrieved = db_session.query(AnalysisFeedback).filter_by(analysis_id=analysis.id).first()
    assert retrieved is not None
    assert retrieved.user_verdict == "ACCURATE"
    assert retrieved.analysis.job_title == "Data Entry Intern"


def test_company_benchmark_model(db_session: Session):
    """Test known company benchmark persistence."""
    company = CompanyBenchmark(
        canonical_name="Tata Consultancy Services",
        official_career_url="https://www.tcs.com/careers",
        legitimate_domains=["tcs.com", "careers.tcs.com"],
        never_charges_fees_policy=True,
        official_hr_email_pattern="*@tcs.com",
        frequently_spoofed=True,
        advisory_note="TCS never charges any recruitment or training fees.",
    )
    db_session.add(company)
    db_session.commit()

    retrieved = db_session.query(CompanyBenchmark).filter_by(canonical_name="Tata Consultancy Services").first()
    assert retrieved is not None
    assert "tcs.com" in retrieved.legitimate_domains
    assert retrieved.never_charges_fees_policy is True


def test_model_eval_metric_model(db_session: Session):
    """Test model evaluation metric persistence."""
    metric = ModelEvalMetric(
        model_version="v1.0-benchmark",
        algorithm_name="Calibrated Logistic Regression",
        dataset_records_count=1000,
        test_accuracy=0.88,
        precision_macro=0.87,
        recall_macro=0.86,
        f1_macro=0.865,
        roc_auc=0.92,
        confusion_matrix={"tn": 450, "fp": 50, "fn": 60, "tp": 440},
        feature_importance_top20=[{"feature": "fee", "weight": 2.4}],
    )
    db_session.add(metric)
    db_session.commit()

    retrieved = db_session.query(ModelEvalMetric).filter_by(model_version="v1.0-benchmark").first()
    assert retrieved is not None
    assert retrieved.roc_auc == 0.92
    assert retrieved.confusion_matrix["tn"] == 450
