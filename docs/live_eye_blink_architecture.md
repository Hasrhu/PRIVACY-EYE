# Privacy Eye — Live Eye, Blink, Visibility & Confidence Architecture

**Version**: 2.0.0-PROD  
**Component**: Live Camera Authenticity & Anti-Spoofing Pipeline  
**Module**: Eye Tracking, Blink State Machine, Screen Detection & Uncertainty-Aware Calibration  

---

## 1. System Philosophy & Core Tenets

1. **Uncertainty-Aware & Evidence-Based**: The system never claims absolute authenticity (100% real) or definitive falsehood. Every result is an aggregation of multi-spectral biometric, spatial, temporal, and physical signals with explicit confidence intervals.
2. **Never Single-Signal Dependent**: Blinking alone is **never** proof of humanity, and the absence of blinking is **never** proof of an AI deepfake. Legitimate humans stare, blink rapidly, wear glasses, or turn away.
3. **Observation-Qualified Timers**: Timers (such as the 25-second no-blink window) accumulate time **only** when eyes are observable with sufficient resolution, lighting, and stability. When eyes are blurry, occluded, or turned sideways, the timer pauses.
4. **Physical Presentation Attack Priority**: When a screen (smartphone, tablet, laptop, or monitor) is identified as the physical surface displaying the target face, direct human observation confidence is overridden to 0%, because the camera is observing a screen display, not a living person.

---

## 2. Global Live Camera State Taxonomy

The engine transitions between 18 distinct, mutually exclusive primary states:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        LIVE CAMERA STATE TAXONOMY                      │
├──────────────────────────┬─────────────────────────────────────────────┤
│ State                    │ Description & Trigger Criteria              │
├──────────────────────────┼─────────────────────────────────────────────┤
│ INITIALIZING             │ Video stream establishing; buffer warming up│
│ CAMERA_PERMISSION_REQUIRED│ WebRTC camera permission prompt pending     │
│ NO_FACE                  │ No facial contour identified in viewport    │
│ FACE_DETECTED            │ Face acquired; spatial tracking active      │
│ MULTIPLE_FACES           │ Multiple faces present; requires target lock│
│ LOW_QUALITY              │ Severe blur, dark lighting, or sensor noise │
│ EYES_NOT_VISIBLE         │ Face detected but eyes blurry or occluded   │
│ EYES_VISIBLE             │ Both eyes clearly localized and measurable  │
│ BLINK_TRACKING           │ Eyes visible; temporal blink machine active │
│ PHONE_DETECTED           │ Mobile/tablet device detected in scene      │
│ SCREEN_REPLAY_SUSPECTED  │ Target face enclosed within display bezel   │
│ PHOTO_REPLAY_SUSPECTED   │ Static planar photo printout identified     │
│ LIVENESS_ANALYSIS        │ 3D parallax & physiological micro-motion    │
│ ANALYZING                │ Fusing multi-frame temporal evidence        │
│ LIKELY_LIVE_HUMAN        │ Calibrated bona fide human face verified    │
│ SUSPICIOUS               │ Anomalous spatial or temporal indicators    │
│ HIGH_SYNTHETIC_RISK      │ Neural synthesis / boundary artifacts found │
│ POSSIBLE_REPLAY          │ Screen / video / photo replay confirmed     │
│ UNABLE_TO_DETERMINE      │ Inconclusive evidence / failed challenge    │
│ ERROR                    │ Stream, decode, or inference pipeline error │
└──────────────────────────┴─────────────────────────────────────────────┘
```

---

## 3. High-Level Pipeline Architecture

```text
                            CAMERA FRAME (Base64 JPEG)
                                        │
                                        ▼
                         OpenCV Frame Decode & Quality Check
                                        │
                ┌───────────────────────┴───────────────────────┐
                ▼                                               ▼
     YuNet Face & 5-Landmarks                      Screen & Object Detector
                │                                 (Phone, Tablet, Laptop, Screen)
                │                                               │
                │                                               ▼
                │                                  Screen-Face Association Engine
                │                                  (Is face INSIDE display bezel?)
                │                                               │
                ├───────────────────────────────────────────────┘
                ▼
     Dedicated EyeAnalyzer
        ├── Eye Crop & Sharpness Check
        ├── Visibility State Classification (BOTH_VISIBLE, BLURRY, OCCLUDED)
        └── Quality Scoring (0.0 - 1.0)
                │
                ▼
     Blink State Machine & Timer
        ├── EAR & Vertical Energy Curve
        ├── State: OPEN → CLOSING → CLOSED → OPEN → CONFIRMED
        ├── Continuous Visibility Accumulator (Paused when blurry/occluded)
        └── 25s Observation Window → Active "PLEASE BLINK" Challenge
                │
                ▼
     Multi-Benchmark Forensic Fusion
        ├── FaceForensics++ (Boundary & Chroma)
        ├── Celeb-DF v2 (Ocular HF energy)
        ├── Silent-Face PAD (Dual-Scale Fourier Moiré)
        └── FFHQ Texture Policy (Micro-pore realism)
                │
                ▼
     Calibrated Risk & Confidence Engine
        ├── Phone Presentation Override (If face inside screen → 0% human confidence)
        ├── Eye Unavailable Compensation (Fallback to spatial/temporal signals)
        ├── Blink Challenge Penalty (Liveness confidence ceiling = 20-30%)
        ├── Exponential Moving Average (EMA temporal smoothing)
        └── Machine-Readable Reason Codes
                │
                ▼
     Frontend Glassmorphism UI (Dashboard Live-Scan)
```

---

## 4. Subsystem Specifications

### 4.1 Eye Landmark & Visibility Engine (`app/ml/eye_analyzer.py`)
- **Interocular Distance (IOD)**: Calibrated distance between pupils $\text{IOD} = \|p_{\text{left}} - p_{\text{right}}\|_2$.
- **Dynamic Eye Orbits**: Bounding box for left and right eyes sized proportional to $\text{IOD}$ ($0.32 \times \text{IOD}$ width, $0.24 \times \text{IOD}$ height).
- **Sharpness & Contrast**: Laplacian variance ($\sigma_{\text{lap}}^2$) of grayscale eye patch.
- **Occlusion & Sunglasses**: Histogram luminance distribution across orbit; dark uniform absorption without pupil-sclera gradient flags `EYES_OBSCURED`.
- **Visibility States**:
  - `BOTH_EYES_VISIBLE`: Quality $\ge 0.50$ on both eyes.
  - `LEFT_ONLY` / `RIGHT_ONLY`: Yaw or obstruction hides contralateral eye.
  - `EYES_TOO_BLURRY`: Motion blur or low camera resolution prevents edge resolution. Eye signal marked `UNAVAILABLE`.
  - `EYES_NOT_VISIBLE`: Complete occlusion or extreme angle.

### 4.2 Blink State Machine & Timer Engine (`app/ml/blink_engine.py`)
- **Biological Constraint**: Valid human blinks last between **80 ms and 700 ms**.
- **Refractory Period**: Minimum 300 ms separation between consecutive blink events.
- **Observation Qualification**: The no-blink timer increments **only** if:
  $$\text{eyes\_visible} = \text{True} \quad \wedge \quad \text{eye\_quality} \ge 0.40 \quad \wedge \quad \text{face\_stable} = \text{True}$$
  If eyes are blurry or hidden, the timer freezes.
- **25-Second Threshold**: Triggers interactive countdown challenge modal in UI without declaring the user fake.

### 4.3 Screen & Phone Presentation Engine (`app/ml/screen_detector.py`)
- Identifies rectangular device displays, bezel edges, Moiré frequency spikes, and specular glare.
- Computes Intersection-over-Face ($\text{IoF}$) between the detected screen polygon and the face bounding box.
- Differentiates a phone held in hand vs. a face rendered on a screen.

---

## 5. Privacy & Edge Computing Guarantee

- Camera frames are processed strictly in-memory.
- No continuous video streams or raw eye crops are stored on disk or sent to third-party endpoints.
- All biometric landmarks are transient session objects destroyed upon session termination.
