# Privacy Eye — UI Design System Specification

## 1. Design Vision & Philosophy

The Privacy Eye UI transforms the structural elegance of modern high-end SaaS (floating cards, generous whitespace, rounded geometry, layered depth) into a **Dark Frosted Glass + AI Cybersecurity** interface.

### Key Visual Tenets:
1. **Apple-Level Polish:** Tactile blur filters, subtle 1px border strokes with directional lighting highlights, and balanced internal padding.
2. **Authenticity & Forensics:** Technical data (YuNet landmarks, Fourier frequencies, Celeb-DF residuals) presented with clarity and calm authority rather than aggressive gaming or hacker visuals.
3. **Layered Depth:** Multi-tiered elevation created through varying opacities, backdrop blur intensities, and low-frequency ambient shadows.

---

## 2. Color Palette & Design Tokens

### 2.1 Surfaces & Backgrounds
```css
:root {
  /* Canvas Backgrounds */
  --bg-canvas: #05070D;       /* Deepest obsidian navy */
  --bg-surface: #080B12;      /* Elevated section background */
  --bg-card: #0D111C;         /* Solid card fallback */
  --bg-card-hover: #121826;

  /* Frosted Glass Layers */
  --glass-base: rgba(255, 255, 255, 0.035);
  --glass-elevated: rgba(255, 255, 255, 0.06);
  --glass-floating: rgba(255, 255, 255, 0.09);

  /* Border Strokes */
  --border-glass-subtle: rgba(255, 255, 255, 0.06);
  --border-glass-medium: rgba(255, 255, 255, 0.12);
  --border-glass-strong: rgba(255, 255, 255, 0.18);
  --border-glass-accent: rgba(94, 167, 255, 0.35);

  /* Text & Typography */
  --text-primary: #F5F7FB;
  --text-secondary: rgba(245, 247, 251, 0.65);
  --text-tertiary: rgba(245, 247, 251, 0.40);
  --text-accent: #5EA7FF;
}
```

### 2.2 Brand & Cybersecurity Accents
```css
:root {
  /* Primary Accents */
  --accent-blue: #5EA7FF;           /* Electric Blue */
  --accent-blue-glow: rgba(94, 167, 255, 0.22);
  --accent-violet: #9B7CFF;         /* Cyber Violet */
  --accent-violet-glow: rgba(155, 124, 255, 0.20);
  --accent-cyan: #38BDF8;

  /* Calibrated Forensic Status Colors */
  --status-safe: #4ADE80;           /* Emerald (Likely Live / Safe) */
  --status-safe-bg: rgba(74, 222, 128, 0.10);
  --status-safe-border: rgba(74, 222, 128, 0.25);

  --status-warning: #FBBF24;        /* Amber (Suspicious / Uncertain) */
  --status-warning-bg: rgba(251, 191, 36, 0.10);
  --status-warning-border: rgba(251, 191, 36, 0.25);

  --status-danger: #FB7185;         /* Coral / Crimson (High Synthetic Risk) */
  --status-danger-bg: rgba(251, 113, 133, 0.10);
  --status-danger-border: rgba(251, 113, 133, 0.25);

  --status-undetermined: #94A3B8;   /* Slate Gray */
  --status-undetermined-bg: rgba(148, 163, 184, 0.10);
  --status-undetermined-border: rgba(148, 163, 184, 0.20);
}
```

---

## 3. Typography Scale & Hierarchy

- **Primary Typeface:** `Inter`, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif
- **Data & Telemetry:** `JetBrains Mono`, monospace (used for SHA-256 hashes, latency metrics, and percentages)

| Element | Class / Token | Size | Weight | Tracking |
|---|---|---|---|---|
| Hero Display | `font-sans font-bold` | `48px - 72px` (`text-5xl` to `text-7xl`) | 700 / 800 | `-0.03em` |
| Section Title | `font-sans font-semibold` | `28px - 36px` (`text-3xl`) | 600 | `-0.02em` |
| Card Heading | `font-sans font-semibold` | `18px - 22px` (`text-xl`) | 600 | `-0.01em` |
| Body Default | `font-sans font-normal` | `14px - 15px` (`text-sm` / `text-base`) | 400 | `0` |
| Micro Label | `font-sans uppercase` | `11px - 12px` (`text-xs`) | 600 | `0.08em` |
| Monospace Data| `font-mono` | `12px - 14px` (`text-xs` / `text-sm`) | 500 | `0` |

---

## 4. Glassmorphism Elevation System

Cards and surfaces utilize three distinct elevation levels with strict border radii between **20px and 28px**:

### Level 1: Surface Glass (`glass-surface`)
- **Usage:** Secondary panels, background containers, table wrappers.
- **CSS:**
  ```css
  background: rgba(255, 255, 255, 0.035);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 20px;
  ```

### Level 2: Interactive Glass Card (`glass-card`)
- **Usage:** Dashboard metric cards, analysis items, upload zones.
- **CSS:**
  ```css
  background: rgba(255, 255, 255, 0.055);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.11);
  border-radius: 24px;
  box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
  ```
- **Hover State:**
  ```css
  transform: translateY(-2px);
  border-color: rgba(94, 167, 255, 0.3);
  box-shadow: 0 16px 40px -10px rgba(0, 0, 0, 0.6), 0 0 20px rgba(94, 167, 255, 0.08);
  ```

### Level 3: Floating Hero Glass (`glass-floating`)
- **Usage:** Floating Navigation bar, Live Camera Viewfinder HUD, Modals.
- **CSS:**
  ```css
  background: rgba(13, 17, 28, 0.75);
  backdrop-filter: blur(28px);
  -webkit-backdrop-filter: blur(28px);
  border: 1px solid rgba(255, 255, 255, 0.16);
  border-radius: 28px;
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.65), 0 0 32px rgba(94, 167, 255, 0.1);
  ```

---

## 5. UI Component Specifications

### 5.1 `GlassNavbar`
Floating centered glass pill navigation:
- Left: Brand icon (abstract stylized Eye + Shield + AI glyph) + "PRIVACY EYE"
- Center: Route links (`Dashboard`, `Live Scan`, `Analyze`, `History`, `Reports`, `Privacy`) with active glass pill indicators
- Right: System live indicator, Notifications bell, User profile menu

### 5.2 `LiveCameraFrame`
Inspired by authentic facial scanning biometrics:
- Viewfinder container with `rounded-3xl` (24px) border and subtle dark glass perimeter.
- Face bounding box rendered with soft corners and thin electric blue/cyan lines.
- YuNet 5-point landmark indicators (eyes, nose, mouth corners) with micro-pulsing glow.
- Radial tick markers / circular aperture scanning HUD surrounding face oval.
- Floating bottom pill: `● SCANNING... 88% CONFIDENCE` with smooth gradient fill.

### 5.3 `ConfidenceRing`
SVG circular gauge with dual-tone gradient stroke (`#5EA7FF` to `#9B7CFF` or status-based `#4ADE80`). Includes central percentage value, reliability badge, and smooth counter-clockwise entry animation.

### 5.4 `SignalBar`
Horizontal telemetry bar with low-opacity track (`rgba(255, 255, 255, 0.08)`) and calibrated fill. Segments marked at 30% (Low), 70% (Suspicious), and 85% (High Risk).
