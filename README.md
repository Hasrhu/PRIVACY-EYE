# Privacy Eye 👁️

> **AI Can Fake It. Privacy Eye Can Check It.**

Privacy Eye is a **privacy-first AI-powered digital authenticity and deepfake detection platform** that identifies potentially AI-generated or manipulated images, videos, audio, voices, and synthetic media.

---

## Architecture

```
PRIVACY EYE
│
├── frontend/     Next.js 14 + TypeScript + Tailwind CSS
├── backend/      Python 3.11 + FastAPI + SQLAlchemy
├── ml/           PyTorch + OpenCV + librosa + Transformers
├── agents/       Gemini API-powered AI agents
├── docs/         Architecture + API docs
├── tests/        Unit + integration + security + ML tests
└── docker/       Docker Compose for full stack
```

---

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.11+
- PostgreSQL 15+
- (Optional) CUDA-capable GPU

### 1. Clone & Setup

```bash
git clone https://github.com/your-org/privacy-eye.git
cd privacy-eye
cp .env.example .env
# Edit .env with your secrets
```

### 2. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
alembic upgrade head          # Run DB migrations
uvicorn app.main:app --reload --port 8000
```

### 3. ML Models

```bash
cd ml
python scripts/download_models.py   # Download pretrained weights
```

### 4. Frontend

```bash
cd frontend
npm install
npm run dev                          # http://localhost:3000
```

### 5. Docker (Full Stack)

```bash
docker compose up --build
```

---

## Tech Stack

| Layer       | Technology                                       |
|-------------|--------------------------------------------------|
| Frontend    | Next.js 14, React 18, TypeScript, Tailwind CSS   |
| Backend     | Python 3.11, FastAPI, SQLAlchemy, Alembic        |
| Database    | PostgreSQL 15                                    |
| ML/AI       | PyTorch, OpenCV, librosa, Transformers, ONNX     |
| AI Agents   | Google Gemini API                                |
| Auth        | JWT + bcrypt                                     |
| Storage     | Local temp (S3-compatible in production)         |
| DevOps      | Docker, Docker Compose, GitHub Actions           |

---

## API Documentation

After starting the backend, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Environment Variables

See [`.env.example`](.env.example) for all required variables.

---

## Disclaimer

Privacy Eye is an AI-assisted detection tool. It does **not** claim 100% accuracy. Results should be interpreted as probabilistic indicators, not definitive conclusions. Always apply human judgment.

---

## License

MIT License
