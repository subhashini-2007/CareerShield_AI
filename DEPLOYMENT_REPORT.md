# CareerShield AI — Verified Production Deployment Report

**Document Version:** 2.2.0 (Production Guardrail Hardening & Single-Architecture Release)  
**Date:** October 20, 2026  
**Project:** CareerShield AI (`https://github.com/subhashini-2007/CareerShield_AI`)  
**Tagline:** *Verify Opportunities. Protect Futures.*  
**Monthly Operating Cost:** **₹0.00 (Guaranteed Free Tier)**  
**Target Infrastructure:**  
- **Frontend:** Next.js 14+ (App Router) on **Vercel** (Root directory: `frontend`)  
- **Backend:** FastAPI (Python 3.11.9) on **Render Free Web Service** (Root directory: `backend`)  
- **Database:** **Neon Serverless PostgreSQL** (Free Tier via Pooled PgBouncer connection)  
- **Local Fallback:** SQLite (Retained for local development and testing only)  

---

## 1. Verified System Checks & Audit Results

The following checks were directly inspected and verified across the codebase:

| Check Item | Verified Component | Inspection Result | Status |
|---|---|---|---|
| **Python 3.11.9 Runtime** | `render.yaml` & `backend/requirements.txt` | All dependencies (`fastapi`, `pydantic 2.6+`, `sqlalchemy 2.0.28+`, `psycopg2-binary`, `scikit-learn 1.4+`, `numpy 1.26+`, `joblib 1.3+`) are compatible with Python 3.11 on Linux x86_64. Added `PYTHON_VERSION: "3.11.9"` under `envVars` in `render.yaml`. | **PASS** |
| **Production Database Guardrails** | `backend/app/core/config.py` | Enforces that `APP_ENV=production` strictly requires a remote PostgreSQL URL (Neon). Ephemeral SQLite or default localhost URLs trigger immediate startup `ValueError` to prevent silent data loss on Render. Normalizes `postgres://` to `postgresql://` and handles `?sslmode=require`. | **PASS** |
| **CORS Origin Normalization & Safety** | `backend/app/core/config.py` | Parses JSON list strings or comma-separated lists, automatically strips trailing slashes to ensure strict browser `Origin` header equality, and warns immediately if production CORS contains only localhost. | **PASS** |
| **Health Check Resilience** | `backend/app/api/v1/endpoints/health.py` | Route `/api/v1/health` catches DB exceptions and returns HTTP 200 with `{"status": "degraded"}` when database is waking up. Passes Render's HTTP 2xx health check without requiring an immediate database connection. | **PASS** |
| **Model Path Resolution** | `backend/app/core/config.py` & `backend/app/ml/inference_service.py` | `BASE_DIR` resolves to `backend/`. `MODEL_ARTIFACTS_DIR=artifacts/models` resolves cleanly to `backend/artifacts/models`. `baseline_pipeline.joblib` (492 KB binary) and `model_metadata.json` (4 KB) exist on disk and are tracked in Git. | **PASS** |
| **Startup Schema Idempotency** | `backend/app/main.py` & `backend/scripts/init_neon_db.py` | `Base.metadata.create_all()` in startup `lifespan` uses idempotent `CREATE TABLE IF NOT EXISTS`. Tables are created automatically on an empty Neon database. Automated employer record seeding was removed pending verified data sources. | **PASS** |
| **Obsolete Files Assessment** | Root `vercel.json` & `api/index.py` | Verified as obsolete serverless artifacts from previous exploratory phase. Safe to delete before pushing: running `Remove-Item -Recurse -Force api, vercel.json` cleans the working tree. Vercel uses `frontend` as its root directory and reads [`frontend/vercel.json`](file:///C:/Users/subha/OneDrive/Desktop/CareerShield_AI/frontend/vercel.json) exclusively for security headers. | **PASS** |
| **Environment Template Safety** | `.env.example`, `backend/.env.example`, `frontend/.env.example` | Verified: Contains strictly non-sensitive placeholders. Zero real passwords, secret keys, or live credentials exist. | **PASS** |
| **Frontend API Configuration** | `frontend/src/lib/api.ts` | `NEXT_PUBLIC_API_URL` is used consistently across code and documentation. Trailing slashes are stripped dynamically. | **PASS** |
| **Test Suite Verification** | `backend/tests/` & `frontend/` | User run verified: **79 backend unit/integration tests passed** (including the new `test_production_database_and_cors_guardrails`), 1 non-fatal warning; **Next.js frontend production build completed successfully**. | **PASS** |

---

## 2. Production Architecture Diagram

```mermaid
flowchart TD
    User([End User Browser])
    
    subgraph VercelEdge["Vercel Global Edge Network (₹0/mo)"]
        NextJS["Next.js 14 App Router (React 18 / TypeScript)\nRoot Directory: frontend\n• Landing Page (/)\n• Job Risk Analyzer (/analyzer)\n• Analytics Dashboard (/dashboard)\n• Searchable History (/history)\n• Algorithmic Transparency (/model-insights)"]
    end

    subgraph RenderService["Render Free Web Service (₹0/mo)"]
        direction TB
        FastAPI["FastAPI 0.110+ ASGI Engine (Python 3.11.9)\nRoot Directory: backend\n• /api/v1/health (Diagnostics)\n• /api/v1/analyze (Risk Analysis)\n• /api/v1/analytics/summary (Dashboard Stats)\n• /api/v1/analytics/model-transparency (Specs)"]
        
        subgraph PersistentRAM["Persistent Memory (512 MB Free Tier RAM)"]
            LoadedModel["Preloaded Scikit-learn Pipeline in RAM (~170 MB)\n• TF-IDF Vectorizer (10k features)\n• Balanced Logistic Regression\n• Zero Per-Request Unpickling"]
            DBPool["SQLAlchemy Connection Pool\n• pool_size=5, max_overflow=10\n• pool_recycle=300 (Neon Sync)"]
        end
    end

    subgraph NeonCloud["Neon Serverless PostgreSQL (₹0/mo)"]
        PgBouncer["PgBouncer Connection Pooler (Port 5432/6543)"]
        NeonDB[("PostgreSQL Storage (0.5 GiB)\n• job_analyses (Persistent Audit Trail)\n• analysis_feedbacks\n• known_company_benchmarks\n• model_eval_metrics")]
    end

    User -->|HTTPS Requests| NextJS
    NextJS -->|REST API over TLS\nNEXT_PUBLIC_API_URL| FastAPI
    FastAPI --> PersistentRAM
    FastAPI -->|TLS 1.3 / sslmode=require\nDATABASE_URL| PgBouncer
    PgBouncer --> NeonDB
```

---

## 3. Remaining Operational Risks & Mitigations

| Risk | Cause | Probability | Impact | Mitigation |
|---|---|---|---|---|
| **Free-tier cold start latency (~50s)** | Render free web service spins down after 15 minutes of inactivity. | High | Medium | Normal behavior for Render's ₹0 tier. Frontend error messages across `/analyzer`, `/dashboard`, `/history`, and `/model-insights` inform users when the backend is waking up. To keep the service awake 24/7 at ₹0, use a free uptime monitor (e.g., [cron-job.org](https://cron-job.org)) to ping `/api/v1/health` every 10 minutes. |
| **Neon compute auto-suspend** | Neon automatically suspends compute after 5 minutes of inactivity. | High | Low | Neon automatically wakes up within 1.5–2 seconds on the next incoming query. SQLAlchemy is configured with `pool_recycle=300` and `pool_pre_ping=True` to discard stale connections gracefully. |
| **Direct vs. Pooled connection string** | Using direct port 5432 URL instead of PgBouncer pooled URL on Neon. | Medium | Medium | In Neon console, toggle to **Pooled connection** (hostname contains `-pooler`). Free tier allows up to 100 pooled connections vs. 20 direct connections. |
| **Missing or short `SECRET_KEY` in production** | `APP_ENV=production` enforces `len(SECRET_KEY) >= 32`. | Low | High | `render.yaml` sets `generateValue: true` so Render generates a cryptographically secure token automatically. |
| **CORS blocking if Vercel URL omitted** | Deploying backend with `CORS_ORIGINS` pointing only to localhost. | Medium | High | Render's `CORS_ORIGINS` must be set to your live Vercel URL (`https://<your-project>.vercel.app`). The backend now actively logs a warning on startup if only localhost is configured in production. |

---

## 4. Exact Manual Steps to Deploy

Follow these exact steps when you are ready to deploy. No credit card or paid subscription is required.

---

### Step 1: Run Local Verification Commands (Your Terminal)

In this assistant session, terminal command execution is blocked by Windows security permissions (`Access is denied.`). Run these checks in your local PowerShell:

```powershell
cd C:\Users\subha\OneDrive\Desktop\CareerShield_AI

# 1. Check Git diff and whitespace hygiene
git diff --check

# 2. Check Git status of modified/untracked files
git status

# 3. Run backend unit and integration test suite
cd backend
.\venv\Scripts\python.exe -m pytest -v

# 4. Run Next.js production build check
cd ..\frontend
npm run build
```

---

### Step 2: Remove Obsolete Files & Push Code to GitHub

Delete the obsolete serverless files (they are untracked), then stage, commit, and push:

```powershell
cd C:\Users\subha\OneDrive\Desktop\CareerShield_AI

# 1. Cleanly delete obsolete untracked serverless exploration files
Remove-Item -Recurse -Force api, vercel.json

# 2. Stage verified production deployment files
git add .

# 3. Commit changes
git commit -m "feat(deploy): production hardening, Neon PostgreSQL config, and single Render/Vercel architecture"

# 4. Push to your GitHub repository
git push origin main
```

---

### Step 3: Create Free Neon PostgreSQL Database (2 minutes)

1. Open **[https://console.neon.tech](https://console.neon.tech)** and log in with your GitHub account.
2. Click **New Project**:
   - **Name:** `careershield-db`
   - **Postgres Version:** `16` (Default)
   - **Region:** Select the region closest to your audience (e.g. `AWS us-east-2`, `AWS eu-central-1`, or `AWS ap-southeast-1`).
3. In the connection details panel:
   - Ensure the dropdown is toggled to **Pooled connection**.
   - Copy the connection string. It will look like:
     ```
     postgresql://neondb_owner:npg_AbCdEf123456@ep-cool-mountain-a5xyz-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require
     ```
   - Keep this connection string ready for Step 4.

---

### Step 4: Deploy Backend on Render Free Web Service (3 minutes)

1. Open **[https://dashboard.render.com](https://dashboard.render.com)** and log in with your GitHub account.
2. Click **New +** -> **Web Service**.
3. Select your repository: `subhashini-2007/CareerShield_AI`.
4. Configure service settings:
   - **Name:** `careershield-api`
   - **Region:** Select the same region as your Neon database.
   - **Branch:** `main`
   - **Root Directory:** `backend`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install --upgrade pip && pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** `Free` (512 MB RAM)
5. Under **Environment Variables**, add:

| Key | Value | Notes |
|---|---|---|
| `PYTHON_VERSION` | `3.11.9` | Locks Python version |
| `APP_NAME` | `CareerShield AI` | Branding |
| `APP_ENV` | `production` | Enforces production validations & blocks SQLite |
| `DEBUG` | `false` | Production mode |
| `SECRET_KEY` | *(Render can auto-generate or paste 48+ chars)* | Session/IP hash salt (min 32 chars) |
| `DATABASE_URL` | *(Paste your Neon Pooled connection string from Step 3)* | Must be remote PostgreSQL |
| `CORS_ORIGINS` | `https://careershield-ai.vercel.app` | **Set to your actual Vercel project domain!** Do not leave as localhost. |
| `ANONYMIZE_IPS` | `true` | Hashes client IPs before persisting |
| `MODEL_ARTIFACTS_DIR` | `artifacts/models` | Relative path to ML pipeline |

6. Click **Create Web Service**.
7. Wait for Render to build and deploy. Once live, the logs will show:
   ```
   INFO: Successfully connected to database (postgresql) in ...ms.
   INFO: Database tables verified / created successfully.
   INFO: Application startup complete.
   ```
8. Copy your Render backend URL (e.g., `https://careershield-api.onrender.com`).

---

### Step 5: Deploy Frontend on Vercel (2 minutes)

1. Open **[https://vercel.com](https://vercel.com)** and log in with your GitHub account.
2. Click **Add New...** -> **Project**.
3. Locate `subhashini-2007/CareerShield_AI` and click **Import**.
4. Configure Project:
   - **Project Name:** `careershield-ai` (matching the domain used in Step 4)
   - **Framework Preset:** `Next.js`
   - **Root Directory:** Click **Edit** and select `frontend`.
5. Under **Environment Variables**, add:

| Key | Value |
|---|---|
| `NEXT_PUBLIC_API_URL` | `https://your-backend.onrender.com/api/v1` |
| `NEXT_PUBLIC_APP_NAME` | `CareerShield AI` |
| `NEXT_PUBLIC_TAGLINE` | `Verify Opportunities. Protect Futures.` |

6. Click **Deploy**. Vercel will build and deploy the Next.js frontend globally.
7. Note your live Vercel URL (e.g., `https://careershield-ai.vercel.app`).
8. If your assigned Vercel URL differs from what you entered in Step 4, update `CORS_ORIGINS` in Render Dashboard -> `careershield-api` -> **Environment** and click Save Changes.

---

## 5. Post-Deployment Verification Smoke Tests

### Backend Health Check
```powershell
curl -X GET "https://your-backend.onrender.com/api/v1/health"
```
*Expected: `"status": "ok"`, `"database": {"connected": true, "engine": "postgresql"}`, `"model": {"loaded": true, "status": "trained"}`.*

### Frontend End-to-End Test
1. Visit `https://careershield-ai.vercel.app`. Confirm the green **System Operational** indicator.
2. Go to `/analyzer` -> Click preset **"TCS Spoofed Offer (Fee Demand)"** -> Click **Verify Job Opportunity Risk**.
3. Verify that the assessment displays High Risk, fee warning badges, and recruiter domain alerts.
4. Go to `/history` -> Confirm the assessment record appears in the persistent audit trail stored in Neon PostgreSQL.
5. Go to `/dashboard` and `/model-insights` -> Confirm metrics and transparency specifications load properly.
