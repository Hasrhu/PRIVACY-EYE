# Privacy Eye — Production Deployment Guide

This guide details the steps to deploy the **Privacy Eye** platform into production across modern cloud infrastructure.

---

## 1. System Architecture

```text
                                PRIVACY EYE
                                     │
               ┌─────────────────────┴─────────────────────┐
               │                                           │
         FRONTEND (Next.js 14)                     BACKEND (FastAPI)
         Vercel Edge Platform                      Container / Cloud Run / Railway
               │                                           │
         HTTPS Requests                      ┌─────────────┼─────────────┐
         (Browser Camera)                    │             │             │
               │                        PostgreSQL     Model Cache   Object Storage
               └──────────────────────►  (Database)    (Persistent)   (Media/S3)
                                                           │
                                                   Hugging Face Hub
                                                   (Large ML Models)
```

> **Security Rule**: The browser **never** connects directly to PostgreSQL or Hugging Face private endpoints. All traffic routes through the authenticated FastAPI gateway.

---

## 2. Frontend Deployment (Vercel)

### Step 1: Connect GitHub Repository
1. Log into your [Vercel Dashboard](https://vercel.com).
2. Click **Add New...** → **Project**.
3. Select the `Hasrhu/privacy-eye` repository.

### Step 2: Configure Project Settings
- **Framework Preset**: `Next.js`
- **Root Directory**: `frontend` *(Mandatory: click Edit and select `frontend`)*
- **Build Command**: `next build` (or default `npm run build`)
- **Output Directory**: `.next` (default)
- **Install Command**: `npm install` (default)

### Step 3: Environment Variables
Add the following in Vercel **Settings** → **Environment Variables**:

| Variable | Example Value | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `https://api.yourdomain.com/api/v1` | Public URL of your deployed FastAPI backend |
| `NEXT_PUBLIC_APP_URL` | `https://privacy-eye.vercel.app` | Canonical domain for your frontend application |
| `NEXT_PUBLIC_APP_NAME` | `Privacy Eye` | Display branding |
| `NEXT_PUBLIC_API_DOCS_URL`| `https://api.yourdomain.com/docs` | Public link to Swagger OpenAPI documentation |

> **Caution**: Never put database passwords, `HF_TOKEN`, or private keys in variables prefixed with `NEXT_PUBLIC_`.

---

## 3. Backend Deployment (Docker / Cloud Run / Railway / Render)

The backend provides a standardized, non-root, slim `Dockerfile` with automated health checks and dynamic `$PORT` assignment.

### Option A: Deploy via Docker (Recommended)
1. **Container Context**: `backend`
2. **Dockerfile Path**: `backend/Dockerfile`
3. **Container Port**: Configured automatically via `$PORT` (defaults to `8000`).

### Option B: Deploy on Platform-as-a-Service (Render / Railway / Fly.io)
1. Set **Root Directory** to `backend`.
2. Set **Build Command** to:
   ```bash
   pip install --no-cache-dir -r requirements.txt
   ```
3. Set **Start Command** to:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
   ```

### Backend Environment Variables
Configure the following server-side environment variables:

| Variable | Example Value | Purpose |
|---|---|---|
| `APP_ENV` | `production` | Enables strict CORS and security headers |
| `APP_SECRET_KEY` | `32+ random characters` | Session encryption |
| `JWT_SECRET_KEY` | `32+ random characters` | Auth token signing |
| `DATABASE_URL` | `postgresql+asyncpg://user:pass@host:5432/dbname` | Async database pool connection |
| `DATABASE_URL_SYNC` | `postgresql://user:pass@host:5432/dbname` | Synchronous migration connection |
| `CORS_ORIGINS` | `https://privacy-eye.vercel.app` | Allowed origins (comma-separated) |
| `MODEL_REPOSITORY` | `privacy-eye/privacy-eye-models` | Hugging Face Hub model repository |
| `MODEL_REVISION` | `main` | Model Git revision/tag |
| `MODEL_CACHE_DIR` | `/app/models_cache` | Local directory for cached model weights |
| `HF_TOKEN` | `hf_...` | Hugging Face token (only if model repo is private) |
| `AUTO_DOWNLOAD_MODELS` | `true` | Fetch missing models automatically on boot |
| `ML_DEVICE` | `cpu` (or `cuda`) | Inference runtime device |

---

## 4. Database Setup (PostgreSQL)

Privacy Eye uses SQLAlchemy with `asyncpg` for high-throughput non-blocking database queries.

1. **Provision a PostgreSQL 15+ database** (Neon, Supabase, AWS RDS, or Render Postgres).
2. Set `DATABASE_URL=postgresql+asyncpg://<username>:<password>@<host>:<port>/<dbname>`.
3. In local Docker environments:
   ```bash
   docker compose up -d db
   ```
4. Tables are automatically verified and initialized upon FastAPI startup via `lifespan` handler.

---

## 5. Machine Learning Model Storage (Hugging Face Hub)

Privacy Eye separates heavy ML checkpoints (~10 GB cumulative) from the GitHub Git repository:

1. **Lightweight face detector** (`face_detection_yunet.onnx`, 232 KB) is verified via SHA-256 and auto-downloaded if not in cache.
2. **Heavy deepfake classifiers** (`image_efficientnet_b4.onnx`, `video_efficientnet_temporal.onnx`, `audio_wav2vec2_clone.onnx`) reside on Hugging Face Hub.
3. When the container starts:
   - `ModelManager` checks `MODEL_CACHE_DIR`.
   - Downloads required models **once** using `huggingface_hub` or HTTP fallback.
   - Verifies SHA-256 integrity before loading.
   - Reuses in-memory singletons across multiple requests (never redownloading per inference call).
   - If offline or weights are absent, gracefully defaults to the multi-signal forensic suite without downtime.

---

## 6. Health & Readiness Probes

Expose these endpoints to your load balancer or container orchestrator:

- **Liveness Probe**:
  `GET /health` → Returns `200 OK` when the FastAPI server process is active.
- **Readiness Probe**:
  `GET /ready` → Verifies database connection pool and reports operational status of ML models:
  ```json
  {
    "status": "ready",
    "api": "READY",
    "database": "READY",
    "models": "READY",
    "details": {
      "device": "cpu",
      "repository": "privacy-eye/privacy-eye-models",
      "models_count": 4
    }
  }
  ```
