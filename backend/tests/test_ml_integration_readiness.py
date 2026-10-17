"""Integration readiness tests for CareerShield AI Phase 2.1.

Verifies model artifact loading, preprocessing adapter alignment, inference
probability ranges, graceful degradation, and non-dilutive signal fusion
without modifying active production code or services.
"""

from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import joblib
import numpy as np
import pytest

from app.ml.preprocessing import clean_text
from app.schemas.analysis import EvidenceSnippetSchema, JobAnalysisCreate


BASE_DIR = Path(__file__).resolve().parents[1]
MODEL_PATH = BASE_DIR / "artifacts" / "models" / "baseline_pipeline.joblib"
METADATA_PATH = BASE_DIR / "artifacts" / "models" / "model_metadata.json"


def prepare_job_text_for_ml(data: Dict[str, Any]) -> str:
    """Proposed adapter: transforms incoming analyzer payload into training representation."""
    title = str(data.get("job_title") or "")
    company = str(data.get("company_name") or "")
    description = str(data.get("job_description") or "")
    raw_combined = f"{title} {company} {description}"
    return clean_text(raw_combined)


def simulate_hybrid_combiner(
    heuristic_score: float,
    ml_fraud_proba: Optional[float],
) -> float:
    """
    Proposed non-dilutive asymmetric combiner:
    - If heuristic score >= 70 (Critical rule), heuristic dominates; ML cannot suppress it.
    - If heuristic score < 70, ML provides bounded advisory lift only when proba >= 0.65.
    - ML probability never reduces heuristic score.
    """
    if ml_fraud_proba is None:
        return heuristic_score

    if heuristic_score >= 70.0:
        return heuristic_score

    # Bounded lift between 0 and 25 points when ML probability is elevated
    if ml_fraud_proba >= 0.65:
        lift = ((ml_fraud_proba - 0.65) / 0.35) * 25.0
        return min(100.0, round(heuristic_score + lift, 1))

    return heuristic_score


class TestMLIntegrationReadiness:
    """Audit tests verifying that the trained baseline can be safely integrated."""

    def test_artifact_exists_and_loads(self):
        """Verify baseline_pipeline.joblib exists and deserializes correctly."""
        assert MODEL_PATH.exists(), f"Model artifact missing at: {MODEL_PATH}"
        pipeline = joblib.load(MODEL_PATH)
        assert hasattr(pipeline, "predict_proba"), "Pipeline must support predict_proba."
        assert "tfidf" in pipeline.named_steps, "Pipeline missing 'tfidf' step."
        assert "clf" in pipeline.named_steps, "Pipeline missing 'clf' step."

    def test_metadata_descriptor_validity(self):
        """Verify model_metadata.json contains verified audit fields."""
        import json

        assert METADATA_PATH.exists(), f"Metadata missing at: {METADATA_PATH}"
        with open(METADATA_PATH, "r", encoding="utf-8") as f:
            meta = json.load(f)

        assert meta["model_name"] == "CareerShield-AI-Baseline-TFIDF-LogReg"
        assert meta["model_version"] == "1.0.0"
        assert "held_out_test_metrics_default_threshold_0_50" in meta
        assert "held_out_test_metrics_tuned_threshold" in meta

        # Verify tuned threshold metrics
        tuned = meta["held_out_test_metrics_tuned_threshold"]
        assert tuned["threshold"] == 0.61
        assert tuned["fraud_class"]["precision"] > 0.65
        assert tuned["fraud_class"]["recall"] > 0.70

    def test_preprocessing_adapter_cleans_runtime_input(self):
        """Verify adapter strips HTML, normalizes entities, and merges fields."""
        raw_payload = {
            "job_title": "<b>Data Entry Clerk</b>",
            "company_name": "Apex Global &amp; Co",
            "job_description": "<p>Earn money from home! Send details to test@domain.com.</p>",
        }
        processed = prepare_job_text_for_ml(raw_payload)

        assert "<b>" not in processed
        assert "<p>" not in processed
        assert "&amp;" not in processed
        assert "&" in processed
        assert "data entry clerk" in processed
        assert "apex global & co" in processed
        assert "earn money from home!" in processed

    def test_pipeline_inference_on_adapter_text(self):
        """Verify that pipeline outputs valid probability distributions."""
        pipeline = joblib.load(MODEL_PATH)
        sample_payload = {
            "job_title": "Senior Python Backend Engineer",
            "company_name": "TechVentures India",
            "job_description": "We are looking for an experienced engineer with Django, FastAPI, PostgreSQL, and AWS.",
        }
        text = prepare_job_text_for_ml(sample_payload)
        probas = pipeline.predict_proba([text])

        assert probas.shape == (1, 2), "Inference must produce binary class probabilities."
        assert np.isclose(np.sum(probas[0]), 1.0, atol=1e-5), "Probabilities must sum to 1.0."
        assert 0.0 <= probas[0][1] <= 1.0, "Fraud probability must be bounded in [0, 1]."

    def test_graceful_fallback_on_missing_artifact(self):
        """Verify that a missing artifact path does not crash execution."""
        missing_path = BASE_DIR / "artifacts" / "models" / "nonexistent_model.joblib"

        def safe_loader(path: Path) -> Tuple[Optional[Any], str]:
            if not path.exists():
                return None, "v1.0-rules-engine-only"
            try:
                return joblib.load(path), "v1.0.0"
            except Exception:
                return None, "v1.0-rules-engine-only"

        model, version = safe_loader(missing_path)
        assert model is None
        assert version == "v1.0-rules-engine-only"

    def test_non_dilutive_hybrid_combiner_hard_rule_dominance(self):
        """Verify that high-risk heuristic violations are never diluted by low ML score."""
        # Case A: Recruiter demanded money (H=55 + 20=75), but ML thinks text looks genuine (prob=0.15)
        heuristic_score = 75.0
        ml_prob = 0.15
        final_score = simulate_hybrid_combiner(heuristic_score, ml_prob)
        assert final_score == 75.0, "ML probability must never reduce a critical heuristic score."

    def test_non_dilutive_hybrid_combiner_advisory_lift(self):
        """Verify that elevated ML probability provides bounded lift on ambiguous text."""
        # Case B: Heuristic finds no specific hard rules (H=20.0), but ML detects strong scam markers (prob=0.85)
        heuristic_score = 20.0
        ml_prob = 0.85
        final_score = simulate_hybrid_combiner(heuristic_score, ml_prob)
        # Expected lift: ((0.85 - 0.65) / 0.35) * 25 = 14.3 -> final 34.3
        assert final_score > heuristic_score
        assert final_score == 34.3

    def test_non_dilutive_hybrid_combiner_low_ml_no_spurious_lift(self):
        """Verify that low ML probability does not alter a clean heuristic score."""
        heuristic_score = 0.0
        ml_prob = 0.45
        final_score = simulate_hybrid_combiner(heuristic_score, ml_prob)
        assert final_score == 0.0, "ML probability below 0.65 threshold must not inject artificial risk."

    def test_evidence_attribution_schema_compliance(self):
        """Verify that both heuristic and ML evidence comply with EvidenceSnippetSchema."""
        heuristic_snippet = EvidenceSnippetSchema(
            id="evi-fee-01",
            text="Refundable deposit of Rs 2500 demanded",
            attribution="heuristic_rule",
            impact_score=55.0,
            reason="Mandatory upfront fee request violates fair recruitment standards.",
        )
        assert heuristic_snippet.attribution == "heuristic_rule"

        ml_snippet = EvidenceSnippetSchema(
            id="evi-ml-prob-01",
            text="High similarity to historical advance-fee clerical scam corpus",
            attribution="ml_feature",
            impact_score=14.3,
            reason="Machine learning classifier detected statistical scam language (confidence: 85%).",
        )
        assert ml_snippet.attribution == "ml_feature"
