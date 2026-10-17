# CareerShield AI

> **Verify Opportunities. Protect Futures.**

**CareerShield AI** is an AI-powered job opportunity verification and career-risk analysis platform engineered for Indian students, freshers, and job seekers. The platform evaluates job postings, recruiter communications, salary claims, upfront payment demands, and company authenticity indicators using an explainable hybrid AI engine: calibrated machine learning combined with a deterministic heuristic safety engine.

---

## 1. System Architecture Overview

- **Frontend:** Next.js 14+ (App Router), TypeScript, Tailwind CSS, Lucide Icons, Recharts.
- **Backend:** Python 3.10+, FastAPI, SQLAlchemy ORM, Alembic migrations, Scikit-learn, Pandas, Pytest.
- **Database:** PostgreSQL (primary production standard) with explicitly configured SQLite support for zero-friction local development.
- **Security:** Strict CORS origin controls, no hardcoded secrets, PII minimization, sanitized error diagnostics.
- **Explainability:** Independent display of Machine Learning Risk Score, Heuristic Rule Score, and Calibrated Final Score, with token-level highlights and actionable fresher safety checklists.

---

## 2. Environment Tool Inspection Findings

During initialization, the host environment was inspected with the following results:

| Tool | Status | Location / Details |
|---|---|---|
| **Python** | Installed | `C:\Users\subha\AppData\Local\Programs\Python\Python313\python.exe` (Python 3.13 with `pip`, `uvicorn`) |
| **Node.js & npm** | Installed | `C:\Program Files\nodejs\` (`node.exe`, `npm.cmd`, `npx.cmd`) |
| **Git** | Installed | `C:\Program Files\Git\` |
| **PostgreSQL (`psql`)** | Not Installed Locally | See Database Setup Instructions below |
| **Docker** | Not Installed | See Database Setup Instructions below |

---

## 3. Database Setup Instructions

PostgreSQL is the intended primary database for CareerShield AI. Because PostgreSQL and Docker are not pre-installed on this machine, you have two options:

### Option A: PostgreSQL Setup (Recommended Production Path)

1. **Local Windows PostgreSQL Server:**
   - Download and install PostgreSQL 16 for Windows: [postgresql.org/download/windows](https://www.postgresql.org/download/windows/)
   - Default port: `5432`
   - Create the database in pgAdmin or PowerShell:
     ```sql
     CREATE DATABASE careershield_db;
     ```
   - Update `backend/.env`:
     ```env
     DATABASE_URL=postgresql://postgres:your_password@localhost:5432/careershield_db
     ```

2. **Alternative — Free Cloud PostgreSQL (Zero Installation):**
   - Create a free database instance on [Neon](https://neon.tech), [Supabase](https://supabase.com), or [Aiven](https://aiven.io).
   - Paste the provided connection string into `backend/.env`:
     ```env
     DATABASE_URL=postgresql://user:password@host/careershield_db?sslmode=require
     ```

3. **Alternative — Docker (if installed later):**
   - Run the provided `docker-compose.yml`:
     ```powershell
     docker compose up -d
     ```

### Option B: Explicit Local SQLite Development Mode

If you prefer to develop locally before setting up PostgreSQL, CareerShield AI allows SQLite **only when explicitly configured in `backend/.env`**:
```env
DATABASE_URL=sqlite:///./careershield.db
```
> [!NOTE]
> CareerShield AI will **never** silently switch to SQLite if a PostgreSQL connection fails. It only uses SQLite when explicitly configured as the `DATABASE_URL`. The active database engine is always reported transparently via `GET /api/v1/health`.

---

## 4. Getting Started

### Step 1: Backend Setup & Execution

Open a terminal in the project directory:

```powershell
# Navigate to backend directory
cd backend

# Create Python virtual environment
python -m venv venv

# Activate virtual environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Windows Command Prompt:
.\venv\Scripts\activate.bat

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Configure environment variables
Copy-Item .env.example .env
# Edit .env and verify DATABASE_URL and SECRET_KEY

# Run database migrations
alembic upgrade head

# Start FastAPI development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API Base URL: `http://localhost:8000`
- Interactive Swagger UI: `http://localhost:8000/docs`
- Health Check Diagnostics: `http://localhost:8000/api/v1/health`
- Job Opportunity Analysis: `POST /api/v1/analyze`
- Analysis History Log: `GET /api/v1/analyses`
- Analysis Detail Lookup: `GET /api/v1/analyses/{analysis_id}`
- Analytics Dashboard Summary: `GET /api/v1/analytics/summary`
- Model Transparency & Trigger Stats: `GET /api/v1/analytics/model-transparency`

### Step 2: Running Automated Backend Tests

```powershell
cd backend
pytest -v
```

Tests verify:
- Health check endpoints and diagnostics schema
- Absence of leaked passwords or credentials in API responses
- Explicit database engine configuration & fail-fast behavior
- Model constraints and relationship integrity
- Heuristic safety rules (upfront fees, domain spoofing, Telegram channels, task scams)
- Job analysis API submission, validation errors (422), pagination, and detail lookup (404)
- Analytics summary endpoint (empty database zero-safe calculations, populated database aggregations, PII minimization)
- Model transparency specifications (canonical rule definitions, live trigger frequency aggregation across stored records)

---

### Step 3: Frontend Setup & Execution

Open a separate terminal window:

```powershell
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install

# Configure environment variables
Copy-Item .env.example .env.local

# Start Next.js development server
npm run dev
```

- Web Application: `http://localhost:3000`
- Job Risk Analyzer: `http://localhost:3000/analyzer`
- Recruitment Risk Dashboard: `http://localhost:3000/dashboard`
- Analysis Audit History: `http://localhost:3000/history`
- Model Insights & Transparency: `http://localhost:3000/model-insights`

---

## 5. Phase 1 Deliverables Summary

- [x] Monorepo directory structure established for Next.js frontend and FastAPI backend.
- [x] Backend dependencies (`requirements.txt`, `pyproject.toml`) and environment configuration (`config.py`).
- [x] Explicit `DATABASE_URL` selection with fail-fast mechanics (no silent fallback).
- [x] SQLAlchemy ORM models: `job_analyses`, `analysis_feedbacks`, `known_company_benchmarks`, `model_eval_metrics`.
- [x] Alembic configuration and initial migration (`001_initial_schema.py`).
- [x] `GET /api/v1/health` diagnostic endpoint reporting DB engine, connectivity, and model status without exposing secrets.
- [x] Automated Pytest test suite for health, database configuration, and models.
- [x] Minimal Next.js TypeScript application shell with Tailwind CSS navy & cyan design system.
- [x] Safe `.env.example` templates and comprehensive `.gitignore`.

---

## 6. Phase 2 Deliverables Summary (Job Risk Analyzer)

- [x] Explainable Heuristic Rules Engine (`app.ml.rules_engine`) evaluating 7 risk dimensions.
- [x] Recruitment fee and deposit detection (+50 to +55 pts).
- [x] Free webmail domain spoofing against top Indian tech employers (TCS, Infosys, Wipro, etc.).
- [x] Informal communication channel penalty (Telegram, WhatsApp) and direct selection warnings.
- [x] Task scam patterns and unrealistic fresher payout detection.
- [x] REST API endpoints:
  - `POST /api/v1/analyze`: Validate, evaluate, and persist job analysis records.
  - `GET /api/v1/analyses`: Paginated audit history with risk level filtering and company search.
  - `GET /api/v1/analyses/{analysis_id}`: Detail view for individual analysis records.
- [x] SQLite database persistence via SQLAlchemy ORM with IP anonymization salt.
- [x] Pytest automated test suites for rules engine and API integration (`test_rules_engine.py`, `test_analyzer_api.py`).
- [x] Next.js `/analyzer` interface with dark navy & cyan aesthetic, 4 1-click preset scenarios, live dial, and actionable fresher checklist.
- [x] Next.js `/history` audit log page with search, risk tier filter, inspection drawer modal, and pagination.

---

## 7. Phase 3 Deliverables Summary (Analytics Dashboard & Model Insights)

- [x] Analytics aggregation service (`app.services.analytics_service`) calculating total analyses, risk tier proportions, average risk index, upfront deposit share, score intervals, communication channel risk profiles, and top warning indicators.
- [x] PII-minimized recent activity table and safe division-by-zero handling on empty databases.
- [x] Model transparency service (`get_model_transparency`) surfacing 10 canonical heuristic rules, risk point values, mitigating factors, and live database trigger frequencies.
- [x] REST API endpoints:
  - `GET /api/v1/analytics/summary`: Aggregate analytics response for real-time dashboard visualization.
  - `GET /api/v1/analytics/model-transparency`: Algorithmic rules specification and trigger statistics.
- [x] Recharts data visualization in Next.js `/dashboard`:
  - Risk Category Distribution Donut Chart (`LOW_RISK`, `NEEDS_CAUTION`, `HIGH_RISK_INDICATORS`).
  - Score Interval Histogram Bar Chart.
  - Channel Risk Profile comparison with average risk scores.
  - Most frequently flagged warning indicators.
  - Recent analysis activity table with direct link to audit inspection.
  - Informative empty state and loading skeletons (no fabricated data).
- [x] Model Insights & Transparency view in Next.js `/model-insights`:
  - Explicit identification of active system as a Deterministic Heuristic Rules Engine (`v1.0-rules-engine`).
  - Transparent disclosure explaining why supervised ML metrics (Precision, Recall, F1, ROC-AUC) are currently unavailable without empirical model training.
  - Detailed catalog of 10 detection rules, penalty scores, detection mechanisms, and live trigger counts.
  - Mitigating signals breakdown (official domains, multi-round interviews, statutory benefits).
  - Documented system limitations and edge cases.
- [x] Automated Pytest test suite (`test_analytics_api.py`) verifying empty database responses, populated database aggregations, and model transparency trigger counting.

---

## 8. Responsible AI Principles

1. **Non-Defamatory Design:** CareerShield AI never labels an organization or individual as definitively fraudulent solely because of missing data or personal email addresses.
2. **Transparent Signals:** Clearly distinguishes between statistical ML probabilities, deterministic security rules, and final calibrated scores.
3. **Evidence-Based Guidance:** Every flagged indicator highlights the supporting textual evidence and provides actionable safety steps for students.
4. **Honest ML Evaluation:** Never invent or claim fabricated ML metrics (accuracy, F1, confusion matrices) before a verified dataset is trained.


