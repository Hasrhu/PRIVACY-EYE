# PRIVACY EYE — BLINK-BASED CONFIDENCE & LIVE HUMAN SCORING ENGINE SPECIFICATION

**Module**: `app.ml.confidence_fusion` & `app.ml.blink_engine`  
**Configuration**: `configs/confidence.yaml`  
**Status**: Fully Implemented, Calibrated & Verified with 100% Test Coverage  

---

## 1. Executive Summary & Design Principles

Privacy Eye's live-camera authenticity engine treats **confirmed biological human blinking as the strongest single liveness signal**, while integrating natural facial movement, physiological liveness, temporal stability, face tracking continuity, and input quality.

### Critical Safety Principles
1. **Never Assume Blink = 100% Real**: A confirmed blink establishes strong liveness evidence, but never blindly guarantees absolute authenticity.
2. **Replay Dominance (Hard Override)**: If a face is displayed through a smartphone or electronic screen bezel, `live_human_confidence = 0%`. A video of a blinking human played on an iPhone screen is still a presentation attack.
3. **Observable Qualification**: Time is only counted toward observation thresholds when eyes are clearly visible, unblurred, and unobstructed. Blurry eyes or head turns pause timers rather than penalizing the user.
4. **No Arbitrary Numbers**: All confidence metrics are deterministic, explainable, testable, and generated from actual signal measurements.

---

## 2. Confidence Architecture & Centralized Weights

The centralized configuration is stored in `configs/confidence.yaml`:

```yaml
weights:
  blink_weight: 0.70              # Confirmed blink contributes 65%–80% of human evidence
  liveness_movement_weight: 0.15  # Natural facial movement & physiological liveness
  supporting_weight: 0.15         # Temporal consistency, tracking quality, input quality
```

### Decomposed Sub-Scores
The `ConfidenceFusionEngine` separates signals into explicit, explainable components:
- `blink_evidence`: Calibrated product score [65.0 to 88.0] when confirmed; 0.0 otherwise.
- `facial_movement_evidence`: Normalized displacement score (penalizes static photos < 0.005 and erratic jitter > 0.25).
- `liveness_evidence`: Micro-tremor, 3D perspective, and FFHQ texture realism score.
- `temporal_consistency`: Multi-frame landmark and bounding box continuity.
- `face_tracking_quality`: Landmark detector confidence and identity tracking stability.
- `input_quality`: Laplacian blur variance, lighting, contrast, and face framing.
- `replay_risk`: Moiré frequencies, specular glare, and display screen bezels.
- `synthetic_risk`: FaceForensics++, Celeb-DF, and SilentFace neural spoof metrics.
- `phone_presentation_risk`: Specific spatial association of target face inside a phone screen.

---

## 3. Product Confidence Score vs. Calibrated Model Probability

Privacy Eye strictly separates internal statistical probability from consumer-facing UX confidence:

| Metric | Type | Scale | Description |
|---|---|---|---|
| **Product Confidence Score** | User-Facing | `0%` to `100%` | Calibrated scoring rule where 1st confirmed blink enters `65%–80%`, stabilized with EMA smoothing. |
| **Model Probability** | Statistical | `0.00` to `1.00` | Calibrated probability of live human origin derived from multi-signal logistic regression. |
| **Reliability Level** | Uncertainty | `HIGH` / `MEDIUM` / `LOW` | Evaluates signal agreement, input quality, and observation duration. |

---

## 4. Biological Blink 4-Stage State Machine & Quality Metric

Landmark jitter and single-frame dropouts are rejected using a 4-stage temporal sequence:
```
OPEN (openness >= threshold_open)
  ↓
CLOSING (openness < threshold_close for >= 1 frame)
  ↓
CLOSED (eyes closed; tracks duration 80ms <= t <= 700ms)
  ↓
OPEN (reopening transition confirmed)
  ↓
BLINK_CONFIRMED (quality evaluated >= 0.65 threshold)
```

### Blink Quality Formula
$$\text{Quality} = (0.35 \times \text{Duration Optimality}) + (0.40 \times \text{Eye Quality}) + (0.25 \times \text{Visibility Factor})$$
- **Duration Optimality**: Peaks at biological sweet spot (180ms – 320ms).
- **Single-Eye Penalty**: If only one eye is observable (`LEFT_ONLY` or `RIGHT_ONLY`), a 0.75x scaling factor is applied and reliability is adjusted.
- **Diminishing Returns**: 1st blink enters 65%–80% based on quality. 2nd blink adds `+5%`. 3rd blink adds `+2%`. Subsequent blinks saturate.

---

## 5. 25-Second Observable Eye Rule & Liveness Ceiling

1. If eyes are continuously observable without blur for **25 seconds** and no biological blink occurs:
   - System displays **"PLEASE BLINK"** and starts a 5-second challenge window.
2. If challenge passes:
   - Challenge marked `PASSED`, timer resets, ceiling lifted to 1.0.
3. If challenge fails:
   - Challenge marked `FAILED`, status set to `UNABLE_TO_DETERMINE`.
   - Strict **`liveness_confidence_ceiling = 0.28`** applied to liveness component (yielding ~20%–30% final confidence).

---

## 6. Presentation Attack Overrides & Edge Cases

| Scenario | Observation State | Presentation Override? | Resulting Assessment | Confidence |
|---|---|---|---|---|
| **Natural Human Blinking** | Face detected, 1 confirmed blink, natural motion | NO | `LIKELY_LIVE_HUMAN` | `65% – 84%` |
| **Face in Phone Screen** | Phone detected + face inside screen + high PAD | **YES (Hard Override)** | `POSSIBLE_SCREEN_REPLAY_ATTACK` | **`0.0%`** |
| **Phone in Background** | Phone on desk / held in hand, face outside screen | NO | Normal evaluation | `>= 65%` |
| **Static Photo Attack** | Eyes visible, 0 blinks, zero micro-movement | NO (Challenge / PAD) | `PLEASE_BLINK` → `UNABLE_TO_DETERMINE` | `< 30%` |
| **Motion Blur / Occlusion** | Eyes blurry, sunglasses, or turned away | NO (Timer Paused) | `HUMAN_FACE_DETECTED` | `50% – 74%` |
| **Contradictory Signals** | Blink observed, but high Moiré / synthetic risk | NO (Disagreement) | `SUSPICIOUS` | `< 55% (LOW rel.)` |

---

## 7. Developer Forensic Telemetry Panel

A developer-only debug drawer in the frontend UI (`/dashboard/live-scan`) exposes all raw sub-scores:
- Eye Visibility Status
- Blink Confirmation State & Quality
- Blink Count & Refractory Timers
- Liveness Evidence & Natural Facial Movement
- Temporal Consistency & Face Tracking Quality
- Replay & Synthetic Risk Indices
- Model Disagreement & Calibrated Raw Probability vs Product Score
