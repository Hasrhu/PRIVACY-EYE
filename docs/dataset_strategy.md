# Privacy Eye — Enterprise Dataset Strategy & Governance Architecture
**Phase 3 to Phase 13 Deliverable**  
**Standard**: Leakage-Resistant, Subject-Disjoint, Generator-Generalizing, and Ethically Compliant

---

## 1. Executive Dataset Architecture

The Privacy Eye dataset system is engineered around a core tenet: **"Models fail when benchmark data leaks identity or when models conflate camera degradation with synthetic generation."**

```
┌────────────────────────────────────────────────────────────────────────┐
│                      PRIVACY EYE DATASET ENGINE                        │
└───────────────────────────────────┬────────────────────────────────────┘
         ┌──────────────────┬───────┴──────────┬──────────────────┐
         ▼                  ▼                  ▼                  ▼
   ┌───────────┐      ┌───────────┐      ┌───────────┐      ┌───────────┐
   │CATEGORY A │      │CATEGORY B │      │CATEGORY C │      │CATEGORY D │
   │  Genuine  │      │Synthetic  │      │Face-Swap  │      │ Replay &  │
   │Live Human │      │ AI Faces  │      │ Deepfakes │      │PAD Spoof  │
   └───────────┘      └───────────┘      └───────────┘      └───────────┘
                                   │
                                   ▼
                             ┌───────────┐
                             │CATEGORY E │
                             │   Hard    │
                             │ Negatives │
                             └───────────┘
```

---

## 2. The Five Foundational Categories

### Category A: Genuine Live Human Data
- **Objective**: Establish the bona fide biological baseline across wide real-world variance.
- **Visual Diversity Targets**:
  - Headwear: Hats, beanies, caps, religious coverings.
  - Optical Accessories: Prescriptive glasses, anti-reflective coatings, sunglasses.
  - Facial Features: Varied facial hair density, beard lengths, hairstyles.
  - Poses & Distances: Pitch $[-25^\circ, +25^\circ]$, Yaw $[-45^\circ, +45^\circ]$, Roll $[-15^\circ, +15^\circ]$; distance $30\text{ cm}$ to $2.0\text{ m}$.
- **Ethical Safeguard**: **Zero demographic profiling**. No demographic labels (race, ethnicity, gender, sexual orientation, emotion) are inferred or stored. Visual diversity targets rendering physics, not social classifications.
- **Sensors & Hardware**:
  - Laptop webcams: Built-in 720p/1080p (MacBook, Dell XPS, ThinkPad).
  - Mobile cameras: iOS (iPhone 11–15 Pro), Android (Samsung S-series, Pixel, budget MediaTek devices).
  - Standalone USB webcams: Logitech C920/Brio, unbranded $15 generic webcams.
- **Environmental Illuminations**:
  - Bright diffuse daylight ($>500\text{ lux}$), dim evening lighting ($15–40\text{ lux}$), strong window backlight, side-lamp glare, mixed warm/cool fluorescent.
- **Resolutions & Frame Rates**: $360\text{p}$, $480\text{p}$, $720\text{p}$, $1080\text{p}$ at $15$, $24$, $30$, and $60\text{ FPS}$.

### Category B: AI-Generated Faces (Pure Synthetic)
- **Objective**: Expose the model to diverse generative representations without overfitting to one engine.
- **Generative Families**:
  - Generative Adversarial Networks (GANs): StyleGAN1, StyleGAN2-ADA, StyleGAN3, ProGAN.
  - Latent Diffusion Models: Stable Diffusion v1.5, SDXL, SDXL-Turbo.
  - High-Fidelity Autoregressive / Flow Matching: Midjourney v5/v6, FLUX.1-dev.
- **Generalization Protocol (Generator-Disjoint)**:
  - $\mathcal{G}_{\text{train}} = \{\text{StyleGAN2}, \text{ProGAN}, \text{Stable Diffusion v1.5}\}$
  - $\mathcal{G}_{\text{test-unseen}} = \{\text{FLUX.1}, \text{SDXL}, \text{Midjourney v6}\}$
  - The model is scored on its ability to detect generators it has never seen during training.

### Category C: Face-Swap & Deepfakes
- **Objective**: Detect facial boundary seams, color inconsistencies, and warp blending.
- **Techniques Covered**:
  - DeepFakes (DeepFaceLab autoencoder swap).
  - Face2Face (RGB facial reenactment).
  - FaceSwap (Graphics-based 3D landmark mesh replacement).
  - NeuralTextures (Neural rendering with neural texture maps).
  - FaceShifter (High-fidelity occlusion-aware face swapping).
- **Benchmark Source Repositories**:
  - FaceForensics++ (c23 / c40 compression tiers).
  - Celeb-DF v2 (Challenging forensic benchmark).

### Category D: Replay & Presentation Attack (PAD)
- **Objective**: Live camera physical spoof resistance.
- **Attack Modalities**:
  - **Photo Attacks**: Matte photo, glossy photo, curved/folded printout, cutout eye holes.
  - **Screen Replay Attacks**: Smartphone (AMOLED), tablet (IPS), laptop LCD, high-refresh desktop gaming monitor (144Hz). Capture moiré patterns, screen borders, reflection glints, scan lines.
  - **Replay Video Playback**: Prerecorded genuine user video held in front of the camera.
  - **3D Mask Attacks**: Silicone mask, resin mask, paper mask (benchmarked via CASIA-SURF research protocol).

### Category E: Real Human Hard Negatives
- **Objective**: Break the toxic false heuristic: $\text{Low Quality} \neq \text{Fake}$.
- **Scenarios Included**:
  - Severe low light ($<5\text{ lux}$) with webcam sensor noise.
  - Harsh backlighting causing silhouette / underexposure.
  - Rapid head turn causing severe motion blur.
  - Lens smudge / poor autofocus.
  - Heavy theatrical makeup, intense eye shadow.
  - Blue light screen reflection in glasses.
  - Mirror reflections and video conferencing preview windows.

---

## 3. Controlled Paired Internal Test Corpus

To measure precision against identical facial identities, Privacy Eye generates paired recording suites:

| Identity Key | Bona Fide Recording | Paired Stress / Replay Variant | Paired Manipulation Variant |
|---|---|---|---|
| `PERSON_001` | `001_REAL_NORMAL` | `001_REAL_LOW_LIGHT` | `001_DEEPFAKE_SWAP` |
| `PERSON_001` | `001_REAL_NORMAL` | `001_REAL_BACKLIGHT` | `001_REENACT_F2F` |
| `PERSON_001` | `001_REAL_NORMAL` | `001_REAL_GLASSES` | `001_SYNTH_DIFFUSION` |
| `PERSON_001` | `001_REAL_NORMAL` | `001_REPLAY_PHONE` | `001_REPLAY_MONITOR` |
| `PERSON_001` | `001_REAL_NORMAL` | `001_PHOTO_MATTE` | `001_PHOTO_GLOSSY` |

---

## 4. Subject-Disjoint & Leakage Prevention Strategy

### Absolute Partitioning Constraint
Let $\mathcal{S}$ be the set of unique human identities across the entire dataset.
$$\mathcal{S}_{\text{train}} \cap \mathcal{S}_{\text{val}} = \emptyset, \quad \mathcal{S}_{\text{train}} \cap \mathcal{S}_{\text{test}} = \emptyset, \quad \mathcal{S}_{\text{val}} \cap \mathcal{S}_{\text{test}} = \emptyset$$

- **Split Ratio**: $70\%$ Train, $15\%$ Validation, $15\%$ Test.
- **Video Disjoint Rule**: Frame extraction **never** precedes dataset splitting. Videos are assigned to splits as indivisible atomic units. Nearby frames from the same 10-second clip can never bridge train and test sets.

---

## 5. Dataset Manifest Schema (`datasets/manifest.csv`)

Every dataset sample is tracked with 16 immutable metadata fields:

```csv
sample_id,subject_id,source_video_id,dataset,label,attack_type,generator,camera,resolution,fps,environment,compression,license,consent_status,split
PE_A_0001,subj_012,vid_012_01,InternalConsented,REAL,NONE,NONE,mac_facetime_720p,720p,30,office_bright,h264_q20,InternalConsent-v1,True,train
PE_B_0042,None,None,GenImage,SYNTHETIC,NONE,FLUX_1,virtual_render,1024p,None,synthetic_studio,lossless_png,ResearchTerms,True,test_unseen_generator
PE_C_0189,subj_ff_44,vid_44_swap,FaceForensics++,SYNTHETIC,FACE_SWAP,FaceShifter,broadcast_cam,720p,30,studio,c23,FaceForensicsResearch,True,val
PE_D_0312,subj_004,vid_004_replay,InternalPAD,PRESENTATION_ATTACK,SCREEN_REPLAY,NONE,iphone_13,1080p,60,bedroom_dim,h264_q28,InternalConsent-v1,True,test_unseen_device
PE_E_0088,subj_091,vid_091_dark,InternalHardNeg,REAL,NONE,NONE,budget_usb_cam,480p,15,extreme_low_light,raw_yuy2,InternalConsent-v1,True,train
```

---

## 6. Public Dataset Licensing Matrix & Commercial Policies

| Dataset | Research Terms | Commercial Deployment Policy | Privacy Eye Compliance Status |
|---|---|---|---|
| **FaceForensics++** | FaceForensics Terms (MIT Code) | Prohibited for commercial weights distribution | **Evaluated on isolated benchmark server only** |
| **Celeb-DF v2** | Non-Commercial Research Only | Strictly research benchmarking | **Evaluated on isolated benchmark server only** |
| **CASIA-SURF** | CASIA Agreement (Research Only) | Academic PAD reference | **Reference baseline only** |
| **ASVspoof 2021** | Open Data Commons (ODC-By) | Permitted with attribution | **Compliant** |
| **NVIDIA FFHQ** | CC BY-NC-SA 4.0 | Non-commercial; no facial recognition | **Texture baseline only; excluded from model training** |
| **Internal Consented Corpus** | Privacy Eye Contributor License | **100% Fully Cleared for Commercial Deployment** | **Primary training corpus** |
