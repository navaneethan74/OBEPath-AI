# OBEPath Production Deployment Guide

This guide details the step-by-step production deployment of OBEPath using **Vercel** (Frontend SPA), **Render Free Web Service** (Backend FastAPI), and **Neon** (Serverless PostgreSQL).

---

## Architecture Overview

```
                      +-----------------------------+
                      |   Vercel (Frontend SPA)     |
                      |   - Vite + React + TypeScript|
                      |   - In-Browser Pyodide WASM |
                      |   - vercel.json SPA Rewrites|
                      +--------------+--------------+
                                     |
                          HTTPS API  | (VITE_API_URL)
                          CORS Guard | (ALLOWED_ORIGINS)
                                     v
                      +-----------------------------+
                      | Render Free Web Service     |
                      | - FastAPI / Uvicorn (Py3.11)|
                      | - Health Check: /health     |
                      | - TRUST_PROXY: true         |
                      | - In-memory tutor cache     |
                      +--------------+--------------+
                                     |
                         SSL Pooler  | (DATABASE_URL)
                                     v
                      +-----------------------------+
                      | Neon Serverless PostgreSQL  |
                      | - Alembic Schema Migrations |
                      | - Seeded Curriculum & OBE   |
                      +-----------------------------+
```

---

## 1. Neon Serverless PostgreSQL Setup

1. **Create Account and Project**:
   - Go to [console.neon.tech](https://console.neon.tech) and create a free account.
   - Click **New Project** and name it `obepath-prod`.
   - Select the cloud region closest to your users or Render deployment (e.g., `us-east-2` Ohio or `eu-central-1` Frankfurt).

2. **Retrieve Connection String**:
   - In the Neon Dashboard, copy the connection string under **Connection Details**.
   - Select **Pooled connection** for serverless scaling.
   - Ensure the connection string includes `sslmode=require`.
   - Example format:
     ```text
     postgresql://neondb_owner:npg_SecretPass123@ep-cool-mountain-a5xyz-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require
     ```
   *(Note: If the connection string starts with `postgres://`, OBEPath automatically normalizes it to `postgresql://`)*.

---

## 2. Render Free Web Service Setup (Backend)

You can deploy using either the included `render.yaml` Blueprint or manually through the Render Dashboard.

### Manual Setup via Render Dashboard
1. Go to [dashboard.render.com](https://dashboard.render.com) -> **New** -> **Web Service**.
2. Connect your GitHub repository.
3. Configure service settings:
   - **Name**: `obepath-backend`
   - **Region**: Same or nearest region to your Neon database (e.g., Ohio / Frankfurt).
   - **Branch**: `main`
   - **Root Directory**: (Leave blank or set to repo root)
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: `Free`
4. Expand **Advanced Settings**:
   - **Health Check Path**: `/health`
   - **Auto-Deploy**: `Yes`

### Environment Variables
Configure the following environment variables in the Render Dashboard (**Environment** tab):

| Variable Name | Required | Example / Value | Description |
|---|---|---|---|
| `ENV` | **Yes** | `production` | Enforces production mode, disables dev backdoors, and applies migrations |
| `DATABASE_URL` | **Yes** | `postgresql://user:pass@ep-xyz.neon.tech/neondb?sslmode=require` | Neon Postgres pooled connection URL with SSL |
| `JWT_SECRET` | **Yes** | `8f4b1a...` (64+ hex characters) | Cryptographic signing key (generate via `openssl rand -hex 32`) |
| `ALLOWED_ORIGINS` | **Yes** | `https://obepath.vercel.app` | Comma-separated list of allowed frontend origins (NO `*`) |
| `TRUST_PROXY` | **Yes** | `true` | Allows reading real client IP from `X-Forwarded-For` for rate limiting |
| `ADMIN_EMAIL` | **Yes** | `admin@institution.edu` | Initial admin account bootstrap email |
| `ADMIN_PASSWORD` | **Yes** | `SecureP@ssw0rd2026!` | Initial admin account bootstrap password (min 8 chars, mixed case, numbers) |
| `GEMINI_API_KEY` | **Yes** | `AIzaSy...` | Google Gemini API key for AI Tutor and question generation |
| `GEMINI_MODEL` | Optional | `gemini-2.5-flash` | Gemini model name (default: `gemini-2.5-flash`) |
| `GOOGLE_CLIENT_ID`| Optional | `123456...apps.googleusercontent.com` | Google OAuth Client ID for student/faculty Google Login |
| `SMTP_HOST` | Optional | `smtp.resend.com` | SMTP email host for automated notifications |
| `SMTP_PORT` | Optional | `587` | SMTP port |
| `SMTP_USER` | Optional | `resend` | SMTP username |
| `SMTP_PASS` | Optional | `re_...` | SMTP password / API token |
| `SMTP_FROM` | Optional | `support@obepath.edu` | Outbound email sender address |

---

## 3. Database Migration and Seeding

OBEPath is built to be turnkey on serverless deployments without SSH shell access.

### Automatic Migration on Startup
When `ENV=production` is set, `backend/main.py` runs programmatic Alembic migrations on startup:
```python
# Automatically executed in production startup path
command.upgrade(alembic_cfg, "head")
```
It then bootstraps the administrator account defined by `ADMIN_EMAIL` and `ADMIN_PASSWORD` if no admin exists yet.

### Manual Migration Command
If running from a CLI or CI/CD runner:
```bash
cd backend
alembic upgrade head
```

### Curriculum Seeding Command
To seed all 4 accredited courses (CS101, CS201, AI301, CS302), topics, Bloom's taxonomies, prerequisite edges, course outcomes, and comprehensive QuestionBank:
```bash
# From repository root with DATABASE_URL set to Neon:
python backend/scripts/seed_curriculum.py
```
*(Or inside `backend/`: `python scripts/seed_curriculum.py`)*

---

## 4. Vercel Setup (Frontend)

1. Go to [vercel.com/dashboard](https://vercel.com/dashboard) and click **Add New...** -> **Project**.
2. Import the GitHub repository.
3. Configure project settings:
   - **Framework Preset**: `Vite`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Install Command**: `npm install`
4. Set the single canonical environment variable:

| Variable Name | Value | Description |
|---|---|---|
| `VITE_API_URL` | `https://obepath-backend.onrender.com/api` | Full URL of your deployed Render backend including `/api` prefix |

5. Click **Deploy**.

### SPA Rewrites Verification
The repository includes `frontend/vercel.json` with the rewrite rule:
```json
{
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```
This guarantees that direct URLs and browser refreshes on routes like `/admin-login` and `/faculty` route directly to `index.html` without encountering Vercel 404 errors.

---

## 5. Render Free Tier Cold Starts & Keep-Alive

### Cold Start Characteristics
- Render free tier instances spin down after **15 minutes of inactivity**.
- The first inbound request to an idle instance triggers a cold boot, typically taking **30 to 50 seconds**.
- The OBEPath frontend handles this gracefully:
  - The loading spinner indicates session authentication with the backend.
  - Browser compiler tasks (Pyodide Python runner) execute entirely client-side inside a Web Worker, ensuring zero dependency on server latency for code execution.

### Free Keep-Alive Mitigation (Optional)
To eliminate cold starts for active demo periods:
1. Register for a free uptime monitor such as [UptimeRobot](https://uptimerobot.com) or [Cron-job.org](https://cron-job.org).
2. Configure an HTTP `GET` monitor pointing to your backend health endpoint:
   ```text
   https://obepath-backend.onrender.com/health
   ```
3. Set the interval to **every 14 minutes**.
4. The `/health` endpoint responds with `{ "status": "healthy" }` in `< 10ms` and keeps the container warm within Render's free quota.

---

## 6. Pre-Flight Verification (Smoke Test)

Run the automated smoke test suite against your newly deployed backend:

```bash
# Against your live deployed backend:
python scripts/smoke_test.py https://obepath-backend.onrender.com

# Or locally:
python scripts/smoke_test.py http://127.0.0.1:8000
```
This verifies health checks, student onboarding, diagnostic assessments, practice submission, class enrollment, faculty dashboards, 403 role denials, 401 forged token rejection, and production backdoor disabling (simulate-activity returning 404).
