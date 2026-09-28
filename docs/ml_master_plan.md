# Privacy Eye — Master Machine Learning Engineering Plan
**Document Version**: 2.0-Production-Blueprint  
**Status**: APPROVED & ACTIVE  
**Engineering Leads**: Principal ML Engineer, Computer Vision Architect, Cybersecurity & MLOps Lead

---

## 1. Product Objective & Guiding Axiom

Privacy Eye is an enterprise-grade live-camera face authenticity and anti-spoofing system designed to distinguish between:
1. `LIVE_REAL`: A genuine live human physically present in front of the camera.
2. `AI_GENERATED_FACE`: A pure synthetic face rendered by a GAN or Diffusion model.
3. `FACE_SWAP`: A real person's face manipulated or swapped using DeepFaceLab, Face2Face, FaceShifter, etc.
4. `MANIPULATED_LIVE_VIDEO`: Real-time generative neural reenactment or puppet stream.
5. `REPLAY_VIDEO`: A prerecorded video of a genuine person played back in front of the sensor.
6. `PHOTO_ATTACK`: A printed photograph (matte, glossy, or folded).
7. `SCREEN_ATTACK`: A digital display (smartphone, tablet, laptop, monitor) showing a face.
8. `MASK/PRESENTATION_ATTACK`: A 3D physical or silicone mask attack.
9. `UNKNOWN`: An attack pattern that deviates from in-distribution forensic manifolds.
10. `UNABLE_TO_DETERMINE`: Insufficient illumination, severe blur, or out-of-distribution input.

### Core Product Principles:
- **The System Answers**: *"How much evidence is there that this observed media is consistent with a live genuine person, synthetic media, or a presentation/manipulation attack?"*
- **The System Rejects**: False binary certainty. It never proclaims *"This person is 100% definitely real."*
- **The Golden Rule**: **"Abstain with `UNABLE_TO_DETERMINE` when evidence is degraded or conflicting, rather than emitting a high-confidence mistake."**
- **Strict Anti-Profiling**: No demographic, ethnic, gender, or emotional inference is ever collected, inferred, or stored.

---

## 2. End-to-End Primary Architecture

```
                                CAMERA FEED
                                     │
                                     ▼
                            ┌─────────────────┐
                            │  FRAME CAPTURE  │
                            └────────┬────────┘
                                     │
                                     ▼
                            ┌─────────────────┐
                            │ FACE DETECTION  │  (OpenCV YuNet / MediaPipe)
                            └────────┬────────┘
                                     │
                                     ▼
                            ┌─────────────────┐
                            │  FACE TRACKING  │  (Landmark temporal trajectory)
                            └────────┬────────┘
                                     │
                                     ▼
                            ┌─────────────────┐
                            │  QUALITY GATE   │  (Size, Sharpness, Exposure, Blur)
                            └────────┬────────┘
                                     │ (Passed)
                                     ▼
                            ┌─────────────────┐
                            │ TEMPORAL BUFFER │  (16-frame sliding FIFO window)
                            └────────┬────────┘
                                     │
         ┌───────────────────┬───────┴───────────┬───────────────────┐
         ▼                   ▼                   ▼                   ▼
  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
  │  BRANCH 1   │     │  BRANCH 2   │     │  BRANCH 3   │     │  BRANCH 4   │
  │   Spatial   │     │  Temporal   │     │  Liveness   │     │   Replay    │
  │  Artifacts  │     │ Incoherence │     │(Pass/Active)│     │PAD / Moiré  │
  └──────┬──────┘     └──────┬──────┘     └──────┬──────┘     └──────┬──────┘
         │                   │                   │                   │
         └───────────────────┼───────────────────┴───────────────────┘
                             ▼
                    ┌─────────────────┐
                    │ OPTIONAL AUDIO  │  (AASIST voice clone & AV sync)
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ EVIDENCE FUSION │  (Multi-Signal Metaclassifier)
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   CALIBRATION   │  (Temperature Scaling / ECE)
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   RISK ENGINE   │  (Hierarchical State Mapping)
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │TEMPORAL SMOOTH  │  (Hysteresis & Consensus Window)
                    └────────┬────────┘
                             │
                             ▼
                   FINAL RESULT / ABSTAIN
```

---

## 3. Two-Stage Cascade Execution Model

To balance sub-second real-time responsivity with heavyweight forensic accuracy:

```
STAGE 1: LIGHTWEIGHT REAL-TIME FILTER (<30 ms)
- Target: Client Edge (Browser WebAssembly / Local Python Worker)
- Modules:
  * YuNet Face Detector (335 KB)
  * Laplacian & Luminance QualityGate (<2 ms)
  * MiniVision MiniFASNet Dual-Scale PAD (3.2 MB, <5 ms)
  * Active Challenge Nonce Verifier
- Outcome:
  * If Bona Fide Human Confidence >= 95% AND Replay Risk <= 5% -> Emit LIKELY_LIVE_HUMAN
  * If Screen/Print Moiré Spike >= 85% -> Emit POSSIBLE_REPLAY
  * If Uncertain / Borderline -> Escalate to Stage 2

STAGE 2: HEAVYWEIGHT FORENSIC CLOUD (120–250 ms)
- Target: GPU Worker (RTX 3050 CUDA / Server Cluster)
- Modules:
  * 16-Frame Spatio-Temporal FTCN Sequence Incoherence
  * Self-Blended Images (SBI) Facial Perimeter Boundary Analysis
  * 2D FFT & DCT Frequency Domain Artifact Extraction
  * Energy-Based Out-of-Distribution (OOD) Novel Attack Detector
  * Calibrated Evidence Fusion Metaclassifier
- Outcome:
  * Emits Calibrated Probabilistic State Space with Reliability Index
```

---

## 4. Phase-by-Phase Implementation Roadmap

### Phase 0 — Research Before Coding (Completed)
- Documented model selection cards across Image, Video, Face, PAD, Audio, and Provenance models.
- Established strict licensing matrix: Commercial production weights isolated from academic-only datasets (FaceForensics++, Celeb-DF, FFHQ).
- Output: [`docs/model_selection_matrix.md`](file:///c:/Users/harsh/.gemini/antigravity-ide/scratch/privacy-eye/docs/model_selection_matrix.md).

### Phase 1 — Hardware / Environment Audit (Completed)
- Audited local host: Windows 11, Intel Core i5-10200H (8 threads), 16GB RAM, NVIDIA GeForce RTX 3050 Laptop GPU (4GB VRAM), CUDA 13.3 driver, 207GB free SSD.
- Established 4GB VRAM training budgets and inference batch limits.
- Output: [`scripts/check_environment.py`](file:///c:/Users/harsh/.gemini/antigravity-ide/scratch/privacy-eye/scripts/check_environment.py) and [`ml/environment_report.md`](file:///c:/Users/harsh/.gemini/antigravity-ide/scratch/privacy-eye/ml/environment_report.md).

### Phase 2 — ML Environment & Dependency Pinning
- Standalone configurations in `configs/` for training, evaluation, and inference.
- Minimal pinned dependencies for inference (`fastapi`, `numpy`, `opencv-python`, `structlog`).
- Isolated Python 3.11 virtualenv for heavy PyTorch training.

### Phase 3 to 13 — Dataset Management, Governance & Splitting
- Five major categories: Category A (Genuine), Category B (Synthetic), Category C (Face-Swap), Category D (Replay/PAD), Category E (Hard Negatives).
- Zero demographic profiling; visual physical diversity targeting rendering physics only.
- Strict subject-disjoint and video-disjoint isolation (70% Train, 15% Val, 15% Test).
- Generator-disjoint evaluation: Train on StyleGAN2/SD 1.5; evaluate zero-shot on FLUX.1/SDXL.
- Probabilistic realistic data augmentations (JPEG, blur, noise, lighting, dropped frames, variable FPS).
- Output: [`docs/dataset_strategy.md`](file:///c:/Users/harsh/.gemini/antigravity-ide/scratch/privacy-eye/docs/dataset_strategy.md) and [`scripts/check_dataset_leakage.py`](file:///c:/Users/harsh/.gemini/antigravity-ide/scratch/privacy-eye/scripts/check_dataset_leakage.py).

### Phase 14 to 25 — Multi-Signal Forensic Branches
- **Face Detection**: Modular interface supporting OpenCV YuNet and MediaPipe.
- **Input QualityGate**: Evaluates size ($\ge 64\times 64$), Laplacian sharpness ($\ge 35$), luminance ($30–230$), motion blur; abstains with `UNABLE_TO_DETERMINE` when unusable.
- **Spatial Model**: SBI boundary blending, ELA residuals, and color space YCbCr chroma distance.
- **Temporal Model**: 16-frame sliding temporal window; inter-frame displacement variance and optical flow continuity.
- **Liveness Model**: Passive 3D parallax micro-jitter + active randomized challenge-response nonces (Turn Left, Turn Right, Smile, Blink 3 Times).
- **Replay Detector**: Dual-scale 1.0/2.7 Fourier spectrum peak-to-average harmonic analysis + LBP texture entropy.
- **Optional Audio / AV Sync**: Speech voice clone detection via AASIST + lip-phoneme synchronization.
- **Identity Consistency**: Tracks feature embedding cosine drift over time (supporting forensic cue only).

### Phase 26 to 31 — Evidence Fusion, Calibration & Hysteresis
- **Evidence Fusion**: Multi-branch logistic / weighted cross-attention fusion (never naive averaging).
- **Model Disagreement**: Epistemic uncertainty computed across conflicting branches; triggers confidence penalty or abstention when signals clash.
- **Calibration**: Temperature scaling and Platt scaling; targets Expected Calibration Error (ECE) $\le 0.045$ and Brier Score $\le 0.08$.
- **Open-Set / OOD Detection**: Free Energy score $E(x) = -T \cdot \log \sum \exp(z_i / T)$ and Mahalanobis distance; unfamiliar inputs routed to `UNABLE_TO_DETERMINE (OOD)`.
- **Temporal Smoothing & Hysteresis**: Rolling 16-frame consensus with asymmetric enter/exit thresholds ($\tau_{\text{enter}} = 0.75$, $\tau_{\text{exit}} = 0.40$) to prevent UI flickering.

### Phase 32 to 37 — Training Protocol & Checkpoint Security
- Transfer learning with frozen backbones, gradual unfreezing, and differential learning rates.
- Class-balanced Focal Loss to combat skew between abundant real faces and rare attack variants.
- Cryptographic SHA-256 verification of all checkpoint weights; zero untrusted `pickle.load` deserialization.
- Separate artifacts: `best_validation.pt`, `best_generalization.pt`, `last_checkpoint.pt`, `training_history.json`.

### Phase 38 to 44 — Benchmark Evaluation, Metrics & Hard-Negative Mining
- Evaluation across 11 isolated stress benches (Subject-disjoint, Generator-disjoint, Device-disjoint, Environment-disjoint, Compression, Replay, Low-Light, Hard-Negative, OOD).
- Full ISO/IEC 30107-3 reporting (APCER, BPCER, EER, ACER, FPS, TTFR, Latency).
- Failure case database (`failure_cases.csv`) logging every high-confidence mistake for human-in-the-loop review.
- Continuous hard-negative mining loop: promoting reviewed failures into Category E training data.
- Internal red-teaming with re-recorded screens, noise perturbations, and challenge replay attempts.
- Output: [`docs/evaluation_strategy.md`](file:///c:/Users/harsh/.gemini/antigravity-ide/scratch/privacy-eye/docs/evaluation_strategy.md) and [`evaluation/generator_disjoint.py`](file:///c:/Users/harsh/.gemini/antigravity-ide/scratch/privacy-eye/evaluation/generator_disjoint.py).

### Phase 45 to 56 — Production Architecture, Backend & Frontend
- **Backend**: FastAPI with async SQLAlchemy 2.0, Pydantic validation, structured logging, rate limiting, and request IDs.
- **Database**: PostgreSQL schema with `dataset_records`, `failure_cases`, `model_registry`, `live_sessions`, `audit_logs`.
- **Circuit Breaker**: If model fails or throws exceptions, system automatically falls back to secondary detector or returns `UNABLE_TO_DETERMINE`. Never defaults to "REAL".
- **Frontend**: Next.js 14 HUD showing calibrated risk bands, multi-signal radar, active challenge indicators, and zero raw video retention.
- **Privacy Guarantee**: Webcam frames exist only in volatile RAM buffers during active live inference and are immediately discarded. No video is stored without explicit user consent.

### Phase 57 to 59 — Antigravity Engineering Execution & Skill Integration
- Rigorous step-by-step verification using real terminal execution.
- Privacy Eye ML Engineering Skill installed at `.agents/skills/privacy-eye-ml/SKILL.md`.
