# Privacy Eye — Report Generation Architecture & Pipeline

## 1. Overview
The Privacy Eye Report Generation Engine produces two authoritative, publication-ready forensic documents for every completed scan report:
1. **Multi-Page A4 PDF Forensic Dossier**: A formal compliance and audit-ready document built with ReportLab.
2. **Single-Page Branded JPG Card**: A high-resolution (1200x1600) dark-glass summary card built with Pillow (PIL) for rapid distribution and mobile review.

Both documents are generated purely downstream from immutable inference snapshots without modifying or recalculating scores.

---

## 2. Document Generators

### 2.1 PDF Dossier Generator (`ReportPDFGenerator`)
- **Library**: `reportlab.platypus` (SimpleDocTemplate, Paragraph, Table, Spacer, Image) + `reportlab.pdfgen.canvas`.
- **Canvas Implementation**: `NumberedCanvas` runs two-pass rendering to dynamically compute total pages (e.g., "Page 1 of 2").
- **Page Header & Footer**:
  - Header: Privacy Eye Cyan/Indigo title badge, report ID, generation timestamp.
  - Footer: Multi-page numbering, confidentiality notice, and statutory disclaimer.
- **Sections**:
  1. **Executive Assessment Banner**: Assessment status badge (Likely Live Human, Presentation Attack, Suspicious, Inconclusive), confidence percentage, and reliability score.
  2. **Scan Metadata Grid**: Report ID, session ID, processing location, media type, creation timestamp, and owner reference.
  3. **Visual Evidence Frame**: Scaled representative face frame with optional aspect-ratio preservation. If Privacy Mode was engaged (`save_face_capture=False`), an explicit notice is rendered: *"Biometric capture withheld per user privacy settings."*
  4. **Why Assessment Assigned**: Bulleted forensic rationales directly mapped to evaluated signal thresholds.
  5. **Verification Test Matrix**: Detailed tabular breakdown of all performed tests (`Face Detection`, `Face Tracking`, `Eye Visibility`, `Blink Detection`, `Liveness Analysis`, `Temporal Consistency`, `Replay Detection`, `Screen Presentation`, `Input Quality`), their status (`PASS`, `FAIL`, `WARNING`, `NOT_AVAILABLE`), and diagnostic messages.
  6. **Signal Breakdown Table**: Normalized signal values, thresholds, and operational flags.
  7. **Model Lineage & Versions**: Model name, core engine version, preprocessing version, fusion version, calibration version.
  8. **Statutory Security Disclaimer**: Explanatory statement regarding probabilistic authenticity assessments.

---

### 2.2 Single-Page JPG Report Card Generator (`ReportImageGenerator`)
- **Library**: `PIL.Image`, `PIL.ImageDraw`, `PIL.ImageFont`.
- **Dimensions**: 1200 x 1600 px (3:4 portrait aspect ratio, suitable for mobile sharing, Slack, and email attachments).
- **Design Aesthetic**:
  - Dark Cyber / Frosted Glass palette: Deep slate `#0B0F19`, gradient accents `#00F0FF` (Cyan) and `#7000FF` (Electric Violet).
  - High-contrast typography: Clean, modern sans-serif fonts with fallback to default PIL fonts if OS-specific fonts are absent.
  - Card components: Frosted container with border highlights, circular assessment icon, face frame thumbnail, test status pills with green checkmarks or warning badges, and footer watermark.

---

## 3. Asynchronous & Safe Execution Pipeline

```text
               Client POST /reports
                       │
                       ▼
           Extract Authoritative Snapshot
                       │
                       ▼
             Save Secure Face JPG
                       │
         ┌─────────────┴─────────────┐
         ▼                           ▼
  Generate PDF Dossier        Generate JPG Card
         │                           │
         └─────────────┬─────────────┘
                       ▼
          Validate File Headers & Size
                       │
                       ▼
            Update Database Status:
                 'COMPLETED'
```

### 3.1 Failure Recovery & Atomicity
- If document generation fails at any stage:
  - `report_status` is updated to `'FAILED'`.
  - Temporary and orphan files are purged by `storage_service.delete_report_dir()`.
  - User receives HTTP 500 with diagnostic reference, and live scan data is preserved.
- Validated headers:
  - PDF: Magic bytes `%PDF-` and size > 1KB.
  - JPG: JPEG SOI marker `\xFF\xD8` and readable PIL image headers.
