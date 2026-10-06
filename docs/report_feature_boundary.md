# Privacy Eye — Report Feature Boundary Invariants

## Core Invariant Declaration

> **Reporting is strictly downstream of inference and must not alter the inference result.**

The Privacy Eye core inference engine is treated as **READ-ONLY**. Under no circumstances does the report service or any export mechanism:
- Modify AI/ML model architecture or weights
- Alter detection or liveness thresholds
- Recalculate confidence scores or invent auxiliary scores
- Modify face landmark detection or bounding box metrics
- Alter eye quality, blink detection state machine, or duration timers
- Alter 2D FFT Moiré screen detection or presentation attack association logic
- Change preprocessing, normalization, or postprocessing pipelines

## Architectural Boundary

```text
CURRENT CAMERA / MEDIA
          ↓
EXISTING CORE MODEL (READ ONLY)
          ↓
EXISTING INFERENCE RESULTS (SOURCE OF TRUTH)
          │
    ┌─────┴─────────────────────────────────┐
    │                                       │
    ▼                                       ▼
FRONTEND LIVE HUD                    REPORT SERVICE
                                            ↓
                           DATABASE + FACE CAPTURE + REPORTS
                                            ↓
                                       JPG / PDF
                                            ↓
                                    REPORT REVIEW UI
```

## Source of Truth Hierarchy

1. **Authoritative Core Inference Snapshot**: Emitted by `LiveAuthenticityEngine.analyze_frame()`.
2. **Scan Report Record**: Persisted in PostgreSQL (`scan_reports`) containing the exact values of assessment, confidence, reliability, signals, and test outcomes.
3. **Report Renderers**: High-definition PDF (`report_pdf_generator.py`) and JPG (`report_image_generator.py`) consuming the exact persisted values.

The reporting subsystem is purely an audit representation and forensic dossier generator.
