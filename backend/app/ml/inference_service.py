"""Isolated ML inference and advisory scoring service for CareerShield AI.

Provides safe, lazy loading of serialized pipeline artifacts, consistent
preprocessing alignment with training distribution, and non-dilutive
signal combination with the deterministic heuristic rules engine.
"""

from dataclasses import dataclass, field
import json
import logging
from pathlib import Path
import re
import threading
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np

from app.core.config import settings
from app.ml.preprocessing import clean_text
from app.ml.rules_engine import map_score_to_risk_level

logger = logging.getLogger("careershield.ml")

# Canonical version constants
CANONICAL_MODEL_VERSION = "CareerShield-AI-Baseline-TFIDF-LogReg-v1.0.0"
FALLBACK_MODEL_VERSION = "v1.0-rules-engine-only"

# Regex patterns for runtime URL, email, and phone normalization
# Matching EMSCAD training preprocessing where URLs, emails, and phones were masked and stripped
RAW_URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
RAW_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
RAW_PHONE_RE = re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,5}\)?[-.\s]?\d{3,5}[-.\s]?\d{3,5}")


def prepare_job_text_for_ml(data: Dict[str, Any]) -> str:
    """
    Preprocess runtime job opportunity payload into exact training representation.
    
    Mirrors training pipeline's `combine_text_fields`:
    1. Mask raw URLs, emails, and phone numbers in job description to spaces.
       This prevents unmasked URLs/domains from creating noisy out-of-vocabulary n-grams,
       matching EMSCAD training data where URLs/emails/phones were masked and stripped.
    2. Combines job_title, company_name, and masked job_description with single spaces.
    3. Applies `clean_text` (HTML stripping, entity unescaping, placeholder
       removal, lowercasing, and whitespace normalization).
    """
    title = str(data.get("job_title") or "").strip()
    company = str(data.get("company_name") or "").strip()
    description = str(data.get("job_description") or "").strip()

    # Safely mask raw URLs, emails, and phone numbers in description
    description_masked = RAW_URL_RE.sub(" ", description)
    description_masked = RAW_EMAIL_RE.sub(" ", description_masked)
    description_masked = RAW_PHONE_RE.sub(" ", description_masked)

    parts = [p for p in (title, company, description_masked) if p]
    raw_combined = " ".join(parts)
    return clean_text(raw_combined)


@dataclass
class MLInferenceResult:
    """Structured internal result of ML model inference."""

    is_available: bool
    ml_risk_score: float  # 0.0 to 100.0
    fraud_probability: Optional[float]  # 0.0 to 1.0 or None
    status: str  # "success", "unavailable", "insufficient_text", "error"
    model_version: str
    top_contributing_features: List[Tuple[str, float]] = field(default_factory=list)
    advisory_note: Optional[str] = None


class MLInferenceService:
    """Thread-safe, lazy-loading ML model inference manager."""

    def __init__(
        self,
        model_path: Optional[Path] = None,
        metadata_path: Optional[Path] = None,
    ):
        self.model_path = (
            model_path
            if model_path is not None
            else settings.model_artifacts_path / "baseline_pipeline.joblib"
        )
        self.metadata_path = (
            metadata_path
            if metadata_path is not None
            else settings.model_artifacts_path / "model_metadata.json"
        )

        self._pipeline = None
        self._metadata: Optional[Dict[str, Any]] = None
        self._is_available: bool = False
        self._pipeline_loaded: bool = False
        self._lock = threading.Lock()
        self.model_version = FALLBACK_MODEL_VERSION

    @property
    def is_available(self) -> bool:
        """Return True if model pipeline is loaded and available for inference."""
        self._ensure_loaded()
        return bool(self._is_available and self._pipeline is not None)

    @property
    def version(self) -> str:
        """Return canonical or fallback model version string."""
        self._ensure_loaded()
        return self.model_version

    def _ensure_loaded(self) -> None:
        """Lazily load serialized pipeline and metadata on first inference."""
        if self._pipeline_loaded:
            return

        with self._lock:
            if self._pipeline_loaded:
                return

            try:
                if not self.model_path.exists():
                    logger.warning(
                        "ML model artifact not found at %s. Operating in rule-only mode.",
                        self.model_path,
                    )
                    self._is_available = False
                    self._pipeline = None
                    self.model_version = FALLBACK_MODEL_VERSION
                    return

                # Load serialized pipeline
                self._pipeline = joblib.load(self.model_path)
                self._is_available = True
                self.model_version = CANONICAL_MODEL_VERSION

                # Load metadata if present
                if self.metadata_path.exists():
                    try:
                        with open(self.metadata_path, "r", encoding="utf-8") as f:
                            self._metadata = json.load(f)
                    except Exception as meta_err:
                        logger.warning("Could not read model metadata: %s", str(meta_err))

                logger.info("Successfully loaded ML model pipeline: %s", self.model_version)

            except Exception as load_err:
                logger.warning(
                    "Failed to deserialize ML model pipeline: %s. Operating in rule-only fallback mode.",
                    str(load_err),
                )
                self._is_available = False
                self._pipeline = None
                self.model_version = FALLBACK_MODEL_VERSION
            finally:
                self._pipeline_loaded = True

    def predict(self, data: Dict[str, Any]) -> MLInferenceResult:
        """
        Execute safe inference on a job posting dictionary.
        
        Guarantees:
        - Never throws unhandled exceptions or leaks traces.
        - Returns fallback result if artifact is missing or corrupted.
        - Preprocesses text using canonical training representation with URL/email masking.
        - Returns structured metadata with explainable contributing features.
        """
        self._ensure_loaded()

        if not self._is_available or self._pipeline is None:
            return MLInferenceResult(
                is_available=False,
                ml_risk_score=0.0,
                fraud_probability=None,
                status="unavailable",
                model_version=self.model_version,
                top_contributing_features=[],
                advisory_note=None,
            )

        # 1. Preprocess and align text
        cleaned_text = prepare_job_text_for_ml(data)

        # 2. Check for empty or trivial input
        if len(cleaned_text.strip()) < 10:
            return MLInferenceResult(
                is_available=True,
                ml_risk_score=0.0,
                fraud_probability=0.0,
                status="insufficient_text",
                model_version=self.model_version,
                top_contributing_features=[],
                advisory_note="Insufficient text content for statistical machine learning analysis.",
            )

        # 3. Execute inference safely
        try:
            probas = self._pipeline.predict_proba([cleaned_text])
            fraud_prob = float(probas[0][1])
            ml_risk_score = round(fraud_prob * 100.0, 1)

            # Extract top contributing features if possible
            top_features = self._extract_contributing_features(cleaned_text)

            advisory_note = None
            if fraud_prob >= 0.70:
                advisory_note = (
                    "Advisory: Job text displays wording patterns frequently observed in historical "
                    "recruitment scam datasets (statistical correlation, not verified proof)."
                )

            return MLInferenceResult(
                is_available=True,
                ml_risk_score=ml_risk_score,
                fraud_probability=round(fraud_prob, 4),
                status="success",
                model_version=self.model_version,
                top_contributing_features=top_features,
                advisory_note=advisory_note,
            )

        except Exception as inf_err:
            logger.warning("ML inference failed: %s. Returning fallback result.", str(inf_err))
            return MLInferenceResult(
                is_available=False,
                ml_risk_score=0.0,
                fraud_probability=None,
                status="error",
                model_version=self.model_version,
                top_contributing_features=[],
                advisory_note=None,
            )

    def _extract_contributing_features(
        self, cleaned_text: str, top_k: int = 5
    ) -> List[Tuple[str, float]]:
        """Extract top N-grams in the document with positive fraud coefficients."""
        try:
            if not hasattr(self._pipeline, "named_steps"):
                return []

            vectorizer = self._pipeline.named_steps.get("tfidf")
            classifier = self._pipeline.named_steps.get("clf")

            if not vectorizer or not classifier or not hasattr(classifier, "coef_"):
                return []

            # Vectorize single document
            X_doc = vectorizer.transform([cleaned_text])
            indices = X_doc.indices
            data_values = X_doc.data
            coef = classifier.coef_[0]
            feature_names = vectorizer.get_feature_names_out()

            contributions: List[Tuple[str, float]] = []
            for idx, tfidf_val in zip(indices, data_values):
                weight = coef[idx] * tfidf_val
                if weight > 0:  # Only features pushing towards scam class
                    contributions.append((str(feature_names[idx]), round(float(weight), 3)))

            # Sort by contribution descending
            contributions.sort(key=lambda x: x[1], reverse=True)
            return contributions[:top_k]

        except Exception:
            return []

    def get_transparency_info(self) -> Dict[str, Any]:
        """Return truthful transparency status and offline benchmark metrics."""
        self._ensure_loaded()
        if not self._is_available or self._pipeline is None:
            return {
                "engine_type": "Deterministic Heuristic Rules Engine (Rules-Only Fallback)",
                "engine_version": FALLBACK_MODEL_VERSION,
                "ml_model_status": "Unavailable / Rules-Only Fallback Active",
                "ml_metrics_available": False,
                "ml_metrics_explanation": (
                    "ML model artifact is unavailable or corrupt. Operating in deterministic rules-only fallback mode."
                ),
                "score_calculation_formula": (
                    "Final Risk Score = min(100.0, max(0.0, Raw Penalty Points - Mitigation Points)). "
                    "Operating in deterministic rules-only fallback mode."
                ),
            }

        metrics_available = False
        metrics_explanation = "Model artifact is loaded, but saved evaluation metadata is missing."

        if self._metadata and "held_out_test_metrics_tuned_threshold" in self._metadata:
            metrics_available = True
            m = self._metadata["held_out_test_metrics_tuned_threshold"]
            roc = self._metadata.get("held_out_test_metrics_default_threshold_0_50", {}).get("roc_auc", 0.9628)
            pr = m.get("pr_auc", 0.7921)
            prec = m.get("fraud_class", {}).get("precision", 0.7007)
            rec = m.get("fraud_class", {}).get("recall", 0.7442)
            thresh = m.get("threshold", 0.61)
            metrics_explanation = (
                f"Historical offline benchmark on held-out test split (EMSCAD dataset, N=3,023, random_state=42): "
                f"ROC-AUC={roc:.4f}, PR-AUC={pr:.4f}, Fraud Precision={prec*100:.2f}%, Fraud Recall={rec*100:.2f}% "
                f"at cross-validation optimal threshold {thresh}. Note: Historical offline metrics reflect 2012–2014 data, "
                f"not real-world live Indian scam prevalence."
            )

        formula = (
            "Hybrid scoring: Deterministic heuristic rules are authoritative. "
            "If Heuristic Score >= 65.0, Final Score = Heuristic Score (Hard Rule Dominance). "
            "If Heuristic Score < 65.0 and ML Fraud Probability >= 0.70, "
            "Final Score = max(Heuristic Score, min(64.0, round(Heuristic Score + Bounded Advisory Lift, 1))), "
            "where Lift = min(15.0, round(((P - 0.70) / 0.30) * 15.0, 1)). "
            "Otherwise, Final Score = Heuristic Score."
        )

        benchmark_metrics = None
        if metrics_available:
            benchmark_metrics = {
                "dataset_name": "EMSCAD Dataset (Held-Out Test Split, N=3,023, random_state=42)",
                "test_split_size": 3023,
                "roc_auc": round(float(roc), 4),
                "pr_auc": round(float(pr), 4),
                "fraud_precision": round(float(prec * 100.0), 2),
                "fraud_recall": round(float(rec * 100.0), 2),
                "threshold": round(float(thresh), 2),
                "caveat": "Historical offline benchmark on held-out test split, not live Indian scam prevalence.",
            }

        return {
            "engine_type": "Hybrid (Deterministic Heuristics + Supplementary TF-IDF ML Advisory)",
            "engine_version": CANONICAL_MODEL_VERSION,
            "ml_model_status": "Active (Trained Baseline Loaded)",
            "ml_metrics_available": metrics_available,
            "ml_metrics_explanation": metrics_explanation,
            "score_calculation_formula": formula,
            "benchmark_metrics": benchmark_metrics,
        }


# Module singleton
_inference_service_instance = MLInferenceService()


def get_ml_service() -> MLInferenceService:
    """Access module singleton MLInferenceService."""
    return _inference_service_instance


def combine_evaluations(
    heuristic_eval: Dict[str, Any],
    ml_result: MLInferenceResult,
) -> Dict[str, Any]:
    """
    Combine deterministic rules engine results with supplementary ML advisory score.
    
    Asymmetric Rule-Dominant Combination Logic:
    1. Hard Rule Dominance:
       If heuristic_risk_score >= 65.0 (High Risk), heuristic findings dominate 100%.
       A low ML score can NEVER dilute or reduce a confirmed policy violation
       (e.g., upfront fees or MNC impersonation).
       
    2. Fallback / Neutrality:
       If ML model is unavailable, errored, or fraud probability < 0.70,
       final_risk_score = heuristic_risk_score (no change).
       
    3. Bounded Advisory Lift & Strict Monotonicity:
       If heuristic_risk_score < 65.0 AND fraud probability >= 0.70:
       lift = min(15.0, round(((fraud_prob - 0.70) / 0.30) * 15.0, 1))
       final_score = max(h_score, min(64.0, round(h_score + lift, 1)))
       
       Guarantees:
       - Monotonicity: final_score >= h_score for all inputs (zero score dilution).
       - Capping at 64.0 ensures ML ALONE NEVER classifies a job as HIGH_RISK_INDICATORS (>= 65.0).
       - It can at most escalate an ambiguous job into NEEDS_CAUTION (35.0-64.0).
       
    4. Recommendation Consistency:
       If ML lift elevates a Low Risk job (H <= 34.0) into Needs Caution (> 34.0),
       stale low-risk reassurances ("standard corporate hiring signals") are pruned
       and caution/advisory recommendations are ensured.
    """
    combined = dict(heuristic_eval)
    h_score = float(heuristic_eval.get("heuristic_risk_score", 0.0))

    # 1. Model Availability & Score Population
    if not ml_result.is_available or ml_result.fraud_probability is None:
        combined["ml_risk_score"] = 0.0
        combined["model_version"] = FALLBACK_MODEL_VERSION
        combined["final_risk_score"] = h_score
        combined["risk_level"] = map_score_to_risk_level(h_score)
        return combined

    combined["ml_risk_score"] = ml_result.ml_risk_score
    combined["model_version"] = ml_result.model_version
    fraud_prob = ml_result.fraud_probability

    # 2. Rule Dominance Check
    if h_score >= 65.0:
        # High-risk deterministic rules dominate; no dilution or modification
        combined["final_risk_score"] = h_score
        combined["risk_level"] = "HIGH_RISK_INDICATORS"
        return combined

    # 3. Check for Bounded Advisory Lift
    if fraud_prob >= 0.70:
        lift = min(15.0, round(((fraud_prob - 0.70) / 0.30) * 15.0, 1))
        # Monotonicity & Clamping:
        # Guaranteed: final_score >= h_score (never decreases score)
        # Guaranteed: final_score <= 64.0 (for h_score <= 64.0)
        # Guaranteed: final_score < 65.0 (for all h_score < 65.0)
        final_score = max(h_score, min(64.0, round(h_score + lift, 1)))
        combined["final_risk_score"] = final_score
        combined["risk_level"] = map_score_to_risk_level(final_score)

        # Add explainable evidence snippet tagged as "ml_feature"
        import uuid

        evidence_list = list(combined.get("evidence_snippets", []))
        top_words = [f"'{word}'" for word, _ in ml_result.top_contributing_features[:3]]
        words_clause = f" (lexical markers: {', '.join(top_words)})" if top_words else ""

        evidence_list.append({
            "id": f"evi-ml-{uuid.uuid4().hex[:8]}",
            "text": f"Historical recruitment scam vocabulary match{words_clause}",
            "attribution": "ml_feature",
            "impact_score": lift,
            "reason": (
                f"Statistical classifier detected text patterns resembling historical scam postings "
                f"(model confidence: {ml_result.ml_risk_score}%). Advisory pattern only, not factual verification."
            ),
        })
        combined["evidence_snippets"] = evidence_list

        # Recommendation Consistency:
        recs = list(combined.get("recommendations", []))

        # If ML lift pushed a Low Risk job (H <= 34.0) into Needs Caution (> 34.0),
        # prune stale low-risk reassurances and insert caution guidance
        if h_score <= 34.0 and final_score > 34.0:
            recs = [r for r in recs if "standard corporate hiring signals" not in r.lower()]
            caution_rec = (
                "Exercise caution: Verify the recruiter's identity on LinkedIn and ensure no payments or deposits are ever made."
            )
            if caution_rec not in recs:
                recs.insert(0, caution_rec)

        # Add ML advisory recommendation if not already present
        advisory_rec = (
            "Advisory: Job description matches wording patterns historically associated with recruitment "
            "fraud. Independently verify the employer's domain and official career portal."
        )
        if advisory_rec not in recs:
            recs.append(advisory_rec)

        combined["recommendations"] = recs

    else:
        # No lift applied
        combined["final_risk_score"] = h_score
        combined["risk_level"] = map_score_to_risk_level(h_score)

    return combined
