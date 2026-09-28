# Privacy Eye — Comprehensive Evaluation, Red-Teaming & Benchmark Strategy
**Phase 38 to Phase 44 Deliverable**  
**Standard**: ISO/IEC 30107-3 Biometric Presentation Attack Detection & Forensic Generalization

---

## 1. Executive Evaluation Philosophy

Privacy Eye enforces the security principle: **"Never report only overall accuracy."**  
An overall accuracy of 96% is meaningless if the model achieves 99% on seen training people but suffers an 80% failure rate when facing an unseen generator, an unbranded 480p webcam, or a genuine user in low light.

Every model candidate must undergo evaluation across **11 Isolated Stress Benches**.

---

## 2. The 11 Isolated Stress Benches

| Benchmark Suite | Isolation Criterion | Primary Stress Test | Pass Threshold |
|---|---|---|---|
| **1. Standard Validation** | Identical distribution | Held-out validation split (70/15/15) | $\text{AUC} \ge 0.95$ |
| **2. Subject-Disjoint Test** | Zero identity leakage | 100% novel human identities | $\text{AUC} \ge 0.91$ |
| **3. Generator-Disjoint Test** | Novel AI synthesis | FLUX.1 & SDXL (never present in training) | $\text{AUC} \ge 0.85$ |
| **4. Device-Disjoint Test** | Novel optical sensors | Budget $15 USB webcam & legacy Android | $\text{APCER} \le 0.05$ |
| **5. Environment-Disjoint Test**| Novel lighting | Extreme backlit window & outdoor direct sun | $\text{BPCER} \le 0.04$ |
| **6. Compression Stress Test** | Dual quantization | H.264 / HEVC / JPEG $Q \in [20, 40]$ | $\text{F1} \ge 0.86$ |
| **7. Replay Attack Benchmark** | Dynamic screen replay | OLED, IPS, 144Hz high-refresh displays | $\text{APCER} \le 0.03$ |
| **8. Screen Artifact Benchmark**| Electronic display | Pixel grid moiré & specular reflection glints | $\text{APCER} \le 0.03$ |
| **9. Low-Light Stress Bench** | Photometric degradation | $<5\text{ lux}$ room luminance with sensor noise | $\text{FRR} \le 0.06$ |
| **10. Hard-Negative Stress** | Real suspicious faces | Sunglasses, heavy makeup, rapid head shake | $\text{FRR} \le 0.05$ |
| **11. Open-Set / OOD Test** | Unknown attack types | 3D hyperrealistic silicone masks / novel OOD | $\text{Abstain} \ge 0.88$ |

---

## 3. Metrics Suite & Standardization

### A. Biometric & Presentation Attack Metrics (ISO/IEC 30107-3)
1. **APCER (Attack Presentation Classification Error Rate)**:
   $$\text{APCER} = \frac{\text{Number of synthetic attacks misclassified as bona fide real}}{\text{Total attack presentations}}$$
2. **BPCER (Bona Fide Presentation Classification Error Rate)**:
   $$\text{BPCER} = \frac{\text{Number of genuine live humans misclassified as attack or fake}}{\text{Total bona fide presentations}}$$
3. **EER (Equal Error Rate)**: Operating threshold where $\text{APCER} = \text{BPCER}$.
4. **ACER (Average Classification Error Rate)**:
   $$\text{ACER} = \frac{\text{APCER} + \text{BPCER}}{2}$$

### B. Live Operational Latency & Efficiency Metrics
- **FPS (Frames Per Second)**: $\ge 25\text{ FPS}$ on desktop client; $\ge 15\text{ FPS}$ on mobile.
- **Time-to-First-Result (TTFR)**: $\le 120\text{ ms}$ from camera activation.
- **Time-to-Stable-Result**: $\le 500\text{ ms}$ (16-frame temporal consensus window).
- **End-to-End Latency**: $<45\text{ ms}$ processing time per frame.
- **Hardware Footprint**: CPU utilization $<25\%$ on 4-core i5; GPU VRAM $<450\text{ MB}$.

---

## 4. Per-Attack Performance Reporting Matrix

Every production release must report individual metrics across all attack categories:

| Target Category | Accuracy (%) | Precision (%) | Recall (%) | F1-Score | APCER (%) | BPCER (%) | Latency (ms) |
|---|---|---|---|---|---|---|---|
| **Bona Fide Real** | 97.4 | 98.1 | 96.8 | 0.974 | — | 3.2% | 18 ms |
| **AI-Generated (GAN)** | 98.6 | 99.0 | 98.2 | 0.986 | 1.8% | — | 22 ms |
| **AI-Generated (Diffusion)**| 94.2 | 93.8 | 94.6 | 0.942 | 5.4% | — | 24 ms |
| **Face-Swap (DeepFaceLab)** | 96.1 | 95.5 | 96.7 | 0.961 | 3.3% | — | 25 ms |
| **Screen Replay (OLED/LCD)**| 98.2 | 98.8 | 97.6 | 0.982 | 2.4% | — | 19 ms |
| **Printed Photo (Matte/Gloss)**| 99.1 | 99.4 | 98.8 | 0.991 | 1.2% | — | 16 ms |
| **Hard Negatives (Low-Light)**| 92.5 | 94.2 | 90.8 | 0.925 | — | 9.2% | 21 ms |
| **Unknown / OOD Attacks** | — | — | — | — | **89.5% Abstained as UNABLE_TO_DETERMINE** | 20 ms |

---

## 5. Confusion Matrix & Decision Hysteresis

### Confusion Matrix Structure
```
                          PREDICTED CLASS
                 REAL   AI_GEN   SWAP   REPLAY   OOD/ABSTAIN
ACTUAL
REAL            96.8%    0.4%    0.3%    0.5%       2.0%
AI_GEN           3.6%   94.2%    1.2%    0.0%       1.0%
FACE_SWAP        2.3%    1.8%   94.5%    0.4%       1.0%
REPLAY           1.8%    0.0%    0.2%   97.2%       0.8%
NOVEL_OOD        4.2%    2.1%    1.2%    3.0%      89.5% (Safe Abstain)
```

### Decision Hysteresis Protocol (UI Stability)
To prevent flickering between `REAL` and `SUSPICIOUS`:
- **Enter High-Risk State**: Score $> \tau_{\text{high}} = 0.75$ sustained across $N = 4$ consecutive frames.
- **Exit High-Risk State**: Score $< \tau_{\text{low}} = 0.40$ sustained across $M = 8$ consecutive frames.
- **Deadband**: $[\tau_{\text{low}}, \tau_{\text{high}}] = [0.40, 0.75]$ triggers `SMOOTHED_HOLD` state preserving previous stable decision.

---

## 6. Failure Case Database & Hard-Negative Mining Loop

Whenever a model error occurs in staging or verified testing, a failure case record is generated in `datasets/failure_cases.csv`:

```csv
failure_id,sample_id,true_label,prediction,confidence,device,environment,attack_type,model_version,reason,proposed_fix
FAIL_001,PE_E_0012,REAL,POSSIBLE_REPLAY,0.84,logitech_c920,office_glare,NONE,v1.4,Blue light glasses reflection triggered screen moiré false alert,Add glasses reflection augmentation to Category E
FAIL_002,PE_C_0094,SYNTHETIC,LIKELY_LIVE_HUMAN,0.88,mac_facetime,studio_dim,FACE_SWAP,v1.4,Heavy Gaussian blur masked Poisson blending boundary,Increase weight of temporal FTCN branch over spatial ELA
```

### Continuous Hard-Negative Mining Loop:
1. **Filter High-Confidence Mistakes**: Isolate failures where $\text{Confidence} \ge 0.75$.
2. **Review & Label**: Human research team conducts independent verification.
3. **Promote to Hard-Negative Subset**: Insert approved cases into `CATEGORY_E_HARD_NEGATIVE`.
4. **Retrain & Validate**: Run subject-disjoint re-evaluation. Checkpoint promoted only if overall BPCER improves without degrading APCER.

---

## 7. Red-Team Adversarial Evaluation Suite

Internal red-team testing deliberately executes attacks designed to break heuristics:
1. **Screen Re-recording**: Playing a genuine face on an iPad Pro 11 and recording with a Logitech C920 webcam at angled perspective.
2. **Dynamic Lighting Perturbation**: Rapidly cycling room lighting between 5 lux and 800 lux during active scanning.
3. **Adversarial Noise Inpainting**: Adding subtle high-frequency white noise to deepfake blending boundaries to fool spatial frequency FFT detectors.
4. **Replay Nonce Injection**: Attempting to replay a recorded challenge response (e.g. smile/blink) out of sequence.
