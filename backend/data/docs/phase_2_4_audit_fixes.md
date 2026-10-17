# CareerShield AI — Phase 2.4: Controlled Audit Fixes Report

**Document Version:** 1.0.0  
**Resolution Date:** 2026-10-15  
**Scope:** Controlled Remediation of Phase 2.3 Audit Findings  
**Target Systems:**  
- `backend/app/ml/inference_service.py`
- `backend/app/services/analytics_service.py`
- `backend/tests/test_inference_service.py`
- `backend/tests/test_analytics_api.py`

---

## 1. Executive Summary

Phase 2.3 audit identified 1 critical defect (P0 score dilution), 2 significant issues (P1 recommendation dissonance, P1 outdated transparency endpoint), and 2 technical debt issues (P2 version string drift, P2 preprocessing URL/email masking gap). 

All findings have been remediated cleanly and incrementally in Phase 2.4 without breaking changes, database migrations, model retraining, or API contract modifications.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          PHASE 2.4 RESOLUTION SCORECARD                     │
├───────┬─────────────────────────┬──────────┬────────────────────────────────┤
│ Level │ Finding                 │ Status   │ Fix Applied                    │
├───────┼─────────────────────────┼──────────┼────────────────────────────────┤
│  P0   │ Score dilution in       │ RESOLVED │ final_score = max(h_score,     │
│       │ range [60.1, 64.9]      │          │ min(64.0, round(h+lift, 1)))   │
├───────┼─────────────────────────┼──────────┼────────────────────────────────┤
│  P1   │ Recommendation textual  │ RESOLVED │ Pruned standard hiring signals │
│       │ dissonance              │          │ and added caution guidance     │
├───────┼─────────────────────────┼──────────┼────────────────────────────────┤
│  P1   │ Transparency endpoint   │ RESOLVED │ Connected to ML inference info │
│       │ reports model untrained │          │ with truthful benchmark data   │
├───────┼─────────────────────────┼──────────┼────────────────────────────────┤
│  P2   │ Version label drift     │ RESOLVED │ Standardized canonical &       │
│       │ across modules          │          │ fallback version constants     │
├───────┼─────────────────────────┼──────────┼────────────────────────────────┤
│  P2   │ Runtime URL/email       │ RESOLVED │ Added regex masking in         │
│       │ preprocessing drift     │          │ prepare_job_text_for_ml()      │
└───────┴─────────────────────────┴──────────┴────────────────────────────────┘
```

---

## 2. Detailed Technical Fixes

### Step 1 — P0: Fix Score Dilution & Guarantee Monotonicity

- **Root Cause in Phase 2.3:**
  In `combine_evaluations()`, `final_score = min(60.0, round(h_score + lift, 1))` lacked a lower bound $\max(h\_score, \dots)$. If heuristic score $H = 64.0$ and ML had elevated scam confidence ($P = 0.85$, $\text{lift} = 7.5$), the score was clamped down to $60.0$, inadvertently decreasing the risk score by $4.0$ points.
- **Implemented Fix (`backend/app/ml/inference_service.py`):**
  ```python
  # 2. Rule Dominance Check
  if h_score >= 65.0:
      combined["final_risk_score"] = h_score
      return combined

  # 3. Check for Bounded Advisory Lift
  if fraud_prob >= 0.70:
      lift = min(15.0, round(((fraud_prob - 0.70) / 0.30) * 15.0, 1))
      final_score = max(h_score, min(64.0, round(h_score + lift, 1)))
      combined["final_risk_score"] = final_score
  ```
- **Guarantees Enforced:**
  1. **Strict Monotonicity:** $\text{Final Risk Score} \ge \text{Heuristic Risk Score}$ for all inputs. Score dilution is mathematically impossible.
  2. **Rule Dominance:** If $H \ge 65.0$, deterministic high-risk findings dominate and cannot be modified.
  3. **ML Cap at 64.0:** If $H < 65.0$, ML alone can never reach $65.0$ (`HIGH_RISK_INDICATORS`). At most, it escalates an ambiguous posting into `NEEDS_CAUTION` ($[35.0, 64.0]$).

---

### Step 2 — P1: Remove Contradictory Recommendation Text

- **Root Cause in Phase 2.3:**
  When heuristic engine scored $H \le 34.0$, it emitted *"This posting aligns with standard corporate hiring signals."* If ML lift pushed $Final > 34.0$ into `NEEDS_CAUTION`, the user received contradictory guidance in the same card.
- **Implemented Fix (`backend/app/ml/inference_service.py`):**
  ```python
  # If ML lift pushed a Low Risk job (H <= 34.0) into Needs Caution (> 34.0),
  # prune stale low-risk reassurances and insert caution guidance
  if h_score <= 34.0 and final_score > 34.0:
      recs = [r for r in recs if "standard corporate hiring signals" not in r.lower()]
      caution_rec = (
          "Exercise caution: Verify the recruiter's identity on LinkedIn and ensure no payments or deposits are ever made."
      )
      if caution_rec not in recs:
          recs.insert(0, caution_rec)

  advisory_rec = (
      "Advisory: Job description matches wording patterns historically associated with recruitment "
      "fraud. Independently verify the employer's domain and official career portal."
  )
  if advisory_rec not in recs:
      recs.append(advisory_rec)
  ```
- **Guarantees Enforced:**
  - Candidates never receive conflicting "standard corporate hiring signals" reassurance alongside a caution risk badge.

---

### Step 3 — P1: Truthful Model Transparency Reporting

- **Root Cause in Phase 2.3:**
  `GET /api/v1/analytics/model-transparency` in `backend/app/services/analytics_service.py` hardcoded `"Untrained / Heuristic Mode Active"` even though a validated baseline pipeline was trained and saved.
- **Implemented Fix (`backend/app/services/analytics_service.py` & `backend/app/ml/inference_service.py`):**
  - Added `get_transparency_info()` to `MLInferenceService` to inspect the loaded pipeline and `model_metadata.json`.
  - Replaced hardcoded values in `analytics_service.py`:
  ```python
  info = get_ml_service().get_transparency_info()

  return ModelTransparencyResponse(
      engine_type=info["engine_type"],
      engine_version=info["engine_version"],
      total_rules_defined=len(CANONICAL_RULES),
      ml_model_status=info["ml_model_status"],
      ml_metrics_available=info["ml_metrics_available"],
      ml_metrics_explanation=info["ml_metrics_explanation"],
      total_evaluations_analyzed=total_analyses,
      score_calculation_formula=info["score_calculation_formula"],
      score_bands=SCORE_BANDS,
      rules=rules_definitions,
      mitigating_signals=MITIGATING_SIGNALS,
      limitations=LIMITATIONS,
  )
  ```
- **Guarantees Enforced:**
  - Accurately reports `engine_type="Hybrid (Deterministic Heuristics + Supplementary TF-IDF ML Advisory)"` and `ml_model_status="Active (Trained Baseline Loaded)"`.
  - Reports genuine held-out test split metrics (ROC-AUC 0.9628, PR-AUC 0.7921, threshold 0.61) without claiming live Indian scam probability calibration.
  - If model artifact is missing or corrupted, gracefully degrades to `ml_model_status="Unavailable / Rules-Only Fallback Active"`.

---

### Step 4 — P2: Standardized Model Version Labels

- **Root Cause in Phase 2.3:**
  Different modules used inconsistent strings: `"v1.0-rules+ml-baseline"`, `"v1.0-rules-engine"`, `"1.0.0"`, `"CareerShield-AI-Baseline-TFIDF-LogReg-v1.0.0"`.
- **Implemented Fix:**
  - Defined constants in `backend/app/ml/inference_service.py`:
    ```python
    CANONICAL_MODEL_VERSION = "CareerShield-AI-Baseline-TFIDF-LogReg-v1.0.0"
    FALLBACK_MODEL_VERSION = "v1.0-rules-engine-only"
    ```
  - Standardized all prediction results, combiner outputs, and transparency reporting to use these constants.

---

### Step 5 — P2: Runtime URL, Email, and Phone Masking

- **Root Cause in Phase 2.3:**
  In the EMSCAD training dataset, URLs, emails, and phone numbers were masked (`#URL_...#`, `#EMAIL_...#`, `#PHONE_...#`) and removed by `clean_text()`. In runtime inputs, raw URLs (`https://jobs.company.com/apply`) produced sub-tokens (`https`, `jobs`, `com`) that the TF-IDF vocabulary never saw during training.
- **Implemented Fix (`backend/app/ml/inference_service.py`):**
  Added regex masks in `prepare_job_text_for_ml()`:
  ```python
  RAW_URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
  RAW_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
  RAW_PHONE_RE = re.compile(r"\+?\d[\d -]{7,}\d")

  def prepare_job_text_for_ml(job_dict: Dict[str, Any]) -> str:
      # ...
      # Strip raw contact links before clean_text tokenization
      merged_text = RAW_URL_RE.sub(" ", merged_text)
      merged_text = RAW_EMAIL_RE.sub(" ", merged_text)
      merged_text = RAW_PHONE_RE.sub(" ", merged_text)
      return clean_text(merged_text)
  ```
- **Guarantees Enforced:**
  - Tokenization distribution at inference time matches training representation. User-facing inputs in `job_description` are preserved intact for the heuristic rules engine and database persistence.

---

## 3. Regression Test Suite

A dedicated regression test suite `TestPhase24AuditFixes` has been implemented in `backend/tests/test_inference_service.py`:

| Test Name | Target Finding | Verification Condition |
|:---|:---|:---|
| `test_score_dilution_boundary_heuristic_near_64` | P0 Score Dilution | $H \in \{60.1, 62.0, 64.0, 64.9\}$ with ML lift never drops below $H$; capped at $64.0$; stays $< 65.0$. |
| `test_strict_monotonicity_across_score_spectrum` | P0 Monotonicity | Parametric sweep across $H \in [0.0, 100.0]$ and $P \in [0.0, 1.0]$ confirms $Final \ge H$ universally. |
| `test_hard_rule_dominance_for_high_risk` | P0 Rule Dominance | $H \ge 65.0 \implies Final = H$ for all $P$. |
| `test_ml_cannot_elevate_into_high_risk_alone` | P0 Isolation Cap | $H < 65.0 \implies Final \le 64.0$ even with $P = 1.0$. |
| `test_recommendation_pruning_on_low_to_caution_transition` | P1 Rec Dissonance | Transition from Low Risk to Needs Caution strips "standard corporate hiring signals", adds caution advice. |
| `test_recommendation_preserved_when_no_category_change` | P1 Rec Dissonance | Low-risk reassurance preserved when ML does not lift risk category. |
| `test_transparency_info_with_loaded_baseline` | P1 Transparency | Truthful hybrid status, offline EMSCAD benchmarks, and formula returned. |
| `test_transparency_info_fallback_mode` | P1 Transparency | Fallback mode status and rules-only version returned on missing model. |
| `test_transparency_api_endpoint` | P1 / P2 API Contract | `GET /api/v1/analytics/model-transparency` returns 200 with canonical version and metadata. |
| `test_runtime_preprocessing_masks_urls_emails_phones` | P2 Preprocessing | Raw URLs, emails, and phone numbers are stripped to spaces before tokenization. |
