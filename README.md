# Privacy Eye 👁️

> **AI Can Fake It. Privacy Eye Can Check It.**

Privacy Eye is a production-grade digital authenticity and deepfake detection platform. Built for enterprise defense, high-speed live camera streams, and forensic media verification, it combines deep learning classifiers with spatial, temporal, biometric, and frequency-domain signals.

---

## 1. System Architecture

```text
                                PRIVACY EYE
                                     │
               ┌─────────────────────┴─────────────────────┐
               │                                           │
         FRONTEND (Next.js 14)                     BACKEND (FastAPI)
         Deployed on Vercel                        Container / Cloud Run / Railway
               │                                           │
         HTTPS Requests                      ┌─────────────┼─────────────┐
         (Live Camera Stream)                │             │             │
               │                        PostgreSQL     Model Cache   Object Storage
               └──────────────────────►  (Database)    (Persistent)   (Media/S3)
                                                           │
                                                   Hugging Face Hub
                                                   (Large ML Models)
```

- **Frontend**: Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS, Framer Motion, 3D Canvas Visualizer, Dark Frosted Glassmorphism.
- **Backend**: FastAPI, Python 3.11, Uvicorn, SQLAlchemy (Asyncpg), OpenCV, ONNX Runtime.
- **Database**: PostgreSQL with connection pooling.
- **Model Storage**: Hugging Face Hub (decoupled from the Git repository).
- **Security**: The browser **never** connects directly to PostgreSQL. All requests route through the FastAPI gateway with JWT authentication.

---

## 2. Decoupled Model Architecture

To keep the GitHub source repository lightweight (< 2 MB) and avoid large binary blobs, all heavy machine learning models are managed through **Hugging Face Hub** and cached locally via `ModelManager`:

| Model Name | Checkpoint Size | Framework | Storage Target | Runtime Purpose |
|---|---|---|---|---|
| `face_detection_yunet` | 232 KB | OpenCV / ONNX | `privacy-eye/privacy-eye-models` | 5-landmark face detector & active liveness |
| `image_efficientnet_b4`| 78.6 MB | ONNX Runtime | `privacy-eye/privacy-eye-models` | Spatial deepfake detector (FF++ c23) |
| `video_efficientnet_temporal` | 157.3 MB | ONNX Runtime | `privacy-eye/privacy-eye-models` | Frame-sampled temporal consistency classifier |
| `audio_wav2vec2_clone` | 377.5 MB | ONNX Runtime | `privacy-eye/privacy-eye-models` | Wav2Vec2 neural voice clone discriminator |

For full details, see [`docs/model-storage.md`](docs/model-storage.md) and [`models/manifest.json`](models/manifest.json).

---

## 3. Local Development

### Prerequisites
- Node.js 18+ & npm
- Python 3.11+
- PostgreSQL 15+ (or Docker Compose)

### Quick Start with Docker Compose
```bash
# Clone the repository
git clone https://github.com/Hasrhu/privacy-eye.git
cd privacy-eye

# Spin up PostgreSQL, FastAPI backend, and Next.js frontend
docker compose up -d
```
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`
- Health Probe: `http://localhost:8000/health`
- Readiness Probe: `http://localhost:8000/ready`

### Manual Local Setup

#### Backend (FastAPI)
```bash
cd backend
python -m venv venv
# On Windows: venv\Scripts\activate
# On Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend (Next.js)
```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

---

## 4. Environment Variables

Template files with safe default examples are provided in each directory:
- Frontend: [`frontend/.env.example`](frontend/.env.example)
- Backend: [`backend/.env.example`](backend/.env.example)

> **Important**: Never commit `.env` or `.env.local` files to Git. All secrets, private keys, database passwords, and tokens are strictly excluded via `.gitignore`.

---

## 5. Production Deployment

- **Frontend (Vercel)**: Point Vercel to `frontend/` as the Root Directory. Set `NEXT_PUBLIC_API_URL` to your backend URL.
- **Backend (Container Platforms)**: Deploy `backend/Dockerfile` to Railway, Render, Fly.io, AWS ECS, or GCP Cloud Run.
- **Database (PostgreSQL)**: Set `DATABASE_URL=postgresql+asyncpg://...` in the backend environment.

Comprehensive step-by-step instructions are available in [`docs/deployment.md`](docs/deployment.md).

---

## 6. Verification & Health Monitoring

The platform provides standard HTTP health probes:

```bash
# Check liveness
curl http://localhost:8000/health

# Check readiness (validates DB connectivity and ML model statuses)
curl http://localhost:8000/ready
```

---

## 7. Security Policy

- **No Secrets in Source**: Codebase is protected by strict `.gitignore` rules and continuous scanning.
- **Probabilistic Transparency**: Privacy Eye reports confidence intervals and explainable forensic signals. Results are probabilistic indicators to assist human verification.
- **Privacy By Design**: Video frames and biometric face crops are analyzed in-memory and ephemeral unless user consent is explicitly granted for anonymized benchmark curation.

---

## 8. License & Governance

Licensed under the Apache-2.0 License. See `LICENSE` for details.
