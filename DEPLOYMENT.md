# LinguFlow Deployment Guide

This guide describes how to deploy LinguFlow using the modern, decoupled target architecture:

- **Frontend**: Vue 3 + Vite static SPA hosted on **Vercel** (`frontend/dist`)
- **Backend & Database**: Python FastAPI backend + PostgreSQL database hosted on **Railway**
- **Media Storage**: Cloudflare R2 object storage accessed via `aioboto3` presigned S3 URLs

---

## 1. Cloudflare R2 Bucket Setup

1. Log in to [Cloudflare Dashboard](https://dash.cloudflare.com) > **R2**.
2. Create a bucket named `linguflow-media`.
3. Go to **R2 > Manage API Tokens** and click **Create API Token**:
   - Set permission to **Object Read & Write**.
   - Scope to `linguflow-media` bucket.
4. Record the following credentials:
   - **Access Key ID**
   - **Secret Access Key**
   - **Endpoint URL** (`https://<ACCOUNT_ID>.r2.cloudflarestorage.com`)

---

## 2. Railway Setup (FastAPI Backend & Postgres)

1. Log in to [Railway](https://railway.app) and create a **New Project**.
2. Click **Add Plugin > PostgreSQL**:
   - Railway automatically sets `${{Postgres.DATABASE_URL}}`.
3. Click **Add Service > GitHub Repo**:
   - Select the `lingu-flow` repository.
   - Set **Root Directory** to `backend`.
   - Set **Builder** to `Dockerfile`.
4. Configure **Environment Variables** in Railway service settings:
   - `ENVIRONMENT`: `production`
   - `JWT_SECRET`: A secure 64-character hex string (generated via `openssl rand -hex 32`)
   - `JWT_ALGORITHM`: `HS256`
   - `CORS_ORIGINS`: `["https://linguflow.vercel.app","http://localhost:5173"]`
   - `CORS_ORIGIN_REGEX`: `https://linguflow-.*\.vercel\.app`
   - `R2_ACCOUNT_ID`: Your Cloudflare Account ID
   - `R2_ACCESS_KEY_ID`: Cloudflare R2 Access Key ID
   - `R2_SECRET_ACCESS_KEY`: Cloudflare R2 Secret Access Key
   - `R2_BUCKET_NAME`: `linguflow-media`
   - `R2_ENDPOINT_URL`: `https://<ACCOUNT_ID>.r2.cloudflarestorage.com`
5. Set the **Custom Start Command** (must migrate **and seed** before serving — FastAPI lifespan no longer seeds):
   ```bash
   alembic upgrade head && python -m app.seed.exam_seed && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
   ```
   Prefer leaving **Start Command empty** so the image uses `backend/entrypoint.sh` (same migrate → seed → uvicorn sequence). A start command that only runs `alembic` + `uvicorn` will boot with an empty built-in exam bank.
6. Generate a public domain under Railway service **Settings > Networking** (e.g. `https://linguflow-backend-production.up.railway.app`).

---

## 3. Vercel Setup (Vue 3 SPA Frontend)

1. Log in to [Vercel](https://vercel.com) and click **Add New > Project**.
2. Import the `lingu-flow` GitHub repository.
3. Configure Project Settings:
   - **Framework Preset**: `Vite`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Install Command**: `npm install`
4. Update `frontend/vercel.json` rewrite destination with your Railway public domain:
   ```json
   {
     "rewrites": [
       {
         "source": "/api/:path*",
         "destination": "https://<your-railway-app>.up.railway.app/api/:path*"
       },
       {
         "source": "/(.*)",
         "destination": "/index.html"
       }
     ]
   }
   ```
5. Deploy. All `/api/*` HTTP calls issued by the SPA will be proxied to Railway backend.

---

## 4. Environment Variables Summary

| Platform | Variable | Scope / Description |
| :--- | :--- | :--- |
| **Vercel** | *(None required)* | Relative API requests proxied via `frontend/vercel.json` |
| **Railway** | `DATABASE_URL` | PostgreSQL connection string (`${{Postgres.DATABASE_URL}}`) |
| **Railway** | `ENVIRONMENT` | `production` |
| **Railway** | `PORT` | Provided by Railway runtime (`${{PORT}}`) |
| **Railway** | `JWT_SECRET` | Secret 64-char key for signing tokens |
| **Railway** | `CORS_ORIGINS` | `["https://linguflow.vercel.app","http://localhost:5173"]` |
| **Railway** | `CORS_ORIGIN_REGEX` | `https://linguflow-.*\.vercel\.app` |
| **Railway** | `R2_ACCOUNT_ID` | Cloudflare Account ID |
| **Railway** | `R2_ACCESS_KEY_ID` | Cloudflare R2 Access Key ID |
| **Railway** | `R2_SECRET_ACCESS_KEY` | Cloudflare R2 Secret Access Key |
| **Railway** | `R2_BUCKET_NAME` | `linguflow-media` |
| **Railway** | `R2_ENDPOINT_URL` | `https://<ACCOUNT_ID>.r2.cloudflarestorage.com` |

---

## 5. Verification Steps

1. **Frontend Typecheck & Build**: Run `npm run build` inside `frontend/`.
2. **Backend Startup**: For a production-like boot, use `./entrypoint.sh` or `alembic upgrade head && python -m app.seed.exam_seed && uvicorn app.main:app --port 8000` inside `backend/` (with `.env` set up). Plain `uvicorn` alone does not seed built-in exams.

3. **Health Check**: Call `GET /api/health` on your deployed backend.
4. **Media Presigned Endpoint**: Test `POST /api/media/presign-upload` with JSON body `{"filename": "test.jpg", "content_type": "image/jpeg"}`.
