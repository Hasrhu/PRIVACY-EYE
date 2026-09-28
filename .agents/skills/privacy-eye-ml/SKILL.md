---
name: privacy-eye-ml
description: >-
  Lead Machine Learning & Deepfake Forensic Engineering Skill for Privacy Eye.
  Provides authoritative procedures, architectural guidelines, leakage audits,
  benchmark evaluation protocols, confidence calibration, and two-stage cascade execution.
---

# Privacy Eye ML Engineering Skill & Runbook

This skill defines the technical workflows, standards, and evaluation protocols for developing, auditing, and deploying Privacy Eye's live face authenticity and presentation attack detection (PAD) models.

---

## 1. Cardinal Engineering Principles

When working on any Privacy Eye machine learning task, strictly uphold these non-negotiables:

1. **Abstain with `UNABLE_TO_DETERMINE`**: Never force a binary classification on degraded or out-of-distribution inputs. If lighting is $<30\text{ lux}$, motion blur is high, or face resolution is $<64\times 64$, return `UNABLE_TO_DETERMINE`.
2. **Never Claim 100% Certainty**: Human authenticity detection is fundamentally probabilistic. Avoid declaring any subject "definitely real".
3. **Absolute Data Isolation**:
   - Zero subject identity overlap across Train, Validation, and Test splits.
   - Video-level splitting must occur before frame extraction.
   - Always evaluate models against **unseen generative families** (e.g. FLUX.1/SDXL if trained on StyleGAN2/SD 1.5).
4. **No Demographic Profiling**: Do not infer, classify, or store demographic attributes (race, gender, sexual orientation, emotion). Visual physical variance must focus on rendering physics (lighting, accessories, optics, angles, compression).
5. **Fail-Closed Architecture**: If a model checkpoint or inference worker encounters an exception, **never default to "REAL"**. Trigger the circuit breaker and return `UNABLE_TO_DETERMINE`.

---

## 2. Standard Diagnostic & Verification Runbook

### Step 1: Environment & Hardware Audit
Before running training or heavy evaluation experiments, inspect compute capabilities:
```powershell
python scripts/check_environment.py
```
- **VRAM Constraint**: The local RTX 3050 has 4GB VRAM. Ensure spatial model batch sizes do not exceed 8 (FP16) and temporal 16-frame sequence batch sizes do not exceed 2.

### Step 2: Dataset Leakage Audit
Before starting any training epoch, validate the dataset manifest for subject, video, and generator isolation:
```powershell
python scripts/check_dataset_leakage.py datasets/manifest.csv
```
The script must return `[VERDICT: PASSED]` before training can proceed.

### Step 3: Run Full Benchmark & Quality Test Suite
Verify that all core modules, quality gates, OOD detectors, and benchmark analyzers pass automated tests:
```powershell
python -m unittest discover backend/tests
```

---

## 3. Two-Stage Real-Time Execution Protocol

For live camera processing, adhere to the two-stage cascade:

```
Camera Frame
    │
    ▼
QualityGate.evaluate_face_crop()
    │
    ├── [FAIL] ──> Emit UNABLE_TO_DETERMINE (User guidance: "Move closer / Improve lighting")
    │
    ▼ [PASS]
Stage 1: Lightweight Edge Detector (<30 ms)
    │  - YuNet Face Landmark Tracker
    │  - MiniVision MiniFASNet Dual-Crop Fourier PAD
    │  - Active Challenge Nonce Verifier
    │
    ├── [High Certainty] ──> Emit Calibrated Risk State
    │
    ▼ [Uncertain / Low Margin]
Stage 2: Heavyweight Forensic Cloud (120-250 ms)
    │  - 16-Frame Spatio-Temporal FTCN Sequence Incoherence
    │  - Self-Blended Images (SBI) Boundary Analyzer
    │  - Energy-Based Out-of-Distribution (OOD) Detector
    │  - Multi-Signal Metaclassifier Fusion
    ▼
Final Probabilistic State + Reliability Index
```

---

## 4. Confidence Calibration & Output Taxonomy

Never expose raw neural network softmax outputs directly to users. Apply temperature scaling ($T \approx 1.25$–$1.35$) and map calibrated probabilities to the hierarchical state space:

| State Key | Calibrated Confidence Band | Interpretation |
|---|---|---|
| `LIKELY_LIVE_HUMAN` | $\ge 85.0\%$ | Multi-signal live human presence verified across all branches. |
| `LIKELY_LIVE_HUMAN` | $70.0\% - 84.9\%$ | Likely human face with moderate confidence. |
| `SUSPICIOUS` | $60.0\% - 69.9\%$ | Need more clarity of face or camera stabilization. |
| `SUSPICIOUS` | $< 60.0\%$ | Face is not likely human; suspicious authenticity cues. |
| `POSSIBLE_REPLAY` | Replay Risk $\ge 70.0\%$ | Screen moiré, pixel grid, or display refresh lines detected. |
| `POSSIBLE_FACE_SWAP` | Swap Risk $\ge 70.0\%$ | Boundary feathering or color temperature mismatch detected. |
| `POSSIBLE_PRESENTATION_ATTACK`| PAD Risk $\ge 70.0\%$ | Printed photo, paper surface, or planar mask detected. |
| `UNABLE_TO_DETERMINE` | Degraded Quality / OOD | Input quality degraded or out-of-distribution. |

---

## 5. Hard-Negative Mining Loop

When an inference failure is identified:
1. Log the case in `datasets/failure_cases.csv` with `failure_id`, `model_version`, `true_label`, `prediction`, `confidence`, and `reason`.
2. A human reviewer verifies and approves the case via `POST /api/v1/dataset/failure-cases/{id}/review`.
3. Add the approved sample to `CATEGORY_E_HARD_NEGATIVE` in the dataset registry.
4. Retrain the model and verify that False Rejection Rate ($\text{FRR}$) decreases without increasing False Acceptance Rate ($\text{FAR}$).
