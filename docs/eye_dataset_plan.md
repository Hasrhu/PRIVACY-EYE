# Privacy Eye — Eye & Blink Dataset Architecture & Training Plan

**Component**: Computer Vision & Ocular Biometric Model Training  
**Objective**: Robust Eye Visibility, Occlusion Classification, and Blink State Estimation  

---

## 1. Class Taxonomy

The ocular ML classifier is trained across 6 discrete ocular states:

```text
1. EYE_OPEN              (Sclera visible on both sides of iris; palpebral fissure normal)
2. EYE_CLOSED            (Eyelids fully apposed; eyelash line horizontal/curved; no iris visible)
3. EYE_PARTIALLY_VISIBLE (Ptosis, partial blink transit, squinting, or asymmetric closure)
4. EYE_OCCLUDED          (Obstruction by hair strands, heavy frames, fingers, or sunglasses)
5. EYE_BLURRY            (Motion blur or defocus exceeding 2.5px point spread function)
6. EYE_OUT_OF_FRAME      (Eye orbit intersects frame perimeter or extreme profile yaw > 45°)
```

---

## 2. Demographic & Optical Environmental Diversity

Training datasets are strictly curated to avoid confounding illumination with eyelid closure:

| Dimension | Variations Curated | Anti-Bias Safeguard |
|---|---|---|
| **Facial & Orbital Anatomy** | Epicanthic folds, deep-set eyes, hooded lids, varied palpebral widths | Prevents false "closed" classifications on narrow eyes |
| **Eyewear & Accessories** | Wire frames, thick acetate frames, anti-glare coatings, sunglasses | Network learns frame boundaries vs anatomical eyelids |
| **Lighting Conditions** | Low lux (< 20 lux), direct backlighting, side lighting, screen glare | Penalizes loss function if dark images predict `EYE_CLOSED` |
| **Camera & Sensor Quality** | 480p laptop webcams, 1080p webcams, mobile front cameras, lens dust | Prevents sensor noise from triggering fake or closed labels |
| **Gaze & Head Poses** | Looking down (reading), looking sideways, yaw up to $\pm 45^\circ$, pitch $\pm 30^\circ$| Downward gaze distinguished from bona fide blink |

---

## 3. Temporal Blink Clips Dataset

Temporal sequence training pairs 8-frame clips (sampled at 30 FPS):

1. **Bona Fide Blink Sequences**:
   `OPEN` (frames 1-2) $\rightarrow$ `CLOSING` (frame 3) $\rightarrow$ `CLOSED` (frames 4-5) $\rightarrow$ `REOPENING` (frame 6) $\rightarrow$ `OPEN` (frames 7-8).
2. **Prolonged Eye Closure (Sleep / Fatigue)**:
   `CLOSED` sustained for $> 25$ frames (flagged as closure, not a blink event).
3. **Hard Negative Glitches**:
   - Tracking jitter: face detection box jumps 1 frame.
   - Saccade / down-gaze: user glances down at keyboard (pupil moves downward; upper lid lowers partially but doesn't seal).
   - Motion blur: rapid head turn causing 2 blurred frames (classified as `EYE_BLURRY`, rejected from blink count).
