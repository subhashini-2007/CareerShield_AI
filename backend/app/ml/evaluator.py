"""Evaluation metrics and validation utilities for CareerShield AI ML models.

Computes confusion matrix, precision, recall, F1, macro F1, PR-AUC, and ROC-AUC
using proper cross-validation on training data for threshold selection.
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)


def find_optimal_threshold(
    y_true: np.ndarray,
    y_proba: np.ndarray,
    metric: str = "f1",
    num_thresholds: int = 81,
) -> Tuple[float, float]:
    """
    Find optimal classification decision threshold using validation / out-of-fold data.
    
    Tests thresholds from 0.10 to 0.90 with step 0.01.
    Never run this directly on the held-out test set to prevent leakage.
    
    Returns:
        Tuple of (best_threshold, best_metric_score)
    """
    thresholds = np.linspace(0.10, 0.90, num_thresholds)
    best_thresh = 0.50
    best_score = -1.0

    for t in thresholds:
        y_pred = (y_proba >= t).astype(int)
        if metric == "f1":
            score = f1_score(y_true, y_pred, pos_label=1, zero_division=0)
        elif metric == "recall":
            score = recall_score(y_true, y_pred, pos_label=1, zero_division=0)
        else:
            score = f1_score(y_true, y_pred, average="macro", zero_division=0)

        if score > best_score:
            best_score = score
            best_thresh = float(t)

    return round(best_thresh, 4), round(best_score, 4)


def compute_metrics(
    y_true: np.ndarray,
    y_proba: np.ndarray,
    threshold: float = 0.50,
) -> Dict[str, Any]:
    """
    Compute comprehensive evaluation metrics for binary recruitment fraud detection.
    
    Returns dictionary with:
    - confusion_matrix: [[TN, FP], [FN, TP]]
    - fraud_precision, fraud_recall, fraud_f1
    - genuine_precision, genuine_recall, genuine_f1
    - macro_f1
    - pr_auc (Average Precision Score)
    - roc_auc
    - total_samples, genuine_count, fraud_count
    """
    y_true = np.asarray(y_true)
    y_proba = np.asarray(y_proba)
    y_pred = (y_proba >= threshold).astype(int)

    cm = confusion_matrix(y_true, y_pred)
    # Ensure standard 2x2 shape
    if cm.shape == (2, 2):
        tn, fp, fn, tp = cm.ravel()
    else:
        tn, fp, fn, tp = int(cm[0, 0]), 0, 0, 0

    fraud_prec = float(precision_score(y_true, y_pred, pos_label=1, zero_division=0))
    fraud_rec = float(recall_score(y_true, y_pred, pos_label=1, zero_division=0))
    fraud_f1 = float(f1_score(y_true, y_pred, pos_label=1, zero_division=0))

    genuine_prec = float(precision_score(y_true, y_pred, pos_label=0, zero_division=0))
    genuine_rec = float(recall_score(y_true, y_pred, pos_label=0, zero_division=0))
    genuine_f1 = float(f1_score(y_true, y_pred, pos_label=0, zero_division=0))

    macro_f1 = float(f1_score(y_true, y_pred, average="macro", zero_division=0))

    try:
        pr_auc = float(average_precision_score(y_true, y_proba))
    except Exception:
        pr_auc = 0.0

    try:
        roc_auc = float(roc_auc_score(y_true, y_proba))
    except Exception:
        roc_auc = 0.0

    return {
        "threshold": float(threshold),
        "confusion_matrix": {
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
            "tp": int(tp),
        },
        "fraud_class": {
            "precision": round(fraud_prec, 4),
            "recall": round(fraud_rec, 4),
            "f1_score": round(fraud_f1, 4),
            "support": int(np.sum(y_true == 1)),
        },
        "genuine_class": {
            "precision": round(genuine_prec, 4),
            "recall": round(genuine_rec, 4),
            "f1_score": round(genuine_f1, 4),
            "support": int(np.sum(y_true == 0)),
        },
        "macro_avg": {
            "f1_score": round(macro_f1, 4),
        },
        "pr_auc": round(pr_auc, 4),
        "roc_auc": round(roc_auc, 4),
        "total_samples": int(len(y_true)),
    }


def extract_top_features(
    vectorizer: Any,
    classifier: Any,
    top_n: int = 20,
) -> Dict[str, List[Tuple[str, float]]]:
    """
    Extract top N n-grams with highest positive (fraud-indicative)
    and lowest negative (legitimacy-indicative) coefficients from Logistic Regression.
    """
    feature_names = vectorizer.get_feature_names_out()
    coef = classifier.coef_[0]

    # Top positive (fraud) features
    top_fraud_idx = np.argsort(coef)[-top_n:][::-1]
    top_fraud = [(str(feature_names[i]), round(float(coef[i]), 4)) for i in top_fraud_idx]

    # Top negative (genuine) features
    top_genuine_idx = np.argsort(coef)[:top_n]
    top_genuine = [(str(feature_names[i]), round(float(coef[i]), 4)) for i in top_genuine_idx]

    return {
        "top_fraud_indicators": top_fraud,
        "top_genuine_indicators": top_genuine,
    }
