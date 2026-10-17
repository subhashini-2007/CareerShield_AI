"""Automated integration tests for job risk analysis API endpoints."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import JobAnalysis


def test_analyze_validation_empty_fields(client: TestClient):
    """Verify that empty required fields or whitespace trigger HTTP 422 validation error."""
    # Empty title
    payload = {
        "job_title": "   ",
        "company_name": "Acme Corp",
        "job_description": "Valid job description with sufficient length for testing.",
    }
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 422

    # Empty company name
    payload = {
        "job_title": "Developer",
        "company_name": "",
        "job_description": "Valid job description with sufficient length for testing.",
    }
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 422

    # Description too short
    payload = {
        "job_title": "Developer",
        "company_name": "Acme Corp",
        "job_description": "Too short",
    }
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 422

    # Negative fee amount
    payload = {
        "job_title": "Developer",
        "company_name": "Acme Corp",
        "job_description": "Valid job description with sufficient length for testing.",
        "requires_payment": True,
        "payment_amount_claimed": -500.0,
    }
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 422


def test_analyze_success_and_persistence(client: TestClient, db_session: Session):
    """Verify that a valid job posting is analyzed, returns 201, and is saved in SQLite database."""
    payload = {
        "job_title": "Graduate Trainee Engineer",
        "company_name": "Infosys Limited",
        "recruiter_email": "campus.hiring@infosys.com",
        "contact_channel": "OFFICIAL_PORTAL",
        "job_description": (
            "We are hiring entry level software engineers. "
            "Selection process involves coding assessment and technical interview rounds. "
            "Successful candidates will undergo formal training at Infosys Mysore campus."
        ),
        "salary_offered": "₹4,00,000",
        "salary_frequency": "ANNUAL",
        "location": "Bangalore / Mysore",
        "requires_payment": False,
    }

    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert "id" in data
    assert data["job_title"] == "Graduate Trainee Engineer"
    assert data["company_name"] == "Infosys Limited"
    assert data["risk_level"] in ["LOW_RISK", "NEEDS_CAUTION", "HIGH_RISK_INDICATORS"]
    assert "heuristic_risk_score" in data
    assert "final_risk_score" in data
    assert "disclaimer" in data
    assert "recommendations" in data

    # Verify persistent database storage
    analysis_id = data["id"]
    db_record = db_session.query(JobAnalysis).filter_by(id=analysis_id).first()
    assert db_record is not None
    assert db_record.company_name == "Infosys Limited"
    assert db_record.job_title == "Graduate Trainee Engineer"
    assert db_record.final_risk_score == data["final_risk_score"]


def test_list_analyses_history(client: TestClient):
    """Verify that GET /api/v1/analyses returns paginated records with filters."""
    # Seed an analysis
    payload = {
        "job_title": "Content Typist",
        "company_name": "QuickCash Gigs",
        "contact_channel": "WHATSAPP",
        "job_description": "Earn 5000 daily typing captchas from home. Immediate joining.",
        "requires_payment": True,
        "payment_amount_claimed": 1200.0,
        "payment_reason": "Software registration fee",
    }
    client.post("/api/v1/analyze", json=payload)

    # Fetch history
    response = client.get("/api/v1/analyses?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1
    assert len(data["items"]) >= 1

    # Filter by risk level
    high_risk_response = client.get("/api/v1/analyses?risk_level=HIGH_RISK_INDICATORS")
    assert high_risk_response.status_code == 200
    hr_data = high_risk_response.json()
    for item in hr_data["items"]:
        assert item["risk_level"] == "HIGH_RISK_INDICATORS"

    # Search filter
    search_response = client.get("/api/v1/analyses?search=QuickCash")
    assert search_response.status_code == 200
    search_data = search_response.json()
    assert search_data["total"] >= 1
    assert any("QuickCash" in item["company_name"] for item in search_data["items"])


def test_get_analysis_by_id(client: TestClient):
    """Verify fetching a specific analysis by UUID and 404 for non-existent IDs."""
    payload = {
        "job_title": "Junior Python Developer",
        "company_name": "CloudTech Solutions",
        "job_description": "Seeking fresher Python engineers for backend REST APIs and database work.",
        "requires_payment": False,
    }
    create_res = client.post("/api/v1/analyze", json=payload)
    assert create_res.status_code == 201
    analysis_id = create_res.json()["id"]

    # Valid ID lookup
    detail_res = client.get(f"/api/v1/analyses/{analysis_id}")
    assert detail_res.status_code == 200
    assert detail_res.json()["id"] == analysis_id

    # Invalid ID lookup
    missing_res = client.get("/api/v1/analyses/non-existent-uuid-12345")
    assert missing_res.status_code == 404


def test_analyze_daily_salary_frequency_supported(client: TestClient, db_session: Session):
    """Verify that daily salary frequency is accepted, normalized, and persisted."""
    payload = {
        "job_title": "Social Media Review Assistant",
        "company_name": "Star Media Promotions",
        "recruiter_email": "contact@t.me/starmedia_bot",
        "contact_channel": "TELEGRAM",
        "job_description": "Like youtube videos and subscribe to channels to earn up to Rs 5000 per day. Instant daily payout.",
        "salary_offered": "₹3,000 - ₹5,000",
        "salary_frequency": "DAILY",
        "location": "Remote / Flexible",
        "requires_payment": False,
    }
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["salary_frequency"] == "DAILY"

    # Verify persisted in database
    db_record = db_session.query(JobAnalysis).filter_by(id=data["id"]).first()
    assert db_record is not None
    assert db_record.salary_frequency == "DAILY"

