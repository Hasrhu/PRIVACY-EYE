# Privacy Eye — Blink & Anti-Spoofing Quantitative Evaluation Plan

**Component**: Quality Assurance, Model Benchmarking & Red-Team Testing  
**Standards**: ISO/IEC 30107-3 (Biometric Presentation Attack Detection Evaluation)  

---

## 1. Subsystem Evaluation Metrics

### 1.1 Eye Detector & Visibility Module
- **Precision & Recall** across `EYE_OPEN`, `EYE_CLOSED`, `EYE_BLURRY`, `EYE_OCCLUDED`.
- **Intersection-over-Union (IoU)** of eye orbit bounding box relative to manual ground-truth annotation (Target: $\text{IoU} \ge 0.82$).
- **Blurry Classification Accuracy**: True positive rate on synthetic motion-blurred frames.

### 1.2 Blink Detection Engine
- **Blink Event Precision**: $\frac{\text{True Blinks Detected}}{\text{Total Blink Events Flagged}}$ (Target: $\ge 95\%$).
- **Blink Event Recall**: $\frac{\text{True Blinks Detected}}{\text{Actual Physical Blinks}}$ (Target: $\ge 92\%$).
- **False Blink Rate (FBR)**: Spurious blinks generated during rapid head rotations, squinting, or speech (Target: $\le 2\%$).
- **Missed Blink Rate (MBR)**: Rapid micro-blinks ($< 120\text{ ms}$) failing detection threshold (Target: $\le 5\%$).

### 1.3 Phone & Presentation Attack Detector
- **Attack Presentation Classification Error Rate (APCER)**: Percentage of spoof attacks (phone replays, tablet videos, paper prints) falsely classified as live humans (Target: $\le 1.0\%$).
- **Bona Fide Presentation Classification Error Rate (BPCER)**: Percentage of legitimate live human presentations falsely flagged as spoof attacks (Target: $\le 1.5\%$).
- **Phone In Scene False Positive Rate**: Rate at which a person holding a phone beside their body is falsely classified as a presentation attack (Target: $\le 0.5\%$).

---

## 2. End-to-End System Benchmark Targets

| Metric | Target SLA | Benchmark Method |
|---|---|---|
| **End-to-End Inference Latency** | $\le 45\text{ ms}$ / frame | WebRTC 30 FPS client stream on standard CPU |
| **Abstention Rate (`UNABLE_TO_DETERMINE`)** | $4.0\% - 8.0\%$ | Extreme edge cases, failed 25s challenges |
| **Blink Challenge Verification Accuracy** | $\ge 98.2\%$ | Interactive 5-second window response verification |
| **Expected Calibration Error (ECE)** | $\le 0.04$ | Binned reliability diagram over 10,000 test frames |
| **Memory Footprint** | $\le 280\text{ MB}$ RSS | Sustained 10-minute continuous camera tracking |

---

## 3. Red-Team Adversarial Scenarios

The test harness evaluates 8 adversarial spoofing paradigms:

1. **4K OLED Smartphone Video Replay**: iPhone 15 Pro displaying 60 FPS face recording directly facing webcam.
2. **Laptop Monitor Video Replay**: MacBook Liquid Retina display playing deepfake video.
3. **High-Res Matte Paper Printout**: Printed face cutout with eye holes cut out.
4. **Static Tablet Display**: iPad displaying still photograph under warm incandescent lighting.
5. **Legitimate User with Phone in Hand**: Real human speaking while holding phone below chest.
6. **25-Second Prolonged Stare**: Real human consciously withholding blinking for 30 seconds.
7. **Severe Motion & Dark Lighting**: User pacing in dark room (< 10 lux) causing motion blur.
8. **Heavy Sunglasses**: Polarized mirrored sunglasses covering eye orbits entirely.
