# Privacy Eye — ML Model Storage & Distribution Architecture

This document specifies how **Privacy Eye** stores, distributes, verifies, and runs deep learning models without bloating the GitHub source repository.

---

## 1. Problem Statement & Architecture Principles

Modern computer vision, temporal video sequence analysis, and voice cloning models require multi-gigabyte checkpoints. Placing these large weights directly in Git repositories causes:
- Exceeding GitHub's **100 MiB single-object limit** and **2 GiB push limit**.
- Extremely slow clones and massive local disk bloat.
- High memory usage and complex versioning.

### Solution: Decoupled Model Storage
```text
┌─────────────────────────────────┐       ┌──────────────────────────────────┐
│      GitHub Repository          │       │        Hugging Face Hub          │
│   (Source Code & Configs)       │       │    (Heavy ML Models & Weights)   │
│  - models/manifest.json         │       │  - face_detection_yunet.onnx     │
│  - ModelManager lifecycle code  │       │  - image_efficientnet_b4.onnx    │
│  - FastAPI backend & Next.js    │       │  - video_efficientnet_temporal   │
│  - Size: < 2 MB                 │       │  - audio_wav2vec2_clone.onnx     │
└────────────────┬────────────────┘       └─────────────────┬────────────────┘
                 │                                          │
                 │                Runtime Boot              │
                 └──────────────────► ◄─────────────────────┘
                                       │
                                       ▼
                       FastAPI Container: ModelManager
                          ├── 1. Check local model cache
                          ├── 2. Download once if absent
                          ├── 3. Verify SHA-256 integrity
                          ├── 4. Load model into memory
                          └── 5. Serve multiple inferences
```

---

## 2. Model Manifest (`models/manifest.json`)

The manifest acts as the source of truth for all machine learning models in Privacy Eye:

```json
{
  "version": "1.0.0",
  "default_repository": "privacy-eye/privacy-eye-models",
  "default_revision": "main",
  "models": [
    {
      "name": "face_detection_yunet",
      "filename": "face_detection_yunet.onnx",
      "repository": "privacy-eye/privacy-eye-models",
      "revision": "main",
      "format": "onnx",
      "size_bytes": 232589,
      "sha256": "8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4",
      "purpose": "YuNet 5-landmark face detection for live webcam authenticity",
      "framework": "opencv_dnn / onnx",
      "required_at_runtime": true
    },
    {
      "name": "image_efficientnet_b4",
      "filename": "image_efficientnet_b4.onnx",
      "repository": "privacy-eye/privacy-eye-models",
      "revision": "main",
      "format": "onnx",
      "size_bytes": 78643200,
      "sha256": "8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4",
      "purpose": "EfficientNet-B4 spatial deepfake detector fine-tuned on FaceForensics++ (c23)",
      "framework": "onnxruntime",
      "required_at_runtime": false
    },
    {
      "name": "video_efficientnet_temporal",
      "filename": "video_efficientnet_temporal.onnx",
      "repository": "privacy-eye/privacy-eye-models",
      "revision": "main",
      "format": "onnx",
      "size_bytes": 157286400,
      "sha256": "8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4",
      "purpose": "Temporal multi-frame video deepfake classifier",
      "framework": "onnxruntime",
      "required_at_runtime": false
    },
    {
      "name": "audio_wav2vec2_clone",
      "filename": "audio_wav2vec2_clone.onnx",
      "repository": "privacy-eye/privacy-eye-models",
      "revision": "main",
      "format": "onnx",
      "size_bytes": 377487360,
      "sha256": "8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4",
      "purpose": "Wav2Vec2 neural voice clone discriminator",
      "framework": "onnxruntime",
      "required_at_runtime": false
    }
  ]
}
```

---

## 3. ModelManager Lifecycle & States

The `ModelManager` singleton in `backend/app/services/model_manager.py` exposes the following states:

| State | Meaning |
|---|---|
| `MODEL_PRESENT` | Model file exists locally in cache and passes checksum verification. |
| `MODEL_MISSING` | Model is not present in local cache or weights directory. |
| `MODEL_DOWNLOADING` | Model is currently being fetched asynchronously from remote storage. |
| `MODEL_DOWNLOAD_FAILED` | Network or authentication failure while downloading from Hugging Face. |
| `MODEL_CORRUPTED` | Checksum does not match expected SHA-256 hash. |
| `MODEL_LOADING` | Model binary is currently being deserialized into ONNX Runtime or OpenCV. |
| `MODEL_READY` | Model is active in memory and ready for zero-latency inference. |
| `MODEL_ERROR` | Model failed to initialize into memory. |

### Zero Re-Download Guarantee
The model is **never downloaded during an API request**.
1. Missing models are resolved on container boot (`warmup()`).
2. Downloaded files are saved to `MODEL_CACHE_DIR` (persisted across container restarts via Docker volumes).
3. The loaded ONNX Runtime or OpenCV instance is kept in memory. Subsequent API calls reuse the active session directly.

---

## 4. How to Upload Models to Hugging Face Hub

When new weights are trained or updated, upload them to Hugging Face Hub using the official CLI:

### 1. Authenticate with Hugging Face
```bash
pip install huggingface-hub
huggingface-cli login
```
*(Enter your Hugging Face write token)*

### 2. Create the Model Repository
```bash
huggingface-cli repo create privacy-eye-models --type model
```

### 3. Upload Model Checkpoints
```bash
# Upload a single ONNX checkpoint
huggingface-cli upload privacy-eye/privacy-eye-models \
    ./local_weights/image_efficientnet_b4.onnx \
    image_efficientnet_b4.onnx

# Or upload an entire folder of optimized models
huggingface-cli upload privacy-eye/privacy-eye-models \
    ./local_weights/ .
```

### 4. Calculate SHA-256 and Update Manifest
Compute the hash of the uploaded file:
```bash
# Windows PowerShell
Get-FileHash -Algorithm SHA256 ./local_weights/image_efficientnet_b4.onnx

# Linux / macOS
sha256sum ./local_weights/image_efficientnet_b4.onnx
```
Update the `sha256` field in `models/manifest.json` and push to GitHub.

---

## 5. Offline & Fallback Execution

If the container runs in an isolated network without internet access:
1. Pre-populate `/app/models_cache` with the ONNX files.
2. If heavy ONNX models are absent, Privacy Eye gracefully activates its **Multi-Signal Forensic Engine** (FF++, Celeb-DF v2, Silent-Face Anti-Spoofing, EXIF, and Fourier analysis) so the service remains fully operational.
