# CareerShield AI — Phase 2.3: Targeted ML Integration Audit Report

**Document Version:** 1.0.0  
**Audit Date:** 2026-10-15  
**Audit Scope:** Read-Only Verification of Controlled ML Integration (Phase 2.2)  
**System Evaluated:** `CareerShield-AI-Baseline-TFIDF-LogReg` + `HeuristicRulesEngine`  
**Overall Readiness Verdict:** **NOT PRODUCTION-READY — ARCHITECTURAL DEFECTS IDENTIFIED**

---

## 1. Executive Summary & Verdict Scorecard

This audit evaluates the live implementation of Phase 2.2 controlled ML integration across `backend/app/ml/inference_service.py`, `backend/app/services/analyzer_service.py`, `backend/app/ml/preprocessing.py`, and related schemas and routes.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             AUDIT SCORECARD                                 │
├─────────────────────────────────────────┬─────────┬─────────────────────────┤
│ Evaluation Area                         │ Verdict │ Key Finding             │
├─────────────────────────────────────────┼─────────┼─────────────────────────┤
│ 1. Score / Category Consistency         │  FAIL   │ Score dilution defect   │
│                                         │         │ in (60.0, 65.0) range   │
├─────────────────────────────────────────┼─────────┼─────────────────────────┤
│ 2. Rule Dominance                       │  FAIL   │ Heuristic score reduced │
│                                         │         │ when ML fires at H=62   │
├─────────────────────────────────────────┼─────────┼─────────────────────────┤
│ 3. Fallback Behavior                    │  PASS   │ Clean degradation on    │
│                                         │         │ missing/corrupt models  │
├─────────────────────────────────────────┼─────────┼─────────────────────────┤
│ 4. Preprocessing Alignment              │ WARNING │ Field provenance and    │
│                                         │         │ URL/email masking drift │
├─────────────────────────────────────────┼─────────┼─────────────────────────┤
│ 5. Score Semantics                      │ WARNING │ Balanced posterior !=   │
│                                         │         │ real-world probability  │
├─────────────────────────────────────────┼─────────┼─────────────────────────┤
│ 6. Evidence Attribution                 │  PASS   │ Strict separation of    │
│                                         │         │ rule vs ml_feature      │
├─────────────────────────────────────────┼─────────┼─────────────────────────┤
│ 7. Persistence & API Compatibility      │ WARNING │ Transparency endpoint   │
│                                         │         │ reports model untrained │
├─────────────────────────────────────────┼─────────┼─────────────────────────┤
│ 8. Model Artifact / Versioning          │ WARNING │ 4 inconsistent version  │
│                                         │         │ strings across modules  │
└─────────────────────────────────────────┴─────────┴─────────────────────────┘
```

---

## 2. Detailed Findings by Verification Area

### Area 1 & 2: Score / Category Consistency & Rule Dominance

#### Finding 1.1: Score Dilution Bug in Heuristic Range [60.1, 64.9] (CRITICAL FAIL)
- **Location:** `backend/app/ml/inference_service.py`, function `combine_evaluations()`, lines 240–250.
- **Evidence:**
  ```python
  # 2. Rule Dominance Check
  if h_score >= 65.0:
      combined["final_risk_score"] = h_score
      return combined

  # 3. Check for Bounded Advisory Lift
  if fraud_prob >= 0.70:
      lift = min(15.0, round(((fraud_prob - 0.70) / 0.30) * 15.0, 1))
      # Cap at 60.0 so ML alone cannot reach HIGH_RISK_INDICATORS (>= 65.0)
      final_score = min(60.0, round(h_score + lift, 1))
      combined["final_risk_score"] = final_score
  ```
- **Analysis:**
  - If a job receives an existing heuristic risk score of **64.0** (`NEEDS_CAUTION`) and the ML model detects an elevated scam probability of $0.85$ ($\text{lift} = 7.5$ points):
    $$\text{sum} = 64.0 + 7.5 = 71.5$$
    $$\text{final\_score} = \min(60.0, 71.5) = \mathbf{60.0}$$
  - **The final score drops from 64.0 to 60.0!**
  - Instead of lifting or maintaining the risk score, the presence of an elevated ML fraud probability **reduces** the heuristic score by $4.0$ points.
  - This directly violates the core non-dilution safeguard: *"Existing rule findings must never be reduced by a low or high ML score."*
- **Root Cause:** The clamping formula applies $\min(60.0, \dots)$ without a $\max(h\_score, \dots)$ lower bound.
- **Remedy:** Must be corrected to:
  $$\text{final\_score} = \max(h\_score, \min(64.0, \text{round}(h\_score + \text{lift}, 1)))$$

#### Finding 1.2: Recommendation Textual Dissonance (WARNING)
- **Location:** `backend/app/ml/rules_engine.py:L452` and `backend/app/ml/inference_service.py:L283`.
- **Evidence:**
  When $H \le 34.0$, `rules_engine.py` appends:
  `"The posting exhibits standard corporate hiring signals. Always verify interview details via official company portals."`
  When ML lift pushes the final score into `NEEDS_CAUTION` ($Final \in [35.0, 60.0]$), `combine_evaluations()` prepends:
  `"Advisory: Job description matches wording patterns historically associated with recruitment fraud..."`
- **Analysis:**
  The candidate receives conflicting guidance in the same response: recommendation #1 states the posting exhibits *"standard corporate hiring signals"*, while recommendation #2 warns of *"historical recruitment fraud patterns"*, under a badge of `"Needs Caution"`.

---

### Area 3: Fallback Behavior (PASS)

- **Locations:** `backend/app/ml/inference_service.py:L86-128`, `L169-179`, and `L224-229`.
- **Verified Mechanics:**
  1. **Missing Artifact:** When `model_path.exists()` is False, `_ensure_loaded()` logs a single `WARNING`, sets `_is_available = False`, and assigns `model_version = "v1.0-rules-engine-only"`. `predict()` returns `status="unavailable"`, `fraud_probability=None`, and `ml_risk_score=0.0`.
  2. **Corrupt Artifact:** `joblib.load()` failures are wrapped in a generic `try...except Exception as load_err`. Catches deserialization errors, logs a warning, and marks `is_available = False`.
  3. **Runtime Inference Exception:** `pipeline.predict_proba()` is wrapped in `try...except Exception as inf_err`. Returns `status="error"` and `is_available = False`.
  4. **Safety & Zero Information Leakage:** In all failure modes, `combine_evaluations()` returns `combined["ml_risk_score"] = 0.0` and preserves the heuristic evaluation untouched. No stack traces or filesystem paths are emitted in API responses.

---

### Area 4: Preprocessing Alignment (WARNING)

- **Comparison Table:**

| Preprocessing Step | Training Pipeline (`train_baseline.py` / `preprocessing.py`) | Runtime Service (`inference_service.py`) | Alignment Verdict |
|:---|:---|:---|:---:|
| **Field Provenance** | 5 tabular columns: `title`, `company_profile`, `description`, `requirements`, `benefits` | 3 runtime payload fields: `job_title`, `company_name`, `job_description` | **MISMATCH** |
| **Company Content** | Long corporate profile narrative (50–250 words) | Bare corporate name string (1–4 words) | **MISMATCH** |
| **Masking Logic** | `#URL_...#`, `#EMAIL_...#`, `#PHONE_...#` regex stripped | Real unmasked URLs and emails in `job_description` | **MISMATCH** |
| **HTML Sanitization** | `clean_text`: entity unescaped + tags stripped | Identical `clean_text` applied | **PASS** |
| **Case & Whitespace** | Lowercase + collapsed whitespace | Identical `clean_text` applied | **PASS** |
| **Empty Input Guard** | Not applied (trained on non-null text series) | Explicit guard: `< 10` chars returns `insufficient_text` | **PASS** (Runtime Safety) |

- **Analysis:**
  - In EMSCAD training data, companies had extensive `company_profile` paragraphs providing vocabulary for legitimate corporate jobs (`team`, `growth`, `software`, `creative`). At runtime, only `company_name` is available.
  - In EMSCAD, all URLs and emails were masked tokens (`#URL_...#`). In runtime submissions, users paste real URLs (`https://...`) and emails. Because `clean_text` does not strip raw URLs, `TfidfVectorizer` tokenizes URL subwords (`https`, `google`, `docs`), which were absent in training.
  - **Verdict:** Alignment is a functional approximation, not an exact distribution match.

---

### Area 5: Score Semantics & Calibration (WARNING)

- **Location:** `backend/app/ml/inference_service.py:L152`.
- **Implementation:**
  ```python
  probas = self._pipeline.predict_proba([cleaned_text])
  fraud_prob = float(probas[0][1])
  ml_risk_score = round(fraud_prob * 100.0, 1)
  ```
- **Analysis:**
  - `ml_risk_score` stores an uncalibrated posterior percentage on a $0.0 - 100.0$ scale.
  - **The Calibration Illusion:** The underlying classifier was trained with `LogisticRegression(class_weight="balanced")`. In balanced training, the effective prior is artificially inflated from $4.8\%$ to $50\%$.
  - Consequently, `probas[0][1] = 0.75` **does NOT mean a 75% empirical probability that a real-world job posting is fraudulent**. It merely indicates that relative to an artificial 50/50 prior, the document has positive log-odds.
  - The API schema description (`"ML model text risk score"`) is accurate, but documentation must forbid presenting `ml_risk_score` as a calibrated probability of real-world crime.

---

### Area 6: Evidence Attribution (PASS)

- **Location:** `backend/app/ml/inference_service.py:L268-280`.
- **Verified Snippet Construction:**
  ```python
  evidence_list.append({
      "id": f"evi-ml-{uuid.uuid4().hex[:8]}",
      "text": f"Historical recruitment scam vocabulary match (lexical markers: 'data entry', 'earn')",
      "attribution": "ml_feature",
      "impact_score": lift,
      "reason": (
          f"Statistical classifier detected text patterns resembling historical scam postings "
          f"(model confidence: {ml_result.ml_risk_score}%). Advisory pattern only, not factual verification."
      ),
  })
  ```
- **Analysis:**
  - Fully complies with `EvidenceSnippetSchema` (`attribution="ml_feature"` vs `"heuristic_rule"`).
  - Explicitly disclaims factual verification. Avoids misleading terms such as *"verified scam"* or *"guaranteed safe"*.
  - Extracts and cites the exact n-grams (`data entry`, `earn`) that triggered positive coefficients.

---

### Area 7: Persistence and API Compatibility (WARNING)

- **Database Models (`app/db/models.py`)**: `JobAnalysis` table already possessed `ml_risk_score: Float`, `heuristic_risk_score: Float`, `final_risk_score: Float`, and `model_version: String`. Zero schema changes or migrations were needed.
- **API Contracts (`app/schemas/analysis.py`)**: `JobAnalysisResponse` and `JobAnalysisCreate` schemas remain 100% backward compatible.
- **Transparency Inconsistency (WARNING)**:
  - **Location:** `backend/app/services/analytics_service.py:L434-443`.
  - The endpoint `GET /api/v1/analytics/model-transparency` continues to report:
    `engine_type="Deterministic Heuristic Rules Engine"`
    `ml_model_status="Untrained / Heuristic Mode Active"`
    `ml_metrics_available=False`
  - While the live analyzer is actively evaluating ML inference and generating `v1.0-rules+ml-baseline` results, the transparency dashboard claims the model is untrained.

---

### Area 8: Model Artifact & Versioning Inconsistency (WARNING)

- **Location:** Across `rules_engine.py`, `inference_service.py`, and `model_metadata.json`.
- **Inconsistency Breakdown:**
  1. `rules_engine.py`: uses `"v1.0-rules-engine"`.
  2. `inference_service.py:L62`: initializes with `"v1.0-rules-engine-only"`.
  3. `inference_service.py:L99`: sets `"CareerShield-AI-Baseline-TFIDF-LogReg-v1.0.0"`.
  4. `inference_service.py:L231`: hardcodes `"v1.0-rules+ml-baseline"`.
  5. `model_metadata.json`: defines `model_name="CareerShield-AI-Baseline-TFIDF-LogReg"` and `model_version="1.0.0"`.
- **Analysis:**
  Depending on which function executes and whether ML was available, `JobAnalysis.model_version` receives one of four different string formats. A single canonical version naming convention is required.

---

## 3. Missing Tests Needed to Establish Confidence

The current test suite (63 passed) lacks coverage for the following critical edge cases:

1. **Heuristic Score Range [60.0, 65.0] Test**:
   - A test where $H = 62.0$ and $P(\text{fraud}) = 0.85$.
   - Current suite did not catch the dilution bug because test cases only tested $H=0$, $H=20$, and $H=75+$.
2. **Boundary Score Value Tests ($H = 34.0, 34.1, 64.0, 64.1$)**:
   - Explicit tests asserting category transitions at the exact boundary thresholds.
3. **Real URL and Email Tokenization Test**:
   - A test verifying whether real URLs in `job_description` generate spurious ML token activations.
4. **Recommendation Consistency Test**:
   - A test asserting that when ML elevates a score from `LOW_RISK` to `NEEDS_CAUTION`, conflicting low-risk recommendations are pruned.
5. **Transparency Endpoint Accuracy Test**:
   - A test verifying that `GET /api/v1/analytics/model-transparency` accurately reflects the active hybrid ML status.

---

## 4. Prioritized List of Recommended Fixes (Do NOT Apply Yet)

| Priority | Component | Issue | Proposed Fix |
|:---:|:---|:---|:---|
| **P0 (Blocker)** | `backend/app/ml/inference_service.py:L248` | Score dilution in $H \in [60.1, 64.9]$ | Change to `final_score = max(h_score, min(64.0, round(h_score + lift, 1)))`. |
| **P1** | `backend/app/ml/inference_service.py:L283` | Recommendation text dissonance | Filter out the standard corporate hiring recommendation if `final_score > 34.0`. |
| **P1** | `backend/app/services/analytics_service.py:L434` | Transparency endpoint reports untrained | Update `get_model_transparency()` to reflect active hybrid baseline pipeline. |
| **P2** | `backend/app/ml/inference_service.py:L231` | Inconsistent version strings | Standardize on canonical format: `v1.0.0-hybrid-rules+tfidf`. |
| **P2** | `backend/app/ml/inference_service.py:L29` | Raw URL tokenization in TF-IDF | Extend `prepare_job_text_for_ml` to normalize raw URLs/emails before vectorization. |

---

## 5. Audit Statement & Production Disclaimer

> [!CAUTION]
> **Production Status:** **NOT READY FOR PRODUCTION DEPLOYMENT**
> 
> While the baseline model executes and integrates without crashing, the active implementation contains a verified score dilution defect (P0) for jobs scoring between 60.1 and 64.9 points, and an architectural discrepancy in model transparency reporting.
> 
> Furthermore, because the model was trained on historical 2012–2014 overseas data containing only 4 Indian scams, it remains an uncalibrated supplementary advisory indicator. Remediation of P0 and P1 items is required before production deployment.
