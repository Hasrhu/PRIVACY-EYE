# Privacy Eye — Railway (Backend) & Vercel (Frontend) Deployment Guide

This guide details the complete, step-by-step process to deploy Privacy Eye to production with public HTTPS links:
* **Backend**: FastAPI + Computer Vision ML Engine deployed on **Railway** via Docker.
* **Frontend**: Next.js 14 Dark Frosted Glass App deployed on **Vercel**.

---

## Architecture Overview

```
                      +-----------------------------------+
                      |         End User Browser          |
                      +-----------------+-----------------+
                                        |
                 https://privacy-eye.vercel.app
                                        v
                      +-----------------------------------+
                      |      Vercel (Next.js 14)          |
                      |   Root Directory: /frontend       |
                      +-----------------+-----------------+
                                        |
                      Internal Proxy / Direct API Calls
                                        |
                 https://privacy-eye-backend.up.railway.app
                                        v
                      +-----------------------------------+
                      |    Railway (FastAPI + ML Engine)  |
                      |   Root Directory: /backend        |
                      |   (Docker: Python 3.11 + libgl1)  |
                      +-----------------------------------+
```

---

## Part 1: Deploy Backend to Railway

Railway provides container hosting with automatic HTTPS, persistent domains, and generous memory suitable for computer vision and PyTorch CPU inference.

### Step 1: Push Code to GitHub
Ensure your latest changes are pushed to your GitHub repository:
```bash
git push origin main
```

### Step 2: Create a New Project on Railway
1. Go to [railway.app](https://railway.app) and sign in with GitHub.
2. Click **"+ New Project"** in the top right.
3. Select **"Deploy from GitHub repo"**.
4. Choose your repository: **`Hasrhu/PRIVACY-EYE`**.

### Step 3: Configure Service Settings
1. Click on the newly created service tile in your Railway canvas.
2. Go to the **"Settings"** tab:
   - **Root Directory**: Enter `/backend` (or leave empty if using root `railway.toml`).
   - **Builder**: Select **Dockerfile** (Railway will automatically detect `backend/Dockerfile`).
3. Under **"Networking"**, click **"Generate Domain"** to create a public URL (e.g. `https://privacy-eye-production.up.railway.app`).

### Step 4: Configure Environment Variables
Go to the **"Variables"** tab in your Railway service and add the following:

| Variable | Recommended Value | Notes |
| :--- | :--- | :--- |
| `APP_ENV` | `production` | Enables production mode |
| `APP_SECRET_KEY` | *(Click "Generate" or 32+ characters)* | Application cryptographic key |
| `JWT_SECRET_KEY` | *(Click "Generate" or 32+ characters)* | JWT signing secret |
| `PORT` | `8000` | Railway injects this dynamically |
| `CORS_ORIGINS` | `*` | Or comma-separated list of your Vercel domains |
| `DATABASE_URL` | `sqlite+aiosqlite:///./privacyeye.db` | Or connect Railway Postgres plugin |
| `ML_DEVICE` | `cpu` | Uses optimized CPU inference |
| `AUTO_DOWNLOAD_MODELS` | `true` | Downloads models on first startup |

*(Optional)* If you want Gemini AI explanations:
- `GEMINI_API_KEY`: `your_gemini_api_key_here`

### Step 5: Verify Backend Deployment
Once the build completes (usually ~1–2 minutes):
1. Open your Railway public domain in a browser:
   - `https://<your-railway-domain>.up.railway.app/health`
   - You should receive: `{"status":"healthy","version":"1.0.0-mvp"}`
2. Check the interactive API documentation:
   - `https://<your-railway-domain>.up.railway.app/docs`

---

## Part 2: Deploy Frontend to Vercel

Vercel provides edge-accelerated CDN delivery and native support for Next.js 14.

### Step 1: Import Project in Vercel
1. Go to [vercel.com](https://vercel.com) and log in.
2. Click **"Add New..."** > **"Project"**.
3. Import your repository **`Hasrhu/PRIVACY-EYE`**.

### Step 2: Configure Project Settings
1. **Framework Preset**: Ensure **Next.js** is selected.
2. **Root Directory**:
   - Click **"Edit"** next to Root Directory.
   - Select the `frontend` folder and click **"Continue"**.
3. **Build Command**: `npm run build` (default).
4. **Output Directory**: `.next` (default).

### Step 3: Set Environment Variables
Under **"Environment Variables"**, add:

| Key | Value | Purpose |
| :--- | :--- | :--- |
| `NEXT_PUBLIC_API_URL` | `https://<your-railway-domain>.up.railway.app/api/v1` | Public backend API endpoint |
| `BACKEND_API_URL` | `https://<your-railway-domain>.up.railway.app` | Internal proxy target for Next.js rewrites |
| `NEXT_PUBLIC_APP_NAME` | `Privacy Eye` | UI Branding |

### Step 4: Click Deploy
1. Click **"Deploy"**.
2. Vercel will install dependencies, run type checks, compile static and dynamic routes, and assign a production URL (e.g. `https://privacy-eye.vercel.app`).

---

## Part 3: Connecting & Verifying

1. Open your Vercel deployment URL: `https://<your-vercel-project>.vercel.app`.
2. Navigate to **Live Camera Scan** (`/dashboard/live-scan`):
   - Grant camera permissions.
   - Test natural blinking, face movement, and presentation attack scenarios.
3. Test Deepfake Analysis (`/dashboard/analysis`):
   - Upload a test image or video.
   - Confirm upload progress and multi-signal forensic breakdown.
4. Verify that no CORS errors appear in the browser developer console (F12 > Console).

---

## Railway & Vercel Configuration Reference

### Railway Root Configuration (`railway.toml`)
```toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "backend/Dockerfile"

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 120
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3
```

### Next.js Proxy Rewrites (`frontend/next.config.js`)
Next.js automatically proxies `/api/v1/*` calls to the Railway backend, eliminating cross-origin browser complications:
```javascript
async rewrites() {
  const rawBackend = process.env.BACKEND_API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
  const backendUrl = rawBackend.replace(/\/api\/v1\/?$/, '').replace(/\/+$/, '');
  return [
    {
      source: '/api/v1/:path*',
      destination: `${backendUrl}/api/v1/:path*`,
    },
    {
      source: '/docs',
      destination: `${backendUrl}/docs`,
    },
  ]
}
```
