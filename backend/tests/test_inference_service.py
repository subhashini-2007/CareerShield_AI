"""Automated tests for ML inference service and controlled integration with the analyzer.

Verifies:
1. Valid artifact loads and produces a bounded score.
2. Runtime text preprocessing matches the training pipeline's expected representation.
3. Empty input is handled safely.
4. Missing artifact triggers graceful fallback.
5. Corrupt artifact or inference failure triggers graceful fallback.
6. High-risk rule evidence is never diluted by a low ML score.
7. Low ML scores do not create unsupported high-risk findings.
8. ML findings remain distinguishable from deterministic rule findings.
9. Existing analyzer API request/response contracts remain unchanged.
10. Existing known-company impersonation and upfront-fee tests continue to pass.
"""

from pathlib import Path
import tempfile
from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import JobAnalysis
from app.ml.inference_service import (
    CANONICAL_MODEL_VERSION,
    FALLBACK_MODEL_VERSION,
    MLInferenceResult,
    MLInferenceService,
    combine_evaluations,
    get_ml_service,
    map_score_to_risk_level,
    prepare_job_text_for_ml,
)
from app.schemas.analysis import JobAnalysisCreate, JobAnalysisResponse


class TestMLInferenceServiceUnit:
    """Unit tests for MLInferenceService and preprocessing adapter."""

    def test_valid_artifact_loads_and_produces_bounded_score(self):
        """1. Verify that real baseline pipeline loads and produces valid bounded probabilities."""
        service = get_ml_service()
        data = {
            "job_title": "Data Entry Clerk",
            "company_name": "Apex Staffing",
            "job_description": "Immediate opening for typing and data processing. Earn high weekly income.",
        }
        result = service.predict(data)

        assert result.is_available is True
        assert result.status == "success"
        assert 0.0 <= result.ml_risk_score <= 100.0
        assert result.fraud_probability is not None
        assert 0.0 <= result.fraud_probability <= 1.0
        assert "TFIDF-LogReg" in result.model_version or "CareerShield" in result.model_version

    def test_runtime_text_preprocessing_matches_training(self):
        """2. Verify that runtime adapter normalizes HTML, unescapes entities, and merges fields."""
        raw_payload = {
            "job_title": "  <h1>Junior Developer</h1>  ",
            "company_name": "Acme &amp; Sons Co.",
            "job_description": "<p>Join our team!<br/>Requirements: Python &amp; SQL.<br/>Visit #URL_abc123#.</p>",
        }
        processed = prepare_job_text_for_ml(raw_payload)

        # Confirm HTML stripped
        assert "<h1>" not in processed
        assert "<p>" not in processed
        assert "<br/>" not in processed
        assert "<br>" not in processed
        # Confirm entities unescaped
        assert "&amp;" not in processed
        assert "&" in processed
        # Confirm placeholders stripped
        assert "#URL_" not in processed
        # Confirm lowercase & content merged
        assert "junior developer" in processed
        assert "acme & sons co." in processed
        assert "python & sql." in processed

    def test_empty_input_handled_safely(self):
        """3. Verify that empty or whitespace-only inputs return safe default result without crashing."""
        service = get_ml_service()

        empty_cases = [
            {},
            {"job_title": "", "company_name": "", "job_description": ""},
            {"job_title": "   ", "company_name": "   ", "job_description": "   "},
            {"job_description": "too short"},
        ]

        for case in empty_cases:
            result = service.predict(case)
            assert result.status == "insufficient_text"
            assert result.ml_risk_score == 0.0
            assert result.fraud_probability == 0.0
            assert result.advisory_note is not None

    def test_missing_artifact_graceful_fallback(self):
        """4. Verify that missing model artifact path falls back cleanly to rule-only mode."""
        missing_path = Path("artifacts/models/non_existent_pipeline_file.joblib")
        service = MLInferenceService(model_path=missing_path)

        data = {
            "job_title": "Software Engineer",
            "company_name": "Tech Corp",
            "job_description": "Standard engineering role with Python and FastAPI.",
        }
        result = service.predict(data)

        assert result.is_available is False
        assert result.status == "unavailable"
        assert result.ml_risk_score == 0.0
        assert result.fraud_probability is None
        assert result.model_version == "v1.0-rules-engine-only"

    def test_corrupt_artifact_graceful_fallback(self):
        """5. Verify that a corrupt binary artifact triggers graceful degradation."""
        with tempfile.NamedTemporaryFile(suffix=".joblib", delete=False) as tmp:
            tmp.write(b"CORRUPT_NOT_A_VALID_JOBLIB_BINARY_DATA_1234567890")
            corrupt_path = Path(tmp.name)

        try:
            service = MLInferenceService(model_path=corrupt_path)
            data = {
                "job_title": "Software Engineer",
                "company_name": "Tech Corp",
                "job_description": "Standard engineering role with Python and FastAPI.",
            }
            result = service.predict(data)

            assert result.is_available is False
            assert result.status == "unavailable"
            assert result.ml_risk_score == 0.0
            assert result.fraud_probability is None
        finally:
            if corrupt_path.exists():
                corrupt_path.unlink()


class TestRuleDominanceAndScoreCombination:
    """Tests verifying asymmetric rule dominance and transparent combination logic."""

    def test_high_risk_rule_never_diluted_by_low_ml(self):
        """6. Verify that a critical heuristic score (>= 65) is NEVER reduced by a low ML score."""
        heuristic_eval = {
            "heuristic_risk_score": 85.0,
            "final_risk_score": 85.0,
            "risk_level": "HIGH_RISK_INDICATORS",
            "warning_signs": [{"category": "UPFRONT_FEE", "severity": "CRITICAL"}],
            "evidence_snippets": [
                {
                    "id": "evi-1",
                    "text": "Requires Rs 2500 registration fee",
                    "attribution": "heuristic_rule",
                    "impact_score": 55.0,
                    "reason": "Direct monetary demand",
                }
            ],
            "recommendations": ["Do not transfer money."],
            "model_version": "v1.0-rules-engine",
        }

        # Model thinks the text looks 95% genuine (fraud prob = 0.05)
        ml_result = MLInferenceResult(
            is_available=True,
            ml_risk_score=5.0,
            fraud_probability=0.05,
            status="success",
            model_version="CareerShield-AI-Baseline-TFIDF-LogReg-v1.0.0",
            top_contributing_features=[],
        )

        combined = combine_evaluations(heuristic_eval, ml_result)

        # Crucial: Final score must NOT be diluted!
        assert combined["final_risk_score"] == 85.0
        assert combined["risk_level"] == "HIGH_RISK_INDICATORS"
        assert combined["heuristic_risk_score"] == 85.0
        assert combined["ml_risk_score"] == 5.0
        assert combined["model_version"] == CANONICAL_MODEL_VERSION

    def test_low_ml_score_does_not_create_unsupported_high_risk(self):
        """7. Verify that ML alone cannot classify a job as HIGH_RISK_INDICATORS."""
        heuristic_eval = {
            "heuristic_risk_score": 0.0,
            "final_risk_score": 0.0,
            "risk_level": "LOW_RISK",
            "warning_signs": [],
            "evidence_snippets": [],
            "recommendations": [],
            "model_version": "v1.0-rules-engine",
        }

        # Sub-threshold probability (< 0.70) receives zero lift
        ml_sub_threshold = MLInferenceResult(
            is_available=True,
            ml_risk_score=68.0,
            fraud_probability=0.68,
            status="success",
            model_version="CareerShield-AI-Baseline-TFIDF-LogReg-v1.0.0",
        )
        res_sub = combine_evaluations(heuristic_eval, ml_sub_threshold)
        assert res_sub["final_risk_score"] == 0.0
        assert res_sub["risk_level"] == "LOW_RISK"

        # Extremely high model probability (0.95) receives bounded lift, capped strictly at 60.0
        ml_extreme = MLInferenceResult(
            is_available=True,
            ml_risk_score=95.0,
            fraud_probability=0.95,
            status="success",
            model_version="CareerShield-AI-Baseline-TFIDF-LogReg-v1.0.0",
        )
        res_extreme = combine_evaluations(heuristic_eval, ml_extreme)
        # 0.0 + ((0.95 - 0.70)/0.30)*15 = 12.5 -> final score 12.5
        assert res_extreme["final_risk_score"] <= 60.0
        assert res_extreme["risk_level"] != "HIGH_RISK_INDICATORS"

    def test_ml_findings_distinguishable_from_deterministic_rules(self):
        """8. Verify that ML evidence is explicitly tagged as 'ml_feature' with advisory phrasing."""
        heuristic_eval = {
            "heuristic_risk_score": 20.0,
            "final_risk_score": 20.0,
            "risk_level": "LOW_RISK",
            "warning_signs": [],
            "evidence_snippets": [
                {
                    "id": "evi-h-1",
                    "text": "WhatsApp channel",
                    "attribution": "heuristic_rule",
                    "impact_score": 20.0,
                    "reason": "Informal hiring channel",
                }
            ],
            "recommendations": ["Verify recruiter."],
            "model_version": "v1.0-rules-engine",
        }

        ml_result = MLInferenceResult(
            is_available=True,
            ml_risk_score=85.0,
            fraud_probability=0.85,
            status="success",
            model_version="CareerShield-AI-Baseline-TFIDF-LogReg-v1.0.0",
            top_contributing_features=[("data entry", 3.19), ("earn", 2.5)],
        )

        combined = combine_evaluations(heuristic_eval, ml_result)

        attributions = [e["attribution"] for e in combined["evidence_snippets"]]
        assert "heuristic_rule" in attributions
        assert "ml_feature" in attributions

        ml_snippet = next(e for e in combined["evidence_snippets"] if e["attribution"] == "ml_feature")
        # Ensure non-misleading advisory phrasing (not claiming verified fraud)
        assert "statistical" in ml_snippet["reason"].lower()
        assert "not factual verification" in ml_snippet["reason"].lower() or "advisory" in ml_snippet["reason"].lower()
        assert "verified scam" not in ml_snippet["reason"].lower()


class TestAnalyzerAPIEndToEndIntegration:
    """Integration tests verifying end-to-end API behavior with active ML inference service."""

    def test_analyzer_api_contract_preserved_with_ml(self, client: TestClient, db_session: Session):
        """9. Verify that /api/v1/analyze returns valid response compliant with existing Pydantic contract."""
        payload = {
            "job_title": "Senior Backend Software Engineer",
            "company_name": "Tata Consultancy Services",
            "recruiter_email": "careers@tcs.com",
            "contact_channel": "OFFICIAL_PORTAL",
            "job_description": (
                "Candidates will undergo coding assessment and technical round of interview. "
                "Includes standard provident fund and medical insurance benefits."
            ),
            "salary_offered": "₹8,50,000",
            "requires_payment": False,
        }

        response = client.post("/api/v1/analyze", json=payload)
        assert response.status_code == 201

        data = response.json()
        # Verify complete schema conformance
        validated = JobAnalysisResponse(**data)
        assert validated.job_title == "Senior Backend Software Engineer"
        assert isinstance(validated.ml_risk_score, float)
        assert 0.0 <= validated.ml_risk_score <= 100.0
        assert validated.final_risk_score == validated.heuristic_risk_score  # Legitimate corporate role
        assert validated.risk_level == "LOW_RISK"
        assert validated.model_version in [CANONICAL_MODEL_VERSION, FALLBACK_MODEL_VERSION]

        # Confirm persisted in DB
        db_record = db_session.query(JobAnalysis).filter_by(id=data["id"]).first()
        assert db_record is not None
        assert db_record.ml_risk_score == data["ml_risk_score"]

    def test_existing_impersonation_and_upfront_fee_remain_high_risk(self, client: TestClient):
        """10. Verify that known impersonation scams and upfront fee demands remain high risk."""
        # A. Upfront fee test
        fee_payload = {
            "job_title": "Data Entry Executive",
            "company_name": "Apex Online Services",
            "contact_channel": "EMAIL",
            "job_description": "Pay Rs 2500 security deposit for laptop and training kit. Direct joining.",
            "requires_payment": True,
            "payment_amount_claimed": 2500.0,
            "payment_reason": "Laptop Security Deposit",
        }
        res_fee = client.post("/api/v1/analyze", json=fee_payload)
        assert res_fee.status_code == 201
        data_fee = res_fee.json()
        assert data_fee["risk_level"] == "HIGH_RISK_INDICATORS"
        assert data_fee["final_risk_score"] >= 65.0
        assert any(w["category"] == "UPFRONT_FEE" for w in data_fee["warning_signs"])

        # B. TCS personal Gmail spoofing
        tcs_payload = {
            "job_title": "Graduate Trainee",
            "company_name": "Tata Consultancy Services (TCS)",
            "recruiter_email": "tcs.campus.hiring@gmail.com",
            "contact_channel": "EMAIL",
            "job_description": "Immediate selection for TCS campus freshers batch across pan-India.",
            "requires_payment": False,
        }
        res_tcs = client.post("/api/v1/analyze", json=tcs_payload)
        assert res_tcs.status_code == 201
        data_tcs = res_tcs.json()
        assert any(w["category"] == "DOMAIN_SPOOFING" for w in data_tcs["warning_signs"])
        assert data_tcs["company_assessment"]["is_known_firm"] is True
        assert data_tcs["company_assessment"]["domain_status"] == "personal_domain"


class TestPhase24AuditFixes:
    """Comprehensive regression tests verifying fixes for Phase 2.3 audit findings (P0, P1, P2)."""

    # -------------------------------------------------------------------------
    # Step 1 (P0): Score Dilution, Monotonicity & Clamping
    # -------------------------------------------------------------------------
    def test_score_dilution_boundary_heuristic_near_64(self):
        """Verify heuristic scores in [60.1, 64.9] are never reduced to 60.0 when ML fires."""
        for h_score in [60.1, 62.0, 64.0, 64.9]:
            h_eval = {
                "heuristic_risk_score": h_score,
                "final_risk_score": h_score,
                "risk_level": "NEEDS_CAUTION",
                "warning_signs": [],
                "evidence_snippets": [],
                "recommendations": ["Some advice."],
                "model_version": "v1.0-rules-engine",
            }
            # High ML confidence: prob = 0.85 -> lift = 7.5
            ml_res = MLInferenceResult(
                is_available=True,
                ml_risk_score=85.0,
                fraud_probability=0.85,
                status="success",
                model_version=CANONICAL_MODEL_VERSION,
            )
            combined = combine_evaluations(h_eval, ml_res)
            # Must NEVER be lower than h_score (monotonicity)
            assert combined["final_risk_score"] >= h_score
            # Must equal max(h_score, min(64.0, round(h_score + 7.5, 1)))
            expected = max(h_score, min(64.0, round(h_score + 7.5, 1)))
            assert combined["final_risk_score"] == expected
            # When h_score < 65.0, final score must stay < 65.0 (ML cannot create HIGH_RISK)
            assert combined["final_risk_score"] < 65.0
            assert combined["risk_level"] != "HIGH_RISK_INDICATORS"
            assert combined["risk_level"] == "NEEDS_CAUTION"

    def test_canonical_boundary_scores_and_risk_levels(self):
        """Verify boundary scores 34, 35, 60, 62, 64, 64.9, 65 across ML unavailable, low-signal, and high-signal."""
        boundary_cases = [
            # (h_score, expected_level_no_ml, expected_final_high_ml, expected_level_high_ml)
            (34.0, "LOW_RISK", 41.5, "NEEDS_CAUTION"),
            (35.0, "NEEDS_CAUTION", 42.5, "NEEDS_CAUTION"),
            (60.0, "NEEDS_CAUTION", 64.0, "NEEDS_CAUTION"),
            (62.0, "NEEDS_CAUTION", 64.0, "NEEDS_CAUTION"),
            (64.0, "NEEDS_CAUTION", 64.0, "NEEDS_CAUTION"),
            (64.9, "NEEDS_CAUTION", 64.9, "NEEDS_CAUTION"),
            (65.0, "HIGH_RISK_INDICATORS", 65.0, "HIGH_RISK_INDICATORS"),
        ]

        ml_high = MLInferenceResult(
            is_available=True,
            ml_risk_score=85.0,
            fraud_probability=0.85,
            status="success",
            model_version=CANONICAL_MODEL_VERSION,
        )

        ml_low = MLInferenceResult(
            is_available=True,
            ml_risk_score=20.0,
            fraud_probability=0.20,
            status="success",
            model_version=CANONICAL_MODEL_VERSION,
        )

        ml_unavailable = MLInferenceResult(
            is_available=False,
            ml_risk_score=0.0,
            fraud_probability=None,
            status="unavailable",
            model_version=FALLBACK_MODEL_VERSION,
        )

        for h_score, exp_lvl_no_ml, exp_final_high, exp_lvl_high in boundary_cases:
            h_eval = {
                "heuristic_risk_score": h_score,
                "final_risk_score": h_score,
                "risk_level": exp_lvl_no_ml,
                "warning_signs": [],
                "evidence_snippets": [],
                "recommendations": [
                    "The posting exhibits standard corporate hiring signals." if exp_lvl_no_ml == "LOW_RISK"
                    else "Exercise caution: Verify recruiter."
                ],
                "model_version": "v1.0-rules-engine",
            }

            # 1. ML Unavailable Case
            res_unavail = combine_evaluations(h_eval, ml_unavailable)
            assert res_unavail["final_risk_score"] == h_score
            assert res_unavail["risk_level"] == exp_lvl_no_ml
            assert res_unavail["model_version"] == FALLBACK_MODEL_VERSION

            # 2. Low ML Signal Case (no lift)
            res_low = combine_evaluations(h_eval, ml_low)
            assert res_low["final_risk_score"] == h_score
            assert res_low["risk_level"] == exp_lvl_no_ml

            # 3. High ML Signal Case
            res_high = combine_evaluations(h_eval, ml_high)
            assert res_high["final_risk_score"] == exp_final_high
            assert res_high["risk_level"] == exp_lvl_high

            # Rule dominance: 65.0 must never be altered
            if h_score >= 65.0:
                assert res_high["final_risk_score"] == 65.0
                assert res_high["risk_level"] == "HIGH_RISK_INDICATORS"

            # Isolation: scores below 65 must never reach HIGH_RISK
            if h_score < 65.0:
                assert res_high["final_risk_score"] < 65.0
                assert res_high["risk_level"] != "HIGH_RISK_INDICATORS"

            # Recommendation consistency for 34.0 -> caution transition
            if h_score == 34.0:
                assert not any("standard corporate hiring signals" in r.lower() for r in res_high["recommendations"])
                assert any("exercise caution" in r.lower() for r in res_high["recommendations"])
                assert any("advisory" in r.lower() for r in res_high["recommendations"])
                # When ML unavailable, low-risk advice preserved
                assert any("standard corporate hiring signals" in r.lower() for r in res_unavail["recommendations"])

    def test_map_score_to_risk_level_helper(self):
        """Verify the canonical mapping function across all boundary values."""
        assert map_score_to_risk_level(0.0) == "LOW_RISK"
        assert map_score_to_risk_level(34.0) == "LOW_RISK"
        assert map_score_to_risk_level(34.1) == "NEEDS_CAUTION"
        assert map_score_to_risk_level(35.0) == "NEEDS_CAUTION"
        assert map_score_to_risk_level(60.0) == "NEEDS_CAUTION"
        assert map_score_to_risk_level(62.0) == "NEEDS_CAUTION"
        assert map_score_to_risk_level(64.0) == "NEEDS_CAUTION"
        assert map_score_to_risk_level(64.9) == "NEEDS_CAUTION"
        assert map_score_to_risk_level(65.0) == "HIGH_RISK_INDICATORS"
        assert map_score_to_risk_level(100.0) == "HIGH_RISK_INDICATORS"

    def test_strict_monotonicity_across_score_spectrum(self):
        """Invariant: Final Risk Score >= Heuristic Risk Score for all score/prob combinations."""
        test_h_scores = [0.0, 10.0, 20.0, 34.0, 35.0, 50.0, 60.0, 64.0, 64.9, 65.0, 70.0, 85.0, 100.0]
        test_probs = [0.0, 0.20, 0.50, 0.69, 0.70, 0.75, 0.85, 0.95, 1.0]

        for h in test_h_scores:
            for p in test_probs:
                h_eval = {
                    "heuristic_risk_score": h,
                    "final_risk_score": h,
                    "risk_level": "HIGH_RISK_INDICATORS" if h >= 65.0 else ("NEEDS_CAUTION" if h >= 35.0 else "LOW_RISK"),
                    "warning_signs": [],
                    "evidence_snippets": [],
                    "recommendations": [],
                }
                ml_res = MLInferenceResult(
                    is_available=True,
                    ml_risk_score=round(p * 100, 1),
                    fraud_probability=p,
                    status="success",
                    model_version=CANONICAL_MODEL_VERSION,
                )
                combined = combine_evaluations(h_eval, ml_res)
                assert combined["final_risk_score"] >= h, f"Violation: final {combined['final_risk_score']} < h {h} at prob {p}"
                assert combined["risk_level"] == map_score_to_risk_level(combined["final_risk_score"])

    def test_hard_rule_dominance_for_high_risk(self):
        """Rule dominance: When H >= 65.0, final score equals H regardless of ML probability."""
        for h in [65.0, 75.0, 90.0, 100.0]:
            for p in [0.0, 0.05, 0.50, 0.95]:
                h_eval = {
                    "heuristic_risk_score": h,
                    "final_risk_score": h,
                    "risk_level": "HIGH_RISK_INDICATORS",
                    "warning_signs": [],
                    "evidence_snippets": [],
                    "recommendations": [],
                }
                ml_res = MLInferenceResult(
                    is_available=True,
                    ml_risk_score=round(p * 100, 1),
                    fraud_probability=p,
                    status="success",
                    model_version=CANONICAL_MODEL_VERSION,
                )
                combined = combine_evaluations(h_eval, ml_res)
                assert combined["final_risk_score"] == h
                assert combined["risk_level"] == "HIGH_RISK_INDICATORS"

    def test_ml_cannot_elevate_into_high_risk_alone(self):
        """Invariant: If H < 65.0, Final Score <= 64.0 and risk_level != HIGH_RISK_INDICATORS."""
        for h in [0.0, 30.0, 34.0, 50.0, 60.0, 64.0]:
            h_eval = {
                "heuristic_risk_score": h,
                "final_risk_score": h,
                "risk_level": "NEEDS_CAUTION" if h >= 35.0 else "LOW_RISK",
                "warning_signs": [],
                "evidence_snippets": [],
                "recommendations": [],
            }
            # Maximum possible ML probability 1.0 (lift = 15.0)
            ml_res = MLInferenceResult(
                is_available=True,
                ml_risk_score=100.0,
                fraud_probability=1.0,
                status="success",
                model_version=CANONICAL_MODEL_VERSION,
            )
            combined = combine_evaluations(h_eval, ml_res)
            assert combined["final_risk_score"] <= 64.0
            assert combined["risk_level"] in ["LOW_RISK", "NEEDS_CAUTION"]
            assert combined["risk_level"] != "HIGH_RISK_INDICATORS"

    # -------------------------------------------------------------------------
    # Step 2 (P1): Recommendation Text Consistency
    # -------------------------------------------------------------------------
    def test_recommendation_pruning_on_low_to_caution_transition(self):
        """When ML lift elevates a low-risk job into Needs Caution, prune 'standard corporate hiring signals' and inject caution guidance."""
        h_eval = {
            "heuristic_risk_score": 30.0,
            "final_risk_score": 30.0,
            "risk_level": "LOW_RISK",
            "warning_signs": [],
            "evidence_snippets": [],
            "recommendations": [
                "This posting aligns with standard corporate hiring signals. However, remain vigilant.",
                "Verify recruiter on official channels.",
            ],
            "model_version": "v1.0-rules-engine",
        }
        # Prob = 0.85 -> lift = 7.5 -> final_score = 37.5 (> 34.0, becomes NEEDS_CAUTION)
        ml_res = MLInferenceResult(
            is_available=True,
            ml_risk_score=85.0,
            fraud_probability=0.85,
            status="success",
            model_version=CANONICAL_MODEL_VERSION,
            top_contributing_features=[("earn", 2.0)],
        )
        combined = combine_evaluations(h_eval, ml_res)
        assert combined["final_risk_score"] == 37.5
        assert combined["risk_level"] == "NEEDS_CAUTION"

        recs = combined["recommendations"]
        assert not any("standard corporate hiring signals" in r.lower() for r in recs)
        assert any("exercise caution" in r.lower() for r in recs)
        assert any("advisory" in r.lower() for r in recs)

    def test_recommendation_preserved_when_no_category_change(self):
        """When ML score is low and job remains LOW_RISK, recommendations are preserved."""
        h_eval = {
            "heuristic_risk_score": 20.0,
            "final_risk_score": 20.0,
            "risk_level": "LOW_RISK",
            "warning_signs": [],
            "evidence_snippets": [],
            "recommendations": [
                "This posting aligns with standard corporate hiring signals.",
            ],
            "model_version": "v1.0-rules-engine",
        }
        # Prob = 0.20 -> no lift
        ml_res = MLInferenceResult(
            is_available=True,
            ml_risk_score=20.0,
            fraud_probability=0.20,
            status="success",
            model_version=CANONICAL_MODEL_VERSION,
        )
        combined = combine_evaluations(h_eval, ml_res)
        assert combined["final_risk_score"] == 20.0
        assert combined["risk_level"] == "LOW_RISK"
        assert any("standard corporate hiring signals" in r for r in combined["recommendations"])

    # -------------------------------------------------------------------------
    # Step 3 (P1) & Step 4 (P2): Truthful Model Transparency & Versioning
    # -------------------------------------------------------------------------
    def test_transparency_info_with_loaded_baseline(self):
        """Verify get_transparency_info() returns active hybrid details and benchmark metrics."""
        service = get_ml_service()
        info = service.get_transparency_info()

        assert info["engine_type"] == "Hybrid (Deterministic Heuristics + Supplementary TF-IDF ML Advisory)"
        assert info["engine_version"] == CANONICAL_MODEL_VERSION
        assert info["ml_model_status"] == "Active (Trained Baseline Loaded)"
        assert info["ml_metrics_available"] is True
        assert "EMSCAD dataset" in info["ml_metrics_explanation"]
        assert "ROC-AUC" in info["ml_metrics_explanation"]
        assert "PR-AUC" in info["ml_metrics_explanation"]
        assert "0.61" in info["ml_metrics_explanation"]
        assert "Historical offline metrics reflect 2012–2014 data" in info["ml_metrics_explanation"]
        assert "Hybrid scoring" in info["score_calculation_formula"]
        assert "Hard Rule Dominance" in info["score_calculation_formula"]

    def test_transparency_info_fallback_mode(self):
        """Verify get_transparency_info() in fallback mode when artifact is missing."""
        fallback_service = MLInferenceService(model_path=Path("non_existent_path.joblib"))
        info = fallback_service.get_transparency_info()

        assert info["engine_type"] == "Deterministic Heuristic Rules Engine (Rules-Only Fallback)"
        assert info["engine_version"] == FALLBACK_MODEL_VERSION
        assert info["ml_model_status"] == "Unavailable / Rules-Only Fallback Active"
        assert info["ml_metrics_available"] is False
        assert "fallback mode" in info["ml_metrics_explanation"]

    def test_transparency_api_endpoint(self, client: TestClient):
        """Verify GET /api/v1/analytics/model-transparency returns standardized schema with canonical version."""
        response = client.get("/api/v1/analytics/model-transparency")
        assert response.status_code == 200
        data = response.json()

        assert data["engine_version"] == CANONICAL_MODEL_VERSION
        assert data["ml_model_status"] == "Active (Trained Baseline Loaded)"
        assert data["ml_metrics_available"] is True
        assert data["total_rules_defined"] == 10
        assert len(data["score_bands"]) == 3

    # -------------------------------------------------------------------------
    # Step 5 (P2): Runtime Preprocessing URL/Email/Phone Masking
    # -------------------------------------------------------------------------
    def test_runtime_preprocessing_masks_urls_emails_phones(self):
        """Verify prepare_job_text_for_ml strips raw URLs, emails, and phone numbers before tokenization."""
        raw_payload = {
            "job_title": "Senior Cloud Architect",
            "company_name": "Acme Global Systems",
            "job_description": (
                "Apply online at https://jobs.acmeglobal.com/careers/apply?id=987654 or http://apply.org. "
                "For inquiries, email recruiting.lead@acmeglobal.co.uk or hr@sub.domain.org. "
                "Contact our hiring desk at +91-9876543210 or +1 (555) 019-2834. "
                "Salary up to Rs 25,00,000 per annum with comprehensive benefits."
            ),
        }
        cleaned = prepare_job_text_for_ml(raw_payload)

        # URLs must be stripped to spaces
        assert "https://" not in cleaned
        assert "http://" not in cleaned
        assert "jobs.acmeglobal.com" not in cleaned
        assert "apply.org" not in cleaned

        # Emails must be stripped to spaces
        assert "recruiting.lead@acmeglobal.co.uk" not in cleaned
        assert "hr@sub.domain.org" not in cleaned
        assert "@" not in cleaned

        # Phone numbers must be stripped to spaces
        assert "+91-9876543210" not in cleaned
        assert "9876543210" not in cleaned
        assert "555" not in cleaned

        # Core semantic tokens must remain intact
        assert "senior cloud architect" in cleaned
        assert "acme global systems" in cleaned
        assert "comprehensive benefits" in cleaned
