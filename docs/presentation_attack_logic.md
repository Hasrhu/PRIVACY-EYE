# Privacy Eye — Presentation Attack Detection & Screen-Target Association Logic

**Component**: Presentation Attack Detection (PAD) & Physical Surface Verification  
**Module**: Screen Detection, Bezel Analysis, and Screen-Face Spatial Association  

---

## 1. Problem Statement: Object Detection $\neq$ Presentation Attack

A naive anti-spoofing engine that flags an attack whenever a smartphone or monitor is detected in the video frame is fundamentally broken:
- A user sitting at an office desk legitimately has monitors and laptops in their background.
- A user may hold a smartphone in their hand or check a notification while on camera.
- In both situations, the target face observed by the webcam is a **living, breathing human**.

**Privacy Eye Rule**: An attack occurs **only** when the detected screen or photo is the **physical presentation medium** through which the face is being displayed to the camera lens.

---

## 2. Decision Tree & Architectural Flow

```text
                               CAMERA FRAME
                                    │
                  ┌─────────────────┴─────────────────┐
                  ▼                                   ▼
          YUNET FACE DETECTOR              SCREEN & DEVICE DETECTOR
                  │                                   │
              Face Box                          Device Box / Bezel
                  │                                   │
                  └─────────────────┬─────────────────┘
                                    │
                                    ▼
                     SCREEN-FACE ASSOCIATION ENGINE
                                    │
                    Is Face INSIDE Screen Polygon?
                                    │
                 ┌──────────────────┴──────────────────┐
                 │                                     │
                 ▼ NO                                  ▼ YES
          CASE A: PHONE IN SCENE                 Compute Presentation Evidence:
      - Person holding phone                     - Bezel edge continuity
      - Laptop in background                     - Moiré 2D FFT harmonics
      - TV on wall                               - Screen specular glare
                 │                               - Planar depth flatness
                 ▼                                     │
      Phone Detected: YES                              ▼
      Attack Suspected: NO               Presentation Confidence $\ge 0.75$?
      Human Confidence: UNMODIFIED                     │
                                         ┌─────────────┴─────────────┐
                                         │                           │
                                         ▼ YES                       ▼ NO
                                  CASE B: SCREEN ATTACK         INCONCLUSIVE
                               - Live Human Confidence: 0%    - Log warning
                               - Replay Risk: 1.0 (100%)      - Request active movement
                               - UI: POSSIBLE SCREEN REPLAY
```

---

## 3. Screen-Target Association Geometry

### 3.1 Intersection-over-Face ($\text{IoF}$) Metric
Let $B_{\text{face}} = [x_1, y_1, w_1, h_1]$ be the face bounding box and $B_{\text{screen}} = [x_2, y_2, w_2, h_2]$ be the screen bounding box.

$$\text{IoF} = \frac{\text{Area}(B_{\text{face}} \cap B_{\text{screen}})}{\text{Area}(B_{\text{face}})}$$

- **Condition for Association**:
  $$\text{IoF} \ge 0.85$$
  The target face must be almost completely enclosed within the bounds of the display bezel.

### 3.2 Boundary Margin Verification
A genuine screen replay exhibits dark bezel margins surrounding the face crop:
$$\text{Margin}_{\text{top}} = y_{\text{face}} - y_{\text{screen}} \ge 0.04 \times h_{\text{screen}}$$
$$\text{Margin}_{\text{bottom}} = (y_{\text{screen}} + h_{\text{screen}}) - (y_{\text{face}} + h_{\text{face}}) \ge 0.04 \times h_{\text{screen}}$$

---

## 4. Multi-Physical Presentation Signals

When $\text{IoF} \ge 0.85$, the engine confirms presentation using 4 orthogonal physical signals:

1. **High-Frequency 2D FFT Moiré Peaks**:
   Webcam sensors capturing active LCD/OLED subpixel grids produce spatial aliasing and periodic frequency spikes in the 2D Fourier power spectrum:
   $$\text{Moiré Ratio} = \frac{\sum_{(u,v) \in \text{High Freq}} |F(u,v)|^2}{\sum_{(u,v) \in \text{Low Freq}} |F(u,v)|^2}$$

2. **Specular Glass Glare & Flat Reflections**:
   Display glass reflects room ambient lighting uniformly across a flat planar surface, causing sharp local highlights ($\text{V} > 245$) with abrupt boundary gradients.

3. **Color Temperature / Gamma Discontinuity**:
   A backlit screen emits light with distinct white-point chromaticity ($D_{65}$) that differs measurably from the ambient background illumination outside the bezel.

4. **Absence of 3D Facial Parallax Depth**:
   When the camera or head moves, a real 3D face exhibits differential motion between the nose tip and ear contours:
   $$\Delta_{\text{3D Parallax}} = \|\vec{v}_{\text{nose}} - \vec{v}_{\text{eyes}}\| > \tau_{\text{3D}}$$
   A screen or photo is planar; all landmarks move in strict 2D affine lockstep ($\Delta_{\text{3D Parallax}} \approx 0$).

---

## 5. Confidence Override Rules

When confirmed presentation attack confidence exceeds threshold $\tau_{\text{attack}} = 0.75$:

```python
if screen_face_associated and presentation_attack_confidence >= 0.75:
    live_human_confidence = 0.0
    presentation_attack_risk = 1.0
    assessment = "POSSIBLE_REPLAY"
    reason_code = "PHONE_PRESENTATION_DETECTED"
    user_message = "A face appears to be displayed through a phone or screen."
```

### Safety & Wording Policy
- **Authorized terminology**:
  - `"POSSIBLE SCREEN/REPLAY PRESENTATION ATTACK"`
  - `"Face displayed through electronic screen"`
  - `"Physical replay medium detected"`
- **Prohibited terminology**:
  - Never display `"This person is fake"` or `"You are AI"`.
  - The human depicted in the video may be real, but the **camera is not observing them directly**.
