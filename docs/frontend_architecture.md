# Privacy Eye — Frontend Architecture Specification

## 1. Executive Summary & Vision

**Privacy Eye** is an enterprise-grade AI digital authenticity and deepfake detection platform. The frontend architecture is designed with **Apple-level polish, modern AI startup aesthetics, and cybersecurity command-center ergonomics**. 

Rather than adopting generic dashboard templates or neon hacker aesthetics, Privacy Eye leverages a **Dark Frosted Glass** design language:
- **Base Canvas:** Deep obsidian and navy tones (`#05070D`, `#080B12`, `#0D111C`) with subtle purple/blue radial ambient lights.
- **Surface Elevation:** Multi-layered frosted glass panels (`backdrop-blur-xl`, `rgba(255, 255, 255, 0.04-0.08)`, subtle border strokes `rgba(255, 255, 255, 0.08-0.14)`).
- **Accents:** Electric Blue (`#5EA7FF`) and Violet (`#9B7CFF`), with calibrated status indicators (Emerald Safe, Amber Suspicious, Crimson High Risk, Slate Undetermined).

---

## 2. Technical Stack

- **Framework:** Next.js 14.2.5 (App Router, React 18, TypeScript 5.5)
- **Styling Engine:** Tailwind CSS 3.4 with custom glassmorphism design tokens, CSS variables, and ambient lighting utilities
- **Motion & Micro-interactions:** Framer Motion 11.2 (spring physics, layout transitions, scan sweeps)
- **State Management:** Zustand 4.5 (modular stores for Live Scan, UI drawer state, and cached analysis)
- **Data Fetching:** Typed Axios client with interceptors, token refresh, and resilient error normalization
- **Visuals & Charts:** Recharts 2.12 & Lucide-React icons
- **Form & Uploads:** React Dropzone & React Hook Form

---

## 3. Directory & Component Architecture

```
frontend/
├── app/
│   ├── layout.tsx                  # Root layout, font loading (Inter, JetBrains Mono), Toast container
│   ├── page.tsx                    # Landing page ("SEE THROUGH THE FAKE.", Floating Glass Hero Engine)
│   ├── globals.css                 # Dark frosted glass tokens, ambient lighting, scan animations
│   ├── auth/
│   │   ├── login/page.tsx          # Frosted glass authentication card
│   │   └── register/page.tsx       # Account creation & organization registration
│   └── dashboard/
│       ├── layout.tsx              # Authenticated app shell with Floating Glass Navbar & persistent ambient glow
│       ├── page.tsx                # Central Command Center ("PROTECTION ACTIVE", Stats, Quick Scans, Feed)
│       ├── live-scan/page.tsx      # Dual-panel Live Camera HUD (Webcam, YuNet HUD, Guided Protocol, Benchmarks)
│       ├── analyze/page.tsx        # Drag-and-drop Media Analysis Studio (Image, Video, Audio)
│       ├── analyze/[id]/page.tsx   # Detailed Forensic Breakdown ("WHY?" explainability, signals, provenance)
│       ├── history/page.tsx        # Audit Trail & Analysis History (Filterable glass table, pagination)
│       ├── reports/page.tsx        # Security & Compliance Reports (Export JSON/PDF, audit hashes)
│       ├── privacy/page.tsx        # Privacy Center (Local vs Cloud, Data Retention, Consent Controls)
│       ├── security/page.tsx       # System & Model Health (Engine status, YuNet, Celeb-DF, Silent-Face)
│       ├── developer/page.tsx      # Developer API Keys & REST Endpoints Documentation
│       └── assistant/page.tsx      # Privacy Eye AI Security Analyst (Structured forensic Q&A)
├── components/
│   ├── layout/
│   │   ├── GlassNavbar.tsx         # Floating frosted glass navigation with badge counts & profile dropdown
│   │   ├── Footer.tsx              # Minimalist cybersecurity footer
│   │   └── AmbientBackground.tsx   # Radial ambient lighting mesh & subtle noise overlay
│   ├── ui/
│   │   ├── GlassCard.tsx           # Multi-elevation glass card (Base, Elevated, Floating Glow)
│   │   ├── GlassButton.tsx         # Primary Electric Blue, Secondary Glass, Ghost, Destructive
│   │   ├── GlassBadge.tsx          # Risk & Status pills with pulsing vitality dots
│   │   ├── GlassInput.tsx          # Form inputs with frosted backdrops and luminous focus rings
│   │   ├── GlassTabs.tsx           # Floating segment pills with Framer Motion layoutId springs
│   │   ├── GlassModal.tsx          # Backdrop blur modal dialogs
│   │   ├── ConfidenceRing.tsx      # SVG circular meter with calibrated gradient strokes
│   │   ├── SignalBar.tsx           # Calibrated telemetry progress bar with risk threshold markings
│   │   └── StatusIndicator.tsx     # Micro-pulse live status dot
│   ├── live/
│   │   ├── CameraFeed.tsx          # Video stream capture with Canvas overlay
│   │   ├── FaceMeshOverlay.tsx     # YuNet 5-point landmark indicators & dynamic bounding box
│   │   ├── GuidedProtocolHUD.tsx   # Smile, 3-Blinks, and Rotation step progression
│   │   └── BenchmarkCards.tsx      # Live cards for FaceForensics++, Celeb-DF, Silent-Face, FFHQ
│   └── analysis/
│       ├── DropzoneUpload.tsx      # Drag-and-drop media ingestion with file validation
│       ├── ScanningState.tsx       # Multi-stage forensic analysis scanner animation
│       └── SignalGrid.tsx          # Spatial, Temporal, Frequency, and Metadata signal matrices
├── lib/
│   ├── api.ts                      # Central Axios API client with all typed service endpoints
│   ├── store.ts                    # Zustand stores (liveSessionStore, uiStore)
│   └── utils.ts                    # Class merger, formatters, and forensic score calibrators
└── types/
    └── index.ts                    # Strict TypeScript definitions mirroring FastAPI schemas
```

---

## 4. State Management Separation

To prevent unnecessary re-renders when high-frequency live inference frames arrive, state is strictly partitioned into three distinct layers:

```
┌────────────────────────────────────────────────────────────────────────┐
│                          STATE ARCHITECTURE                            │
├───────────────────┬───────────────────────────┬────────────────────────┤
│     UI STATE      │       SERVER STATE        │  LIVE INFERENCE STATE  │
│  (Zustand / React)│  (Service Layer / SWR)    │ (Dedicated Frame Loop) │
├───────────────────┼───────────────────────────┼────────────────────────┤
│ • Active tabs     │ • Authenticated user profile│ • MediaStream track  │
│ • Modal visibilities│ • Dashboard statistics  │ • YuNet bounding box   │
│ • Drawer toggles  │ • Analysis history query  │ • 5-point landmarks    │
│ • Toast alerts    │ • Generated reports       │ • Instantaneous conf.  │
│ • Theme ambient   │ • Model health status     │ • Guided protocol state│
│   intensity       │ • API key list            │ • Frame processing ms  │
└───────────────────┴───────────────────────────┴────────────────────────┘
```

1. **Live Inference State:** Managed inside `useLiveScan` hook and `requestAnimationFrame` sampling. Changes to per-frame bounding boxes or micro-metrics mutate a dedicated canvas overlay and memoized HUD components without triggering full dashboard re-renders.
2. **Server State:** Handled through async service functions in `lib/api.ts` with manual or SWR-style cache invalidation upon create/delete mutations.
3. **UI State:** Handled via local `useState` or lightweight Zustand stores for global layout states (e.g., active navigation, notification trays).

---

## 5. Live Camera Pipeline Architecture

```
Webcam Capture (640x480 @ 30 FPS)
            │
            ▼
Frame Sampler (Throttled to 10-15 FPS via requestAnimationFrame)
            │
            ▼
Offscreen HTML5 Canvas (JPEG encoding @ 0.72 quality)
            │
            ▼
POST /api/v1/live/frame (Axios Payload: session_id, image_base64)
            │
            ▼
FastAPI Live Authenticity Engine
  ├── YuNet 5-point Landmark Detection
  ├── Quality Gating (Laplacian sharpness, lux, SNR)
  ├── Guided Protocol (Smile teeth/lips, 3-blinks, yaw/pitch rotation)
  ├── Ear Accessories (Over-ear / In-ear detection)
  └── Multi-Benchmark Inference:
        ├── FaceForensics++ (Boundary & compression seams)
        ├── Celeb-DF v2 (Ocular & oral synthesis artifacts)
        ├── Silent-Face Anti-Spoofing (Dual-scale Fourier replay PAD)
        └── FFHQ Baseline (High-frequency organic texture realism)
            │
            ▼
Client-Side Response Smoothing (Exponential Moving Average)
            │
            ▼
HUD Render:
  ├── Canvas: Smooth bounding box + Landmark ticks + Scan sweep
  ├── Metrics: Dynamic confidence, Liveness, Spatial Risk, Presentation Risk
  └── Guided Protocol: Real-time checkboxes with celebratory feedback
```

### Temporal Anti-Flicker Smoothing
To fulfill Section 15 & 17 requirement ("Do not flicker between REAL and FAKE"):
- The frontend computes an Exponential Moving Average (EMA) of confidence scores:
  $$\text{Score}_t = \alpha \cdot \text{Score}_{\text{new}} + (1 - \alpha) \cdot \text{Score}_{t-1} \quad (\alpha = 0.35)$$
- Result assessment labels transition through hysteresis bands rather than instantaneous binary jumps.

---

## 6. Authentication & Protected Routes

1. **Tokens:** JWT access tokens (1 day) and refresh tokens (7 days) are stored in secure cookies (`SameSite=Strict`, `Secure=true`).
2. **Auto-Refresh:** Axios response interceptor intercepts HTTP 401s, calls `/api/v1/auth/refresh`, updates cookies, and replays the failed request transparently.
3. **Protected Layout:** The `app/dashboard/layout.tsx` verifies token presence on mount and redirects unauthenticated users to `/auth/login`.

---

## 7. Responsive & Accessible Design System

- **Desktop (1024px+):** Dual-column layout for live scan (Left: 60% viewport camera canvas; Right: 40% telemetry and guided protocol panels).
- **Tablet (768px - 1023px):** Adaptive stacked layout with sticky telemetry controls.
- **Mobile (<768px):** Full-screen camera viewfinder with bottom floating glass control sheet and touch-accessible toggles.
- **Accessibility:**
  - Semantic HTML5 tags (`<main>`, `<nav>`, `<aside>`, `<section>`, `<article>`).
  - High-contrast text: `#F5F7FB` on dark surfaces satisfies WCAG 2.1 AA (contrast ratio > 12:1).
  - Reduced-motion queries disable heavy scanning loops and particle animations when preferred by the user.
