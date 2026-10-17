"""End-to-end reproducible baseline ML training script for CareerShield AI.

Trains TF-IDF + Balanced Logistic Regression pipeline with:
- Zero data-leakage deduplication
- Stratified 80/20 train/test partition (random_state=42)
- Out-of-fold cross-validation on training data for threshold selection
- Comprehensive test set evaluation (Precision, Recall, F1, PR-AUC, Confusion Matrix)
- Model serialization to backend/artifacts/models/

Usage:
    cd backend
    python -m app.ml.train_baseline
"""

import json
import os
from pathlib import Path
import time
from typing import Any, Dict

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split
from sklearn.pipeline import Pipeline

from app.ml.evaluator import compute_metrics, extract_top_features, find_optimal_threshold
from app.ml.preprocessing import combine_text_fields, deduplicate_postings

# Paths
BASE_DIR = Path(__file__).resolve().parents[2]
RAW_CSV_PATH = BASE_DIR / "data" / "raw" / "fake_job_postings.csv"
ARTIFACTS_DIR = BASE_DIR / "artifacts" / "models"
DOCS_DIR = BASE_DIR / "data" / "docs"
EVALUATION_REPORT_PATH = DOCS_DIR / "model_evaluation_report.md"


def run_training_pipeline(
    csv_path: Path = RAW_CSV_PATH,
    artifacts_dir: Path = ARTIFACTS_DIR,
    random_state: int = 42,
    max_features: int = 10000,
) -> Dict[str, Any]:
    """Execute end-to-end baseline training pipeline."""
    start_time = time.time()
    print("=" * 80)
    print("CareerShield AI — Phase 2 Baseline ML Pipeline")
    print(f"Dataset: {csv_path}")
    print(f"Artifacts Destination: {artifacts_dir}")
    print("=" * 80)

    if not csv_path.exists():
        raise FileNotFoundError(f"Dataset not found at: {csv_path}")

    # 1. Load Raw Dataset
    print("\n[Step 1/6] Loading raw dataset...")
    df = pd.read_csv(csv_path)
    raw_rows, raw_cols = df.shape
    print(f"  - Raw Records: {raw_rows:,} rows, {raw_cols} columns")

    # 2. Prevent Train/Test Data Leakage via Deduplication
    print("\n[Step 2/6] Inspecting and removing duplicate postings to prevent data leakage...")
    df_clean, removed_count = deduplicate_postings(df)
    clean_rows = len(df_clean)
    print(f"  - Duplicate postings removed: {removed_count:,}")
    print(f"  - Clean unique postings:     {clean_rows:,}")
    print(f"  - Unique Genuine (0):        {(df_clean['fraudulent'] == 0).sum():,} ({(df_clean['fraudulent'] == 0).mean()*100:.2f}%)")
    print(f"  - Unique Fraudulent (1):     {(df_clean['fraudulent'] == 1).sum():,} ({(df_clean['fraudulent'] == 1).mean()*100:.2f}%)")

    # 3. Preprocess and Combine Text Fields
    print("\n[Step 3/6] Preprocessing and concatenating text features...")
    X_text = combine_text_fields(df_clean)
    y = df_clean["fraudulent"].values.astype(int)

    # 4. Stratified 80/20 Train/Test Split
    print("\n[Step 4/6] Creating stratified 80/20 train/test partition (random_state=42)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X_text,
        y,
        test_size=0.20,
        stratify=y,
        random_state=random_state,
    )
    print(f"  - Training Set: {len(X_train):,} samples (Fraud rate: {y_train.mean()*100:.2f}%, {y_train.sum()} scams)")
    print(f"  - Test Set:     {len(X_test):,} samples (Fraud rate: {y_test.mean()*100:.2f}%, {y_test.sum()} scams)")

    # 5. Pipeline Construction & Out-of-Fold Validation for Threshold Selection
    print("\n[Step 5/6] Cross-validating on training data for threshold selection...")
    pipeline = Pipeline([
        (
            "tfidf",
            TfidfVectorizer(
                ngram_range=(1, 2),
                max_features=max_features,
                stop_words="english",
                sublinear_tf=True,
            ),
        ),
        (
            "clf",
            LogisticRegression(
                class_weight="balanced",
                solver="liblinear",
                C=1.0,
                max_iter=1000,
                random_state=random_state,
            ),
        ),
    ])

    # 5-fold cross validation strictly on training split
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=random_state)
    val_proba = cross_val_predict(
        pipeline,
        X_train,
        y_train,
        cv=cv,
        method="predict_proba",
        n_jobs=-1,
    )[:, 1]

    optimal_threshold, val_f1 = find_optimal_threshold(y_train, val_proba, metric="f1")
    print(f"  - Validation Optimal Threshold (max F1): {optimal_threshold:.4f} (Validation F1: {val_f1:.4f})")

    # Fit final pipeline on 100% of training data
    print("\n[Step 6/6] Fitting final pipeline on 100% of training data & evaluating on held-out test set...")
    pipeline.fit(X_train, y_train)

    # Predict on held-out test set
    test_proba = pipeline.predict_proba(X_test)[:, 1]

    # Evaluate at default 0.50 threshold
    metrics_default = compute_metrics(y_test, test_proba, threshold=0.50)
    # Evaluate at validation-selected optimal threshold
    metrics_tuned = compute_metrics(y_test, test_proba, threshold=optimal_threshold)

    # Extract top predictive features
    vectorizer = pipeline.named_steps["tfidf"]
    classifier = pipeline.named_steps["clf"]
    feature_insights = extract_top_features(vectorizer, classifier, top_n=15)

    print("\n" + "=" * 80)
    print("HELD-OUT TEST SET EVALUATION RESULTS:")
    print("=" * 80)
    print(f"1. Default Threshold (0.50):")
    print(f"   - Fraud Precision: {metrics_default['fraud_class']['precision']:.4f}")
    print(f"   - Fraud Recall:    {metrics_default['fraud_class']['recall']:.4f}")
    print(f"   - Fraud F1-Score:  {metrics_default['fraud_class']['f1_score']:.4f}")
    print(f"   - Macro F1-Score:  {metrics_default['macro_avg']['f1_score']:.4f}")
    print(f"   - PR-AUC:          {metrics_default['pr_auc']:.4f}")
    print(f"   - ROC-AUC:         {metrics_default['roc_auc']:.4f}")
    print(f"   - Confusion Matrix: TN={metrics_default['confusion_matrix']['tn']}, FP={metrics_default['confusion_matrix']['fp']}, FN={metrics_default['confusion_matrix']['fn']}, TP={metrics_default['confusion_matrix']['tp']}")

    print(f"\n2. Validation-Tuned Threshold ({optimal_threshold:.4f}):")
    print(f"   - Fraud Precision: {metrics_tuned['fraud_class']['precision']:.4f}")
    print(f"   - Fraud Recall:    {metrics_tuned['fraud_class']['recall']:.4f}")
    print(f"   - Fraud F1-Score:  {metrics_tuned['fraud_class']['f1_score']:.4f}")
    print(f"   - Macro F1-Score:  {metrics_tuned['macro_avg']['f1_score']:.4f}")
    print(f"   - Confusion Matrix: TN={metrics_tuned['confusion_matrix']['tn']}, FP={metrics_tuned['confusion_matrix']['fp']}, FN={metrics_tuned['confusion_matrix']['fn']}, TP={metrics_tuned['confusion_matrix']['tp']}")

    print("\nTop 10 N-Grams Associated with Fraud:")
    for term, score in feature_insights["top_fraud_indicators"][:10]:
        print(f"   + {term:<25}: {score:+.4f}")

    print("\nTop 10 N-Grams Associated with Legitimate Postings:")
    for term, score in feature_insights["top_genuine_indicators"][:10]:
        print(f"   - {term:<25}: {score:+.4f}")

    # Serialize Artifacts
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    model_path = artifacts_dir / "baseline_pipeline.joblib"
    metadata_path = artifacts_dir / "model_metadata.json"

    joblib.dump(pipeline, model_path)
    print(f"\n[INFO] Serialized pipeline saved to: {model_path}")

    elapsed_time = round(time.time() - start_time, 2)
    metadata = {
        "model_name": "CareerShield-AI-Baseline-TFIDF-LogReg",
        "model_version": "1.0.0",
        "created_at_utc": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
        "dataset_source": "EMSCAD (fake_job_postings.csv)",
        "training_time_seconds": elapsed_time,
        "data_leakage_safeguards": {
            "deduplication_performed": True,
            "raw_samples": raw_rows,
            "clean_unique_samples": clean_rows,
            "duplicate_records_removed": removed_count,
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "split_ratio": "80/20",
            "stratified": True,
            "random_state": random_state,
        },
        "hyperparameters": {
            "vectorizer": {
                "ngram_range": [1, 2],
                "max_features": max_features,
                "sublinear_tf": True,
                "stop_words": "english",
            },
            "classifier": {
                "algorithm": "LogisticRegression",
                "class_weight": "balanced",
                "solver": "liblinear",
                "C": 1.0,
                "max_iter": 1000,
                "random_state": random_state,
            },
        },
        "validation_strategy": {
            "method": "5-Fold Stratified Cross-Validation on Training Split",
            "optimal_threshold": optimal_threshold,
            "validation_f1_at_optimal_threshold": val_f1,
        },
        "held_out_test_metrics_default_threshold_0_50": metrics_default,
        "held_out_test_metrics_tuned_threshold": metrics_tuned,
        "top_features": feature_insights,
    }

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"[INFO] Metadata saved to: {metadata_path}")

    return metadata


if __name__ == "__main__":
    run_training_pipeline()
