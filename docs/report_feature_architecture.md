# Privacy Eye — Scan Report Feature Architecture

## Overview

The Scan Report and Audit Trail system provides cryptographically verifiable, exportable forensic reports for Privacy Eye's live camera biometric authenticity engine. It enables users to securely persist scan results, inspect verification test matrices, and download high-resolution single-page JPG report cards and multi-page A4 PDF dossiers.

## Component Architecture

```text
 ┌────────────────────────────────────────────────────────┐
 │                     CLIENT BROWSER                     │
 │  Next.js 14 App Router + TailwindCSS + Framer Motion   │
 │                                                        │
 │  ┌─────────────────────────┐  ┌──────────────────────┐ │
 │  │ /dashboard/live-scan    │  │ /dashboard/reports   │ │
 │  │ Consent Modal & Capture │  │ Dossier Catalog & UI │ │
 │  └───────────┬─────────────┘  └──────────┬───────────┘ │
 └──────────────┼───────────────────────────┼─────────────┘
                │                           │
                ▼ REST API Calls (JWT / HttpOnly)
 ┌────────────────────────────────────────────────────────┐
 │                 FASTAPI BACKEND SERVICE                │
 │                                                        │
 │  ┌──────────────────────────────────────────────────┐  │
 │  │ API Routers: /api/v1/reports, /api/v1/live       │  │
 │  └─────────────────────────┬────────────────────────┘  │
 │                            │                           │
 │  ┌─────────────────────────▼────────────────────────┐  │
 │  │ ScanReportService (Downstream Orchestration)     │  │
 │  │ - Idempotency Guardian                           │  │
 │  │ - Evidence Extraction & Reason Synthesis         │  │
 │  │ - Role-based Authorization & IDOR Defense        │  │
 │  └─────────┬───────────────────┬────────────────────┘  │
 │            │                   │                       │
 │            ▼                   ▼                       │
 │  ┌───────────────────┐  ┌───────────────────────────┐  │
 │  │ PDF & JPG Engines │  │ SecureStorageService      │  │
 │  │ - ReportLab A4    │  │ - Path traversal defense  │  │
 │  │ - Pillow 1200x1600│  │ - File format validation  │  │
 │  └─────────┬─────────┘  └──────────────┬────────────┘  │
 └────────────┼───────────────────────────┼───────────────┘
              │                           │
              ▼                           ▼
 ┌──────────────────────┐   ┌─────────────────────────────┐
 │ POSTGRESQL / SQLITE  │   │   SECURE PRIVATE STORAGE    │
 │ - scan_reports       │   │   storage/secure_reports/   │
 │ - scan_report_signals│   │   users/{uid}/reports/{rid}/│
 │ - scan_report_tests  │   │   - face_evidence.jpg       │
 │ - audit_logs         │   │   - report.pdf              │
 └──────────────────────┘   │   - report.jpg              │
                            └─────────────────────────────┘
```

## Core Responsibilities

1. **`LiveAuthenticityEngine` (Read-Only)**: Executes face detection, ocular quality inspection, biological blink machine, presentation attack analysis, and score calibration. Emits authoritative dictionary snapshot.
2. **`ScanReportService`**: Receives snapshot and representative face frame. Validates image dimensions and integrity. Enforces idempotency via session ID. Extracts verification tests and forensic signals.
3. **`SecureStorageService`**: Manages isolated filesystem namespaces per user. Strictly disallows directory traversal. Purges all physical files when a report is deleted.
4. **`ReportPdfGenerator`**: Renders styled A4 evidence dossier with dark cyber aesthetics, tables, headers, footers, page numbering, and statutory disclaimers.
5. **`ReportImageGenerator`**: Renders single-page 1200x1600 JPG audit graphic optimized for presentation and sharing.
