# Privacy Eye — Confidence Architecture & Evidence Fusion Rules

**Component**: Calibrated Risk Engine & Uncertainty Propagation  
**Module**: Multi-Signal Score Decomposition, Thresholding, and Edge-Case Compensation  

---

## 1. Separate Subsystem Score Representations

Privacy Eye strictly forbids collapsing all multi-spectral indicators into a naive binary score. The backend calculates 9 orthogonal normalized scores ($s \in [0.0, 1.0]$):

| Score Key | Symbol | Range | Meaning |
|---|---|---|---|
| `live_human_score` | $S_{\text{human}}$ | $0.0 \dots 1.0$ | Calibrated probability of direct live human observation |
| `synthetic_score` | $S_{\text{synth}}$ | $0.0 \dots 1.0$ | Neural face-swap or inpainting boundary artifact level |
| `replay_score` | $S_{\text{replay}}$ | $0.0 \dots 1.0$ | Moiré, specular glare, or repeated video frame indicator |
| `presentation_attack_score`| $S_{\text{pad}}$ | $0.0 \dots 1.0$ | Physical screen or photo paper bezel presence |
| `eye_visibility_score` | $S_{\text{eye}}$ | $0.0 \dots 1.0$ | Clarity, focus, and open-orbit landmark resolution |
| `blink_evidence_score` | $S_{\text{blink}}$ | $0.0 \dots 1.0$ | Biological blink frequency and challenge compliance |
| `quality_score` | $S_{\text{qual}}$ | $0.0 \dots 1.0$ | Laplacian sharpness, illumination, contrast, face size |
| `temporal_score` | $S_{\text{temp}}$ | $0.0 \dots 1.0$ | Natural physiological saccadic tremor & 3D parallax |
| `spatial_score` | $S_{\text{spat}}$ | $0.0 \dots 1.0$ | Texture realism, micro-pore consistency, FFHQ score |

---

## 2. Risk Hierarchy & Signal Priority

Signals are processed in a strict risk evaluation hierarchy:

```text
1. CRITICAL PRESENTATION ATTACK (Screen/Photo displaying face)
   └─ If confirmed: Human Confidence = 0%, Presentation Risk = 1.0
   
2. INPUT QUALITY GATE (Sensor Noise / Darkness)
   └─ If Quality Index < 15: Low illumination / noise prevents evaluation

3. 3D BIOMETRIC LIVENESS & TEMPORAL STABILITY
   └─ Micro-jitter, head pose rotation, dynamic parallax

4. SPATIAL FORENSICS & DEEPFAKE DETECTORS
   └─ FaceForensics++ c23, Celeb-DF v2 ocular inpainting, FFHQ texture

5. EYE VISIBILITY & BLINK CHALLENGE
   └─ If eyes clear: tracks blinks
   └─ If eyes blurry: marked UNAVAILABLE; relies on steps 3 & 4
   └─ If 25s no blink + challenge fails: applies 20-30% liveness ceiling
```

---

## 3. Edge-Case Compensation Formulas

### 3.1 Blurry or Obscured Eyes (Sunglasses / Hair / Motion)
**Rule**: Never reduce confidence to zero solely because eyes cannot be resolved.

When $S_{\text{eye}} < 0.35$ (blurry or occluded eyes):
- The eye signal is flagged as `UNAVAILABLE`.
- The blink observation timer is **paused** (does not accumulate no-blink time).
- The fused confidence dynamically re-weights spatial and temporal signals:

$$S_{\text{fused}} = 0.50 \cdot S_{\text{temp}} + 0.35 \cdot S_{\text{spat}} + 0.15 \cdot S_{\text{qual}}$$

**Example**:
- Spatial: $0.85$ (Bona fide epidermal texture)
- Temporal: $0.88$ (Natural breathing jitter)
- Replay: $0.05$ (No screen moiré)
- Eyes: `UNAVAILABLE`
- **Result**: `LIKELY LIVE HUMAN`, Confidence: **$82.5\%$**, Eye Status: `EYES_NOT_CLEARLY_VISIBLE`.

---

### 3.2 25-Second No-Blink Challenge & Confidence Ceiling
**Rule**: An extended period without blinking is not automatic proof of an AI deepfake.

```python
if continuous_eye_observation_sec >= 25.0 and blink_count == 0:
    if not challenge_active:
        trigger_challenge("PLEASE_BLINK", duration_sec=5.0)
    elif challenge_expired and not blink_verified:
        # Liveness confidence ceiling enforced
        liveness_confidence_ceiling = 0.28
        overall_reliability = "LOW"
        assessment = "UNABLE_TO_DETERMINE"
        reason_code = "BLINK_CHALLENGE_FAILED"
```

The liveness confidence is capped at **$28\%$** (within the requested $20\% - 30\%$ range), and the system returns `UNABLE_TO_DETERMINE` or `LIKELY_LIVE_HUMAN: NOT VERIFIED`.

---

## 4. Temporal Smoothing & Minimum Observation Windows

To prevent frame-to-frame flickering:

### 4.1 Exponential Moving Average (EMA)
For consecutive frames at time $t$:
$$C_t = \alpha \cdot C_{\text{raw}, t} + (1 - \alpha) \cdot C_{t-1}, \quad \alpha = 0.35$$

### 4.2 Observation Phase Hysteresis
- **$0.0 - 2.0\text{ s}$**: `INITIALIZING` (Building multi-frame optical flow buffer).
- **$2.0 - 4.5\text{ s}$**: `ANALYZING` (Initial biometric consensus).
- **$> 4.5\text{ s}$**: `STABLE ANALYSIS` (Full confidence convergence).
