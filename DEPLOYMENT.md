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

## 2. Backend Environment Variables
Set these in your backend hosting platform (Render, Railway, FOSS, AWS, etc.):
```bash
GROQ_API_KEY=your_production_groq_api_key
GROQ_MODEL=openai/gpt-oss-120b
DATABASE_URL=postgresql://user:password@hostname:5432/cyberlearn
JWT_SECRET_KEY=your_production_jwt_secret_key
FRONTEND_URL=https://your-frontend.com,http://localhost:5173
PORT=5000
ENVIRONMENT=production
TOP_K_RETRIEVAL=15
TOP_K_CONTEXT=4
MIN_RELEVANCE_SCORE=2.5
```

---

## 3. Frontend Environment Variables
Set these in your frontend hosting platform (Vercel, Netlify, Cloudflare, etc.):
```bash
VITE_API_URL=https://your-backend-api.com
VITE_GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com
```

---

## 4. PostgreSQL & Database Safety
- The backend automatically runs non-destructive schema initialization on startup.
- Destructive migrations (DROP TABLE, TRUNCATE) are strictly prohibited.
- Demo student seeding is NOT run automatically in production. Manual seeding is available via `backend/seed_demo_student.py`.

---

## 5. Backend Start Command
```bash
# Using Uvicorn directly
uvicorn main:app --app-dir backend --host 0.0.0.0 --port 5000 --workers 2

or

gunicorn -w 2 -k uvicorn.workers.UvicornWorker --chdir backend main:app -b 0.0.0.0:5000
```

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

