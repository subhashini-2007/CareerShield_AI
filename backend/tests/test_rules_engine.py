"""Automated tests for the heuristic safety and rules engine."""

from app.ml.rules_engine import evaluate_job_risk


def test_upfront_fee_detection_high_risk():
    """Verify that demanding an upfront registration fee triggers high risk indicators."""
    job_data = {
        "job_title": "Data Entry Executive",
        "company_name": "Apex Global Solutions",
        "job_description": "Candidates must pay Rs 2500 registration fee for training kit and laptop courier charges.",
        "requires_payment": True,
        "payment_amount_claimed": 2500.0,
        "payment_reason": "Registration and laptop deposit",
        "contact_channel": "EMAIL",
    }
    result = evaluate_job_risk(job_data)

    assert result["final_risk_score"] >= 65.0
    assert result["risk_level"] == "HIGH_RISK_INDICATORS"
    assert any(w["category"] == "UPFRONT_FEE" for w in result["warning_signs"])
    assert any("STOP" in rec or "Never transfer" in rec for rec in result["recommendations"])


def test_tcs_impersonation_with_gmail():
    """Verify that claiming to be TCS while using a Gmail address triggers domain spoofing alert."""
    job_data = {
        "job_title": "Systems Engineer",
        "company_name": "Tata Consultancy Services (TCS)",
        "recruiter_email": "tcs.recruitment.hr@gmail.com",
        "job_description": "We are hiring freshers for Systems Engineer profile across pan India locations.",
        "contact_channel": "EMAIL",
        "requires_payment": False,
    }
    result = evaluate_job_risk(job_data)

    assert result["company_assessment"]["is_known_firm"] is True
    assert result["company_assessment"]["domain_status"] == "personal_domain"
    assert any(w["category"] == "DOMAIN_SPOOFING" for w in result["warning_signs"])
    assert result["final_risk_score"] >= 35.0


def test_legitimate_tcs_role_low_risk():
    """Verify that a legitimate job with official domain and multi-stage interview evaluates as Low Risk."""
    job_data = {
        "job_title": "Graduate Engineer Trainee",
        "company_name": "Tata Consultancy Services",
        "recruiter_email": "careers@tcs.com",
        "application_url": "https://www.tcs.com/careers",
        "job_description": (
            "Candidates will undergo coding assessment and technical round of interview. "
            "Successful candidates will undergo panel interview and background verification. "
            "Includes standard provident fund and medical insurance benefits."
        ),
        "contact_channel": "OFFICIAL_PORTAL",
        "requires_payment": False,
        "salary_offered": "₹3,80,000",
    }
    result = evaluate_job_risk(job_data)

    assert result["final_risk_score"] <= 34.0
    assert result["risk_level"] == "LOW_RISK"
    assert result["company_assessment"]["domain_status"] == "verified_match"
    assert not any(w["category"] == "UPFRONT_FEE" for w in result["warning_signs"])


def test_telegram_channel_risk():
    """Verify that conducting hiring exclusively via Telegram elevates risk."""
    job_data = {
        "job_title": "Digital Marketing Trainee",
        "company_name": "FastMedia Agency",
        "contact_channel": "TELEGRAM",
        "job_description": "Join our official Telegram bot channel to receive daily tasks and earn rewards.",
        "requires_payment": False,
    }
    result = evaluate_job_risk(job_data)

    assert any(w["category"] == "CHANNEL_RISK" for w in result["warning_signs"])
    assert result["final_risk_score"] >= 30.0


def test_task_scam_pattern_detection():
    """Verify that social media like-and-subscribe task scams are flagged."""
    job_data = {
        "job_title": "Online Rating Assistant",
        "company_name": "Global Media Promotion",
        "job_description": "Earn up to Rs 5000 per day by like youtube videos and subscribing to channels. Instant daily payout.",
        "contact_channel": "WHATSAPP",
        "requires_payment": False,
    }
    result = evaluate_job_risk(job_data)

    assert any(w["category"] == "SALARY_ANOMALY" for w in result["warning_signs"])
    assert result["final_risk_score"] >= 50.0


def test_score_boundary_clamping():
    """Verify that the risk score stays bounded between 0.0 and 100.0 regardless of multiple triggers."""
    extreme_scam = {
        "job_title": "Direct Joining Executive",
        "company_name": "Google India",
        "recruiter_email": "google.hr@gmail.com",
        "contact_channel": "TELEGRAM",
        "requires_payment": True,
        "payment_amount_claimed": 10000.0,
        "payment_reason": "Security deposit",
        "job_description": (
            "Pay Rs 10000 refundable deposit for laptop courier charge. "
            "No interview required direct appointment letter today only hurry. "
            "Like youtube videos and earn 5000 per day daily payout."
        ),
    }
    result = evaluate_job_risk(extreme_scam)
    assert 0.0 <= result["final_risk_score"] <= 100.0
    assert result["final_risk_score"] >= 80.0
    assert result["risk_level"] == "HIGH_RISK_INDICATORS"


def test_unverified_domain_for_known_firm():
    """Verify R6: Unverified domain for a top tech firm triggers domain warning (+25 pts)."""
    job_data = {
        "job_title": "Associate Consultant",
        "company_name": "Infosys",
        "recruiter_email": "careers@infosys-hiring-portal.net",
        "job_description": "We are seeking software engineers for our global delivery team.",
        "contact_channel": "EMAIL",
        "requires_payment": False,
    }
    result = evaluate_job_risk(job_data)
    assert any(w["category"] == "DOMAIN_SPOOFING" and "Unverified Email Domain" in w["title"] for w in result["warning_signs"])
    assert result["company_assessment"]["domain_status"] == "unverified_domain"
    assert result["final_risk_score"] >= 25.0


def test_whatsapp_channel_risk():
    """Verify R7: Conducting hiring over WhatsApp elevates risk (+20 pts)."""
    job_data = {
        "job_title": "Support Associate",
        "company_name": "Nexus Support Services",
        "contact_channel": "WHATSAPP",
        "job_description": "We are evaluating candidates for customer support associate positions.",
        "requires_payment": False,
    }
    result = evaluate_job_risk(job_data)
    assert any(w["category"] == "CHANNEL_RISK" and "WhatsApp" in w["title"] for w in result["warning_signs"])
    assert result["final_risk_score"] >= 20.0


def test_pressure_tactics_and_zero_interview():
    """Verify R8: Urgency tactics and guaranteed selection without interview trigger warning (+20 pts)."""
    job_data = {
        "job_title": "Back Office Assistant",
        "company_name": "Rapid Enterprises",
        "job_description": "Direct joining letter issued today without any interview! Limited seats available apply today only.",
        "contact_channel": "EMAIL",
        "requires_payment": False,
    }
    result = evaluate_job_risk(job_data)
    assert any(w["category"] == "PRESSURE_TACTIC" and "Artificial Urgency" in w["title"] for w in result["warning_signs"])
    assert result["final_risk_score"] >= 20.0


def test_personal_webmail_for_generic_company():
    """Verify R9: Recruiter using free webmail for generic company triggers caution (+15 pts)."""
    job_data = {
        "job_title": "Junior Graphic Designer",
        "company_name": "Sunrise Creative Studio",
        "recruiter_email": "sunrisestudio.hiring@gmail.com",
        "job_description": "Looking for entry level Photoshop and Figma designers for our small agency.",
        "contact_channel": "EMAIL",
        "requires_payment": False,
    }
    result = evaluate_job_risk(job_data)
    assert any(w["category"] == "DOMAIN_SPOOFING" and "Personal Webmail Domain" in w["title"] for w in result["warning_signs"])
    assert result["final_risk_score"] >= 15.0


def test_missing_contact_info_risk():
    """Verify R10: Missing both application website URL and email contact triggers warning (+15 pts)."""
    job_data = {
        "job_title": "Field Executive",
        "company_name": "Local Logistics Hub",
        "recruiter_email": None,
        "application_url": None,
        "job_description": "Immediate opening for field executives in Bangalore local area.",
        "contact_channel": "OTHER",
        "requires_payment": False,
    }
    result = evaluate_job_risk(job_data)
    assert any(w["category"] == "MISSING_INFO" for w in result["warning_signs"])
    assert result["final_risk_score"] >= 15.0


def test_legitimate_known_firm_without_email_official_portal_url():
    """Verify that an official portal URL for a recognized employer grants verified match even without recruiter email."""
    job_data = {
        "job_title": "Systems Analyst",
        "company_name": "Infosys",
        "recruiter_email": None,
        "application_url": "https://career.infosys.com/jobdesc",
        "job_description": "Apply directly on official Infosys career portal. Structured interviews and assessment.",
        "contact_channel": "OFFICIAL_PORTAL",
        "requires_payment": False,
    }
    result = evaluate_job_risk(job_data)
    assert result["company_assessment"]["domain_status"] == "verified_match"
    assert result["company_assessment"]["is_known_firm"] is True
    assert result["company_assessment"]["verified_url"] == "https://www.infosys.com/careers"


def test_lookalike_domain_cannot_bypass_with_legitimate_url():
    """Verify that a scammer using a lookalike email cannot bypass spoofing detection by supplying a real corporate URL."""
    job_data = {
        "job_title": "Graduate Trainee",
        "company_name": "Tata Consultancy Services",
        "recruiter_email": "careers@tcs-recruitment-portal.biz",
        "application_url": "https://www.tcs.com/careers",
        "job_description": "We are hiring freshers for TCS graduate trainee programs.",
        "contact_channel": "EMAIL",
        "requires_payment": False,
    }
    result = evaluate_job_risk(job_data)
    assert result["company_assessment"]["domain_status"] == "unverified_domain"
    assert result["company_assessment"]["is_known_firm"] is True
    assert any(w["category"] == "DOMAIN_SPOOFING" and "Unverified Email Domain" in w["title"] for w in result["warning_signs"])
    assert result["final_risk_score"] >= 25.0


def test_arbitrary_unverified_company_with_own_domain():
    """Verify that an arbitrary company with its own custom domain is NOT marked as verified_match."""
    job_data = {
        "job_title": "Software Engineer",
        "company_name": "Vertex Global Labs",
        "recruiter_email": "careers@vertexgloballabs.com",
        "application_url": "https://vertexgloballabs.com",
        "job_description": "Growing tech startup hiring engineers for cloud product development.",
        "contact_channel": "EMAIL",
        "requires_payment": False,
    }
    result = evaluate_job_risk(job_data)
    # Custom domain is not a free webmail, but firm is not independently verified in KNOWN_TECH_EMPLOYERS
    assert result["company_assessment"]["is_known_firm"] is False
    assert result["company_assessment"]["domain_status"] == "unverified_domain"
    assert not any(w["category"] == "DOMAIN_SPOOFING" for w in result["warning_signs"])


