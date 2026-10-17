"""Unit and integration tests for CareerShield AI Phase 2 Baseline ML Pipeline.

Tests:
1. Text preprocessing & HTML tag stripping (clean_text).
2. Multi-field text concatenation (combine_text_fields).
3. Data leakage prevention & deduplication (deduplicate_postings).
4. Model evaluation metrics computation (compute_metrics, find_optimal_threshold).
5. Feature extraction (extract_top_features).
6. Scikit-learn Pipeline serialization & artifact loading sanity.
"""

from pathlib import Path
import tempfile
import joblib
import numpy as np
import pandas as pd
import pytest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from app.ml.evaluator import (
    compute_metrics,
    extract_top_features,
    find_optimal_threshold,
)
from app.ml.preprocessing import (
    clean_text,
    combine_text_fields,
    compute_text_fingerprint,
    deduplicate_postings,
)


class TestPreprocessing:
    """Test text cleaning and preprocessing functions."""

    def test_clean_text_basic(self):
        raw = "   Senior Python Engineer with AWS experience!   "
        assert clean_text(raw) == "senior python engineer with aws experience!"

    def test_clean_text_html_stripping(self):
        raw = "<p>Join our team at <b>Acme Corp</b>.<br/>Visit our <a href='#'>portal</a>.</p>"
        cleaned = clean_text(raw)
        assert "<" not in cleaned
        assert ">" not in cleaned
        assert "join our team at acme corp" in cleaned
        assert "portal" in cleaned

    def test_clean_text_html_entities(self):
        raw = "We offer AT&amp;T perks &quot;benefits&quot; &lt;awesome&gt;"
        cleaned = clean_text(raw)
        assert "at&t" in cleaned
        assert '"benefits"' in cleaned

    def test_clean_text_placeholder_masks(self):
        raw = "Contact us at #EMAIL_897dfb1f33f6c34f2bed521623e9808aa4e62d89a6c0284cfe89393e4457e628# or #URL_ec64af2b4fe2ca316e828f93b0cd098c22f8beba98dcac09d4dd7384b221a5e8#"
        cleaned = clean_text(raw)
        assert "#EMAIL_" not in cleaned
        assert "#URL_" not in cleaned
        assert "contact us at or" in cleaned

    def test_clean_text_null_and_empty(self):
        assert clean_text(None) == ""
        assert clean_text(np.nan) == ""
        assert clean_text("") == ""
        assert clean_text("   ") == ""

    def test_combine_text_fields(self):
        data = {
            "title": ["Software Engineer", "Data Entry"],
            "company_profile": ["Tech startup", np.nan],
            "description": ["Build cool APIs", "Type numbers into Excel"],
            "requirements": ["Python, Docker", "Fast typing"],
            "benefits": [np.nan, "Work from home"],
        }
        df = pd.DataFrame(data)
        combined = combine_text_fields(df, clean=True)

        assert len(combined) == 2
        assert "software engineer" in combined.iloc[0]
        assert "tech startup" in combined.iloc[0]
        assert "build cool apis" in combined.iloc[0]
        assert "python, docker" in combined.iloc[0]

        # Row 2 with NaNs handled gracefully
        assert "data entry" in combined.iloc[1]
        assert "type numbers into excel" in combined.iloc[1]
        assert "fast typing" in combined.iloc[1]
        assert "work from home" in combined.iloc[1]


class TestDataLeakageSafeguards:
    """Test deduplication and data leakage prevention logic."""

    def test_deduplicate_postings(self):
        # Create dataset with exact duplicate job posting
        data = {
            "job_id": [1, 2, 3, 4],
            "title": ["DevOps Engineer", "DevOps Engineer", "Product Manager", "DevOps Engineer"],
            "description": [
                "Manage Kubernetes clusters and CI/CD pipelines.",
                "Manage Kubernetes clusters and CI/CD pipelines.",  # Exact duplicate of #1
                "Lead product roadmaps and user discovery.",
                "Manage Kubernetes clusters and CI/CD pipelines with some extra text.",
            ],
            "fraudulent": [0, 0, 0, 0],
        }
        df = pd.DataFrame(data)
        deduped_df, removed_count = deduplicate_postings(df)

        assert removed_count == 1
        assert len(deduped_df) == 3
        # First duplicate kept (job_id 1)
        assert deduped_df.iloc[0]["job_id"] == 1
        # Second duplicate dropped (job_id 2)
        assert 2 not in deduped_df["job_id"].values

    def test_fingerprint_normalization(self):
        row1 = pd.Series({"title": "  Python Developer  ", "description": "<p>Build APIs</p>"})
        row2 = pd.Series({"title": "python developer", "description": "Build APIs"})
        assert compute_text_fingerprint(row1) == compute_text_fingerprint(row2)


class TestEvaluator:
    """Test evaluation metrics and threshold tuning."""

    def test_compute_metrics_known_synthetic(self):
        # Synthetic known ground truth and probabilities
        # 4 genuine, 4 fake
        y_true = np.array([0, 0, 0, 0, 1, 1, 1, 1])
        # High confidence for 3 fakes, 1 low confidence fake, 1 false alarm
        y_proba = np.array([0.1, 0.2, 0.3, 0.7, 0.2, 0.8, 0.9, 0.85])

        metrics = compute_metrics(y_true, y_proba, threshold=0.50)

        # Expected at threshold 0.50:
        # y_pred = [0, 0, 0, 1, 0, 1, 1, 1]
        # TN: 3 (indices 0, 1, 2)
        # FP: 1 (index 3)
        # FN: 1 (index 4)
        # TP: 3 (indices 5, 6, 7)
        cm = metrics["confusion_matrix"]
        assert cm["tn"] == 3
        assert cm["fp"] == 1
        assert cm["fn"] == 1
        assert cm["tp"] == 3

        # Precision = 3 / (3 + 1) = 0.75
        assert metrics["fraud_class"]["precision"] == 0.75
        # Recall = 3 / (3 + 1) = 0.75
        assert metrics["fraud_class"]["recall"] == 0.75
        # F1 = 0.75
        assert metrics["fraud_class"]["f1_score"] == 0.75

        assert metrics["pr_auc"] > 0.0
        assert metrics["roc_auc"] > 0.0

    def test_find_optimal_threshold(self):
        y_true = np.array([0, 0, 0, 0, 1, 1, 1, 1])
        y_proba = np.array([0.1, 0.2, 0.3, 0.4, 0.45, 0.6, 0.7, 0.8])

        thresh, score = find_optimal_threshold(y_true, y_proba, metric="f1")
        assert 0.10 <= thresh <= 0.90
        assert 0.0 <= score <= 1.0


class TestModelArtifacts:
    """Test serialization and loading of Scikit-Learn baseline pipeline."""

    def test_pipeline_serialization_and_inference(self):
        train_texts = [
            "We are hiring a Senior Software Engineer for Python and cloud computing.",
            "Earn easy money from home data entry wire transfer registration fee required.",
            "Frontend React developer wanted for modern UI design team.",
            "Urgent vacancy payment via Western Union send money to start immediate work.",
            "DevOps infrastructure lead for AWS Kubernetes and CI/CD pipelines.",
            "Work from home processing payments quick cash deposit guaranteed return.",
        ]
        train_labels = [0, 1, 0, 1, 0, 1]

        pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2))),
            ("clf", LogisticRegression(class_weight="balanced", random_state=42)),
        ])

        pipeline.fit(train_texts, train_labels)

        # Test feature extraction
        features = extract_top_features(pipeline.named_steps["tfidf"], pipeline.named_steps["clf"], top_n=3)
        assert len(features["top_fraud_indicators"]) <= 3
        assert len(features["top_genuine_indicators"]) <= 3

        # Test save and reload
        with tempfile.TemporaryDirectory() as tmp_dir:
            model_file = Path(tmp_dir) / "test_model.joblib"
            joblib.dump(pipeline, model_file)
            assert model_file.exists()

            loaded_model = joblib.load(model_file)
            test_query = ["Earn quick money with wire transfer registration fee"]
            proba = loaded_model.predict_proba(test_query)[0, 1]
            pred = loaded_model.predict(test_query)[0]

            assert isinstance(proba, float)
            assert proba >= 0.0 and proba <= 1.0
            assert pred in (0, 1)
