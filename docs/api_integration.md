# Privacy Eye — API Integration Specification

## 1. Overview & Connection Architecture

The Privacy Eye frontend interfaces exclusively with the **FastAPI REST API**. 

```
Browser (Next.js 14)
       │
       ▼  HTTPS / REST + JSON / Multipart
FastAPI Backend (http://127.0.0.1:8000/api/v1)
       │
       ├─► Live Authenticity Engine (YuNet + FF++ + Celeb-DF + Silent-Face + FFHQ)
       ├─► Forensic Classifiers (ELA, FFT, Audio Mel, Noise Residuals)
       └─► PostgreSQL (Async SQLAlchemy Session)
```

> **Security Rule:** Under no circumstances does the browser communicate directly with PostgreSQL. Database credentials are never bundled into the client build.

---

## 2. Environment Configuration

The frontend dynamically resolves API URLs via environment variables:

```bash
# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_APP_NAME="Privacy Eye"
NEXT_PUBLIC_ENVIRONMENT=development
```

When deployed behind tunnels or reverse proxies (e.g. Cloudflare Tunnels), `NEXT_PUBLIC_API_URL` is set to the public origin endpoint.

---

## 3. Comprehensive Endpoint Catalog & Schemas

### 3.1 Authentication (`/auth`)

| Method | Endpoint | Description | Request Payload | Response Schema |
|---|---|---|---|---|
| `POST` | `/auth/register` | Register new user | `{ email, password, full_name? }` | `User` object |
| `POST` | `/auth/login` | Authenticate & get tokens | `{ email, password }` | `{ access_token, refresh_token, token_type }` |
| `POST` | `/auth/refresh` | Refresh expired JWT | Query param: `refresh_token` | `{ access_token, token_type }` |
| `GET` | `/auth/me` | Fetch authenticated user | Header: `Bearer <token>` | `User` object |

### 3.2 Media Forensics & Analysis (`/analyze`)

| Method | Endpoint | Content-Type | Payload | Output |
|---|---|---|---|---|
| `POST` | `/analyze/image` | `multipart/form-data` | `file: File` (Max 20MB) | `AnalysisResponse` |
| `POST` | `/analyze/video` | `multipart/form-data` | `file: File` (Max 500MB) | `AnalysisResponse` |
| `POST` | `/analyze/audio` | `multipart/form-data` | `file: File` (Max 50MB) | `AnalysisResponse` |
| `GET` | `/analyze/{id}` | `application/json` | Path: `id: UUID` | `AnalysisResponse` with full signals & provenance |
| `GET` | `/analyze/history`| `application/json` | Params: `page`, `per_page`, `media_type` | `AnalysisListResponse` |
| `DELETE`| `/analyze/{id}` | `application/json` | Path: `id: UUID` | `{ message: "Analysis deleted" }` |
| `GET` | `/analyze/stats` | `application/json` | — | `DashboardStats` |

#### `AnalysisResponse` Schema:
```typescript
interface AnalysisResponse {
  id: string;
  original_filename: string;
  media_type: 'IMAGE' | 'VIDEO' | 'AUDIO';
  file_size_bytes: number;
  file_sha256: string | null;
  mime_type: string | null;
  duration_seconds: number | null;
  status: 'PENDING' | 'PROCESSING' | 'COMPLETE' | 'FAILED';
  risk_level: 'LOW' | 'SUSPICIOUS' | 'HIGH' | 'CRITICAL' | 'UNDETERMINED' | null;
  synthetic_probability: number | null;
  confidence: number | null;
  explanation: string | null;
  signals: Array<{
    signal_key: string;
    signal_label: string;
    severity: 'low' | 'medium' | 'high';
    score: number | null;
    description: string | null;
  }>;
  raw_scores: Record<string, unknown> | null;
  provenance_info: Record<string, unknown> | null;
  media_deleted: boolean;
  processing_ms: number | null;
  created_at: string;
  updated_at: string;
}
```

### 3.3 Live Camera Authenticity Engine (`/live`)

| Method | Endpoint | Purpose | Request Payload |
|---|---|---|---|
| `POST` | `/live/frame` | Real-time multi-benchmark frame inference | `FrameAnalysisPayload` (`session_id`, `image_base64`, `run_challenge`) |
| `POST` | `/live/challenge` | Generate randomized head pose nonce | Params: `session_id` |
| `POST` | `/live/save-audit` | Persist audit session & snapshot | `SaveAuditSessionPayload` |
| `POST` | `/live/consent-response` | Opt-in/out training data consent | `ConsentResponsePayload` |
| `GET` | `/live/training-stats` | Pool size of consented real samples | None |

#### Live Frame Response Schema:
```typescript
interface LiveFrameResponse {
  assessment: string;              // e.g. "REAL_HUMAN_FACE", "LIKELY_HUMAN_FACE", "SUSPICIOUS_PRESENTATION_ATTACK"
  category_label: string;          // e.g. "Real human face", "Likely as human face"
  confidence: number;              // 0.0 - 100.0 (calibrated, movement-responsive)
  reliability: 'HIGH' | 'MEDIUM' | 'LOW';
  quality: {
    quality_index: number;
    sharpness_score: number;
    sharpness_label: 'SHARP' | 'ACCEPTABLE' | 'BLURRY';
    mean_brightness: number;
    lighting_label: string;
    contrast_score: number;
    face_coverage_pct: number;
    face_centered: boolean;
    user_guidance: string[];
  };
  face_detected: boolean;
  face_box?: [number, number, number, number]; // [x, y, w, h]
  landmarks?: {
    right_eye: [number, number];
    left_eye: [number, number];
    nose_tip: [number, number];
    right_mouth: [number, number];
    left_mouth: [number, number];
  };
  head_pose?: {
    yaw: number;
    pitch: number;
    mouth_ratio: number;
    iod: number;
  };
  liveness_score: number;
  spatial_risk: number;
  presentation_risk: number;
  explanation: string;
  signals: Array<{
    key: string;
    label: string;
    severity: 'low' | 'medium' | 'high';
    detail?: string;
    score?: number;
  }>;
  criteria_evaluation: {
    total_matches: number;
    all_matched: boolean;
    blinks: { count_10s: number; matched: boolean; label: string };
    movements: { yaw_span: number; pitch_span: number; matched: boolean; label: string };
    lips: { angle_diff_deg: number; mouth_ratio: number; matched: boolean; label: string };
  };
  guided_protocol: {
    total_marked: number;
    all_marked: boolean;
    task_1_smile: { marked: boolean; teeth_detected: boolean; lips_wide: boolean; label: string };
    task_2_blinks: { marked: boolean; blink_count: number; target: number; label: string };
    task_3_rotation: { marked: boolean; yaw_span: number; smooth: boolean; label: string };
  };
  ear_accessories: {
    detected: boolean;
    accessory_type: 'OVER_EAR_HEADPHONES' | 'IN_EAR_EARBUDS' | 'NONE';
    confidence: number;
    label: string;
  };
  benchmarks: {
    faceforensics: { score: number; is_manipulated: boolean; method: string };
    celeb_df: { score: number; is_deepfake: boolean };
    silent_face: { score: number; is_presentation_attack: boolean; attack_type: string };
    ffhq_baseline: { texture_realism_score: number; is_organic: boolean; policy: string };
  };
  processing_location: string;    // "EDGE / LOCAL SERVER"
  processing_ms: number;
  disclaimer: string;
}
```

### 3.4 Dataset & Governance (`/dataset`)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/dataset/stats` | Dataset distribution across Categories A, B, C, D, E |
| `POST` | `/dataset/records` | Ingest validated forensic dataset record |
| `POST` | `/dataset/quality-gate` | Evaluate frame quality before ingestion |
| `GET` | `/dataset/failure-cases` | Retrieve documented false positives & failure cases |

### 3.5 Security Reports (`/reports`)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/reports/{id}/generate` | Generate formal forensic PDF/JSON security report |
| `GET` | `/reports/{id}` | Retrieve formatted security report summary & recommendations |
| `GET` | `/reports/{id}/download/json` | Stream full cryptographically hashed JSON evidence audit |

---

## 4. Error Handling & Normalization

All service calls funnel errors through `getErrorMessage(err: unknown)`:
- **401 Unauthorized:** Cookies cleared, user redirected to `/auth/login`.
- **413 Payload Too Large:** Formatted prompt indicating maximum file sizes (20MB Image, 500MB Video).
- **422 Validation Error:** Pydantic validation errors concatenated into human-readable bullet points.
- **500 / Network Down:** Graceful fallback messaging displayed inside frosted error cards without revealing internal stack traces.
