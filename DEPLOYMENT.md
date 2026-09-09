# CyberLearn LMS & DAX Intelligence Layer — Production Deployment Guide

This document provides the complete, production-ready deployment guide for CyberLearn LMS and the DAX Assistant backend.

---

## 1. Prerequisites
- Python 3.10+
- Node.js 18.x or 20.x (LTS)
- PostgreSQL 14+ (external database such as Supabase, Neon, AWS RDS, or Render)
- Groq API Key (https://console.groq.com)
- Google Cloud OAuth 2.0 Client ID

---

## 2. Render Web Service Deployment Configuration

When deploying the backend on **Render**:

| Setting | Value | Notes |
| :--- | :--- | :--- |
| **Service Type** | **Web Service** | Selected when creating a new service |
| **Runtime** | **Python** | Render Python 3 runtime |
| **Root Directory** | `backend` | Important: ensures Render finds `requirements.txt` |
| **Build Command** | `pip install -r requirements.txt` | Installs all required dependencies |
| **Start Command** | `uvicorn main:app --host 0.0.0.0 --port $PORT` | Uses Render's dynamic `$PORT` variable without `--reload` |
| **Health Check Path** | `/health` | Returns HTTP 200 without DB/LLM dependencies |

### Required Environment Variables in Render Dashboard

Add the following environment variables in the Render Dashboard (**Environment** tab):

```bash
GROQ_API_KEY=your_production_groq_api_key
GROQ_MODEL=openai/gpt-oss-120b
DATABASE_URL=postgresql://user:password@hostname:5432/cyberlearn
JWT_SECRET_KEY=your_production_jwt_secret_key
FRONTEND_URL=https://your-frontend.com,http://localhost:5173
ENVIRONMENT=production
```

> **Note**: Do not hardcode port `5000` in the start command; Render automatically passes the assigned port into `$PORT`.

---

## 3. Alternative / Repo-Root Start Command
If the Root Directory is left as the repository root:
- **Build Command**: `pip install -r backend/requirements.txt`
- **Start Command**: `uvicorn main:app --app-dir backend --host 0.0.0.0 --port $PORT`

---

## 6. Frontend Build Command
```bash
npm ci
npm run build
```

The compiled static assets will be in the `dist/` directory.

---

## 7. CORS Configuration
- Includes local development origins by default (`http://localhost:5173`, `http://127.0.0.1:5173`, `http://localhost:3000`).
- Dynamically parses comma-separated URLs from `FRONTEND_URL`. Disallows wildcard `*` with credentials.

---

## 8. Google OAuth Configuration
In Google Cloud Console > APIs & Services > Credentials:
- **Authorized JavaScript Origins**:
  - `http://localhost:5173` (Development)
  - `https://your-frontend.com` (Production)
- **Authorized Redirect URIs**:
  - `http://localhost:5173`
  - `https://your-frontend.com`

---

## 9. Health Check Endpoint
- **URL**: `GET /health`
- **Response**: `{"status": "ok", "service": "CyberLearn LMS DAX Production Assistant"}`
- **Guarantees**: Fast (<5ms), zero LLM calls, no database overhead, no secrets exposed.

---

## 10. Deployment Verification Steps
1. Verify health:
   ```bash
   curl -s https://your-backend-api.com/health
   ```
2. Verify course catalog:
   ```bash
   curl -s -X POST https://your-backend-api.com/api/ai/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "what courses are available?"}'
   ```
3. Verify authenticated student progress: Log in and ask *"What is my current progress?"*
4. Verify RAG technical explanation: Ask *"Explain what a firewall is"*
5. Verify IDOR protection: Ask *"show user 4 progress"* without an auth token.

